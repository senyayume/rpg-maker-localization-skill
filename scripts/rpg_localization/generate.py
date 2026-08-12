import copy
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .profile import _find_data_dir


def generate_patch(
    source: Path,
    prepared: dict[str, Any],
    mapping: dict[str, str],
    output: Path,
) -> dict[str, int]:
    source = source.resolve()
    data_dir = _find_data_dir(source)
    per_file: dict[str, list[tuple[str, str]]] = {}
    for task in prepared.get("tasks", []):
        if task["id"] not in mapping:
            raise ValueError(f"missing mapping: {task['id']}")
        for occurrence in task.get("occurrences", []):
            per_file.setdefault(occurrence["file"], []).append(
                (occurrence["path"], mapping[task["id"]])
            )

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=output.name + "-", dir=output.parent))
    try:
        for file_name, entries in sorted(per_file.items()):
            source_file = data_dir / file_name
            data = json.loads(source_file.read_text(encoding="utf-8-sig"))
            translated = copy.deepcopy(data)
            for pointer, value in entries:
                _set_pointer(translated, pointer, value)
            target = temporary / "data" / file_name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps(translated, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
        verification = verify_patch(source, temporary, prepared)
        if not verification["ok"]:
            raise ValueError(f"generated patch failed verification: {verification['issues']}")
        if output.exists():
            shutil.rmtree(output)
        temporary.replace(output)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {"files": len(per_file), "paths": sum(len(entries) for entries in per_file.values())}


def verify_patch(
    source: Path, output: Path, prepared: dict[str, Any]
) -> dict[str, Any]:
    data_dir = _find_data_dir(source.resolve())
    allowed: dict[str, set[str]] = {}
    for task in prepared.get("tasks", []):
        for occurrence in task.get("occurrences", []):
            allowed.setdefault(occurrence["file"], set()).add(occurrence["path"])
    issues: list[dict[str, str]] = []
    for file_name, pointers in sorted(allowed.items()):
        source_data = json.loads((data_dir / file_name).read_text(encoding="utf-8-sig"))
        translated_path = output / "data" / file_name
        if not translated_path.is_file():
            issues.append({"code": "missing_output_file", "file": file_name})
            continue
        translated_data = json.loads(translated_path.read_text(encoding="utf-8-sig"))
        _compare(source_data, translated_data, "", pointers, file_name, issues)
    return {"ok": not issues, "issues": issues}


def _compare(
    source: Any,
    translated: Any,
    pointer: str,
    allowed: set[str],
    file_name: str,
    issues: list[dict[str, str]],
) -> None:
    if type(source) is not type(translated):
        issues.append({"code": "type_changed", "file": file_name, "path": pointer})
        return
    if isinstance(source, dict):
        if source.keys() != translated.keys():
            issues.append({"code": "keys_changed", "file": file_name, "path": pointer})
            return
        for key in source:
            _compare(
                source[key],
                translated[key],
                f"{pointer}/{_escape(str(key))}",
                allowed,
                file_name,
                issues,
            )
    elif isinstance(source, list):
        if len(source) != len(translated):
            issues.append({"code": "array_length_changed", "file": file_name, "path": pointer})
            return
        for index, (left, right) in enumerate(zip(source, translated)):
            _compare(left, right, f"{pointer}/{index}", allowed, file_name, issues)
    elif source != translated and pointer not in allowed:
        issues.append({"code": "non_text_value_changed", "file": file_name, "path": pointer})


def _set_pointer(data: Any, pointer: str, value: str) -> None:
    tokens = [_unescape(token) for token in pointer.split("/")[1:]]
    current = data
    for token in tokens[:-1]:
        current = current[int(token)] if isinstance(current, list) else current[token]
    final = tokens[-1]
    if isinstance(current, list):
        current[int(final)] = value
    else:
        current[final] = value


def _escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _unescape(value: str) -> str:
    return value.replace("~1", "/").replace("~0", "~")
