import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def import_external_mapping(
    prepared: dict[str, Any], external: Any
) -> dict[str, str]:
    if not isinstance(external, dict) or not isinstance(external.get("entries"), list):
        raise ValueError("external mapping must contain an entries array")
    current = {task["id"]: task["source"] for task in prepared.get("tasks", [])}
    mapping: dict[str, str] = {}
    for entry in external["entries"]:
        if not isinstance(entry, dict):
            raise ValueError("external entry must be an object")
        identifier = entry.get("id")
        if identifier not in current:
            raise ValueError(f"external entry is not in current manifest: {identifier}")
        if entry.get("source") != current[identifier]:
            raise ValueError(f"source mismatch for {identifier}")
        translation = entry.get("translation")
        if not isinstance(translation, str) or not translation.strip():
            raise ValueError(f"invalid translation for {identifier}")
        if identifier in mapping:
            raise ValueError(f"duplicate external entry: {identifier}")
        mapping[identifier] = translation
    return mapping


def run_rvpacker_coverage(
    source: Path, command: list[str]
) -> dict[str, Any]:
    source = source.resolve()
    with tempfile.TemporaryDirectory(prefix="rpg-localize-rvpacker-") as temporary:
        mirror = Path(temporary) / "game-mirror"
        shutil.copytree(source, mirror)
        completed = subprocess.run(
            [*command, "read", "-i", str(mirror)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
        return {
            "available": True,
            "status": "completed" if completed.returncode == 0 else "failed",
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
