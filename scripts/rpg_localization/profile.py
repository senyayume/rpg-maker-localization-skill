import json
import hashlib
from pathlib import Path

import yaml


def init_workspace(workspace: Path, *, engine: str) -> dict[str, str]:
    if engine not in {"rpg-maker-mv", "rpg-maker-mz"}:
        raise ValueError(f"unsupported engine: {engine}")

    directories = (
        "translations/memory",
        "translations/batches",
        "translations/staging",
        "translations/staging/checkpoints",
        "translations/accepted",
        "reports",
        ".local",
        "dist",
        "rules",
    )
    for directory in directories:
        (workspace / directory).mkdir(parents=True, exist_ok=True)

    profile = {
        "schema_version": 1,
        "engine": engine,
        "source_language": "auto",
        "target_language": "zh-CN",
        "references": {
            "glossary": "glossary.json",
            "style_guide": "style-guide.md",
            "plugin_rules": "rules/plugin-text.json",
        },
        "output": {"directory": "dist", "mode": "patch"},
    }
    (workspace / "localization.yaml").write_text(
        yaml.safe_dump(profile, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    (workspace / "glossary.json").write_text("{}\n", encoding="utf-8")
    (workspace / "style-guide.md").write_text(
        "# 简体中文译风\n\n记录人物口吻、术语与断句要求。\n",
        encoding="utf-8",
    )
    (workspace / "rules" / "plugin-text.json").write_text(
        json.dumps({"rules": []}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return profile


def bind_workspace(workspace: Path, source: Path) -> dict[str, object]:
    workspace = workspace.resolve()
    source = source.resolve()
    if not (workspace / "localization.yaml").is_file():
        raise ValueError(f"not a localization workspace: {workspace}")
    if workspace == source or source in workspace.parents or workspace in source.parents:
        raise ValueError("workspace and source game must be separate directories")

    data_dir = _find_data_dir(source)
    digest = hashlib.sha256()
    files = sorted(path for path in data_dir.rglob("*.json") if path.is_file())
    if not files:
        raise ValueError(f"no RPG Maker JSON files found in {data_dir}")
    for path in files:
        relative = path.relative_to(data_dir).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")

    machine_path = workspace / ".local" / "machine.json"
    previous = {}
    if machine_path.is_file():
        previous = json.loads(machine_path.read_text(encoding="utf-8"))
    fingerprint = digest.hexdigest()
    result: dict[str, object] = {
        "source": str(source),
        "data_dir": str(data_dir),
        "source_fingerprint": fingerprint,
        "reused": previous.get("source_fingerprint") == fingerprint,
    }
    machine_path.parent.mkdir(parents=True, exist_ok=True)
    machine_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result


def _find_data_dir(source: Path) -> Path:
    candidates = [source / "data", source / "www" / "data"]
    matches = [candidate for candidate in candidates if candidate.is_dir()]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one RPG Maker data directory under {source}")
    return matches[0]
