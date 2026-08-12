import hashlib
import re
from collections import defaultdict
from typing import Any


_CONTROL_CODE = re.compile(r"\\[A-Za-z]+(?:\[[^\]]*\])?|\\[.$|!><^{}\\]")
_PLACEHOLDER = re.compile(r"%\d+|\{[A-Za-z_][A-Za-z0-9_]*\}")


def text_signature(value: str) -> dict[str, Any]:
    return {
        "control_codes": _CONTROL_CODE.findall(value),
        "placeholders": _PLACEHOLDER.findall(value),
        "linebreak_count": value.count("\n"),
    }


def prepare_tasks(
    occurrences: list[dict[str, Any]],
    *,
    glossary: dict[str, str] | None = None,
    accepted: dict[str, str] | None = None,
    contextual_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    glossary = glossary or {}
    accepted = accepted or {}
    contextual_overrides = contextual_overrides or {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for occurrence in occurrences:
        grouped[str(occurrence["source"])].append(dict(occurrence))

    tasks: list[dict[str, Any]] = []
    memory_hits: dict[str, str] = {}
    conflicts: list[dict[str, Any]] = []
    for source in sorted(grouped):
        item_occurrences = sorted(grouped[source], key=lambda item: item["occurrence_id"])
        identifier = "text-" + hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
        override_values = {
            contextual_overrides[item["occurrence_id"]]
            for item in item_occurrences
            if item["occurrence_id"] in contextual_overrides
        }
        if len(override_values) > 1:
            conflicts.append(
                {
                    "code": "contextual_translation_required",
                    "id": identifier,
                    "source": source,
                    "occurrences": item_occurrences,
                }
            )
        if source in accepted and text_signature(source) == text_signature(accepted[source]):
            memory_hits[identifier] = accepted[source]
            continue
        tasks.append(
            {
                "id": identifier,
                "source": source,
                "signature": text_signature(source),
                "occurrences": item_occurrences,
            }
        )
    glossary_subset = {
        source: target
        for source, target in sorted(glossary.items())
        if any(source.casefold() in task["source"].casefold() for task in tasks)
    }
    tasks.sort(key=lambda item: item["id"])
    return {
        "schema_version": 1,
        "tasks": tasks,
        "memory_hits": memory_hits,
        "conflicts": conflicts,
        "glossary_subset": glossary_subset,
    }
