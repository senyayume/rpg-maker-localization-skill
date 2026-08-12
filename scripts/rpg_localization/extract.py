import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .profile import _find_data_dir


_DATABASE_FIELDS = {
    "Actors": ("name", "nickname", "profile"),
    "Classes": ("name",),
    "Skills": ("name", "description", "message1", "message2"),
    "Items": ("name", "description"),
    "Weapons": ("name", "description"),
    "Armors": ("name", "description"),
    "Enemies": ("name",),
    "States": ("name", "message1", "message2", "message3", "message4"),
}


def extract_game(
    source: Path, *, plugin_rules: list[dict[str, str]] | None = None
) -> dict[str, list[dict[str, Any]]]:
    data_dir = _find_data_dir(source.resolve())
    rules = plugin_rules or []
    tasks: list[dict[str, Any]] = []
    discoveries: list[dict[str, Any]] = []
    for path in sorted(data_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        stem = path.stem
        if stem in _DATABASE_FIELDS and isinstance(data, list):
            _extract_database(path.name, sha, data, stem, tasks)
        elif stem == "System" and isinstance(data, dict):
            _extract_system(path.name, sha, data, tasks)
        elif stem == "CommonEvents" and isinstance(data, list):
            for index, event in enumerate(data):
                if isinstance(event, dict):
                    _append_task(tasks, path.name, sha, f"/{index}/name", event.get("name"), "common_event_name")
                    _extract_event_list(
                        path.name,
                        sha,
                        event.get("list", []),
                        f"/{index}/list",
                        tasks,
                        discoveries,
                        rules,
                    )
        elif stem == "Troops" and isinstance(data, list):
            for troop_index, troop in enumerate(data):
                if not isinstance(troop, dict):
                    continue
                _append_task(tasks, path.name, sha, f"/{troop_index}/name", troop.get("name"), "troop_name")
                for page_index, page in enumerate(troop.get("pages", [])):
                    if isinstance(page, dict):
                        _extract_event_list(
                            path.name,
                            sha,
                            page.get("list", []),
                            f"/{troop_index}/pages/{page_index}/list",
                            tasks,
                            discoveries,
                            rules,
                        )
        elif stem.startswith("Map") and isinstance(data, dict):
            _append_task(tasks, path.name, sha, "/displayName", data.get("displayName"), "map_name")
            for event_index, event in enumerate(data.get("events", [])):
                if not isinstance(event, dict):
                    continue
                for page_index, page in enumerate(event.get("pages", [])):
                    if isinstance(page, dict):
                        _extract_event_list(
                            path.name,
                            sha,
                            page.get("list", []),
                            f"/events/{event_index}/pages/{page_index}/list",
                            tasks,
                            discoveries,
                            rules,
                        )
        elif stem == "MapInfos" and isinstance(data, list):
            for index, item in enumerate(data):
                if isinstance(item, dict):
                    _append_task(tasks, path.name, sha, f"/{index}/name", item.get("name"), "map_info")
    tasks.sort(key=lambda item: item["occurrence_id"])
    discoveries.sort(key=lambda item: (item["file"], item["path"]))
    return {"tasks": tasks, "discoveries": discoveries}


def _extract_database(
    file_name: str,
    sha: str,
    data: list[Any],
    stem: str,
    tasks: list[dict[str, Any]],
) -> None:
    for index, entry in enumerate(data):
        if not isinstance(entry, dict):
            continue
        for field in _DATABASE_FIELDS[stem]:
            _append_task(
                tasks,
                file_name,
                sha,
                f"/{index}/{field}",
                entry.get(field),
                f"{stem.lower()}_{field}",
            )
        if stem == "Items":
            note = entry.get("note")
            if isinstance(note, str) and re.search(r"<SG(?:説明|说明)\s*[:：]", note):
                _append_task(tasks, file_name, sha, f"/{index}/note", note, "scene_glossary_note")


def _extract_system(
    file_name: str, sha: str, data: dict[str, Any], tasks: list[dict[str, Any]]
) -> None:
    for key in ("gameTitle", "currencyUnit"):
        _append_task(tasks, file_name, sha, f"/{key}", data.get(key), "system")
    for key in ("elements", "skillTypes", "weaponTypes", "armorTypes", "equipTypes"):
        for index, value in enumerate(data.get(key, [])):
            _append_task(tasks, file_name, sha, f"/{key}/{index}", value, "system_type")
    for index, value in enumerate(data.get("variables", [])):
        _append_task(tasks, file_name, sha, f"/variables/{index}", value, "system_variable_name")
    terms = data.get("terms", {})
    if isinstance(terms, dict):
        _walk_system_terms(file_name, sha, terms, "/terms", tasks)


def _walk_system_terms(
    file_name: str,
    sha: str,
    value: Any,
    pointer: str,
    tasks: list[dict[str, Any]],
) -> None:
    if isinstance(value, str):
        _append_task(tasks, file_name, sha, pointer, value, "system_term")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_system_terms(file_name, sha, child, f"{pointer}/{index}", tasks)
    elif isinstance(value, dict):
        for key, child in value.items():
            _walk_system_terms(file_name, sha, child, f"{pointer}/{_escape(key)}", tasks)


def _extract_event_list(
    file_name: str,
    sha: str,
    commands: Any,
    base: str,
    tasks: list[dict[str, Any]],
    discoveries: list[dict[str, Any]],
    rules: list[dict[str, str]],
) -> None:
    if not isinstance(commands, list):
        return
    choice_help_active = False
    for index, command in enumerate(commands):
        if not isinstance(command, dict):
            continue
        code = command.get("code")
        parameters = command.get("parameters", [])
        pointer = f"{base}/{index}/parameters"
        if not isinstance(parameters, list):
            continue
        if code == 108:
            choice_help_active = bool(parameters and parameters[0] == "選択肢ヘルプ")
        elif code == 408 and choice_help_active and parameters:
            if isinstance(parameters[0], str) and _has_visible_text(parameters[0]):
                _append_task(tasks, file_name, sha, f"{pointer}/0", parameters[0], "choice_help")
        elif code == 122 and len(parameters) > 4 and isinstance(parameters[4], str):
            if parameters[4].lstrip().startswith(('"', "'", "`")):
                _append_task(tasks, file_name, sha, f"{pointer}/4", parameters[4], "variable_text")
        elif code == 101 and len(parameters) > 4:
            _append_task(tasks, file_name, sha, f"{pointer}/4", parameters[4], "speaker")
        elif code == 401 and parameters:
            _append_task(tasks, file_name, sha, f"{pointer}/0", parameters[0], "dialogue")
        elif code == 405 and parameters:
            _append_task(tasks, file_name, sha, f"{pointer}/0", parameters[0], "scrolling_text")
        elif code == 102 and parameters and isinstance(parameters[0], list):
            for choice_index, choice in enumerate(parameters[0]):
                _append_task(
                    tasks,
                    file_name,
                    sha,
                    f"{pointer}/0/{choice_index}",
                    choice,
                    "choice",
                )
        elif code == 402 and len(parameters) > 1:
            _append_task(tasks, file_name, sha, f"{pointer}/1", parameters[1], "choice_branch")
        elif code in {320, 324, 325} and len(parameters) > 1:
            context = {320: "change_name", 324: "change_nickname", 325: "change_profile"}[code]
            _append_task(tasks, file_name, sha, f"{pointer}/1", parameters[1], context)
        elif code == 357 and len(parameters) > 3 and isinstance(parameters[3], dict):
            plugin = str(parameters[0])
            plugin_command = str(parameters[1])
            arguments = parameters[3]
            matched_arguments = {
                rule["argument"]: rule
                for rule in rules
                if rule.get("plugin") == plugin and rule.get("command") == plugin_command
            }
            for argument, value in arguments.items():
                argument_pointer = f"{pointer}/3/{_escape(argument)}"
                if argument in matched_arguments:
                    _append_task(
                        tasks,
                        file_name,
                        sha,
                        argument_pointer,
                        value,
                        matched_arguments[argument].get("context", "plugin_text"),
                    )
                elif _visible(value):
                    discoveries.append(
                        {
                            "file": file_name,
                            "path": argument_pointer,
                            "plugin": plugin,
                            "command": plugin_command,
                            "argument": argument,
                            "value": value,
                            "reason": "unconfirmed_plugin_text",
                        }
                    )


def _append_task(
    tasks: list[dict[str, Any]],
    file_name: str,
    sha: str,
    pointer: str,
    value: Any,
    context: str,
) -> None:
    if not _visible(value):
        return
    tasks.append(
        {
            "occurrence_id": f"{file_name}#{pointer}",
            "file": file_name,
            "path": pointer,
            "source": value,
            "context": context,
            "source_file_sha256": sha,
        }
    )


def _visible(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_visible_text(value: str) -> bool:
    visible = re.sub(r"\\(?:[<>]|[A-Za-z]+(?:\[[^\]]*\])?|[{}])", "", value)
    return bool(visible.strip())


def _escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")
