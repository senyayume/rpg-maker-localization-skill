import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from .validate import validate_mapping


def task_set_hash(prepared: dict[str, Any]) -> str:
    tasks = [
        {
            "id": task["id"],
            "source": task["source"],
            "signature": task["signature"],
        }
        for task in sorted(prepared.get("tasks", []), key=lambda item: item["id"])
    ]
    payload = json.dumps(tasks, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def create_checkpoint(
    prepared: dict[str, Any], mapping: Any, *, source_fingerprint: str
) -> dict[str, Any]:
    report = validate_mapping(prepared, mapping, require_complete=False)
    if not report["ok"]:
        codes = sorted({issue["code"] for issue in report["issues"]})
        raise ValueError(f"partial mapping failed validation: {', '.join(codes)}")
    if not mapping:
        raise ValueError("partial mapping is empty")
    tasks = {task["id"]: task for task in prepared.get("tasks", [])}
    entries = [
        {
            "id": identifier,
            "source": tasks[identifier]["source"],
            "signature": tasks[identifier]["signature"],
            "translation": mapping[identifier],
        }
        for identifier in sorted(mapping)
    ]
    return {
        "schema_version": 1,
        "quality_state": "provisional",
        "source_fingerprint": source_fingerprint,
        "task_set_hash": task_set_hash(prepared),
        "created_at": datetime.now(UTC).isoformat(),
        "completed": len(entries),
        "entries": entries,
    }


def checkpoint_name(document: dict[str, Any]) -> str:
    stable = {
        "source_fingerprint": document["source_fingerprint"],
        "task_set_hash": document["task_set_hash"],
        "entries": document["entries"],
    }
    payload = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"checkpoint-{digest}.json"


def resume_checkpoints(
    prepared: dict[str, Any], documents: list[dict[str, Any]]
) -> dict[str, Any]:
    tasks = {task["id"]: task for task in prepared.get("tasks", [])}
    mapping: dict[str, str] = {}
    invalid = 0
    conflicts: set[str] = set()
    for document in documents:
        if document.get("schema_version") != 1 or document.get("quality_state") != "provisional":
            raise ValueError("unsupported checkpoint document")
        for entry in document.get("entries", []):
            identifier = entry.get("id")
            task = tasks.get(identifier)
            if (
                task is None
                or entry.get("source") != task.get("source")
                or entry.get("signature") != task.get("signature")
            ):
                invalid += 1
                continue
            translation = entry.get("translation")
            if identifier in mapping and mapping[identifier] != translation:
                conflicts.add(identifier)
                continue
            mapping[identifier] = translation
    if conflicts:
        raise ValueError(f"checkpoint translation conflict: {', '.join(sorted(conflicts))}")
    report = validate_mapping(prepared, mapping, require_complete=False)
    if not report["ok"]:
        codes = sorted({issue["code"] for issue in report["issues"]})
        raise ValueError(f"checkpoint set failed validation: {', '.join(codes)}")

    remaining_tasks = [
        task for task in prepared.get("tasks", []) if task["id"] not in mapping
    ]
    remaining_sources = [task["source"].casefold() for task in remaining_tasks]
    glossary_subset = {
        source: target
        for source, target in prepared.get("glossary_subset", {}).items()
        if any(source.casefold() in text for text in remaining_sources)
    }
    remaining = {
        "schema_version": prepared.get("schema_version", 1),
        "tasks": remaining_tasks,
        "memory_hits": {},
        "conflicts": [
            conflict
            for conflict in prepared.get("conflicts", [])
            if conflict.get("id") not in mapping
        ],
        "glossary_subset": glossary_subset,
    }
    return {
        "completed": len(mapping),
        "remaining": len(remaining_tasks),
        "invalid": invalid,
        "mapping": mapping,
        "remaining_tasks": remaining,
    }
