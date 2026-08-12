import json
from pathlib import Path

from .profile import _find_data_dir


_ENCRYPTED_SUFFIXES = {
    ".rpgmvp",
    ".rpgmvo",
    ".rpgmvm",
    ".png_",
    ".ogg_",
    ".m4a_",
}


def audit_game(source: Path) -> dict[str, object]:
    source = source.resolve()
    data_dir = _find_data_dir(source)
    if (source / "js" / "rmmz_core.js").is_file() or (
        source / "www" / "js" / "rmmz_core.js"
    ).is_file():
        engine = "rpg-maker-mz"
    elif (source / "js" / "rpg_core.js").is_file() or (
        source / "www" / "js" / "rpg_core.js"
    ).is_file():
        engine = "rpg-maker-mv"
    else:
        engine = "unknown"

    issues: list[dict[str, str]] = []
    json_files = sorted(data_dir.rglob("*.json"))
    for path in json_files:
        try:
            json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            issues.append(
                {
                    "code": "invalid_json",
                    "file": path.relative_to(source).as_posix(),
                    "evidence": str(error),
                }
            )
    encrypted = sorted(
        path.relative_to(source).as_posix()
        for path in source.rglob("*")
        if path.is_file() and any(path.name.lower().endswith(s) for s in _ENCRYPTED_SUFFIXES)
    )
    return {
        "engine": engine,
        "source": str(source),
        "data_dir": str(data_dir),
        "json_files": len(json_files),
        "map_files": sum(path.name.startswith("Map") for path in json_files),
        "encrypted_assets": encrypted,
        "issues": issues,
    }
