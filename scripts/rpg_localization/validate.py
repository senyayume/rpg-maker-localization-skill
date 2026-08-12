import re
from typing import Any

from .tasks import text_signature


_CJK = re.compile(r"[\u3400-\u9fff]")
_LATIN_WORD = re.compile(r"[A-Za-z]{2,}")
_CONTROL = re.compile(r"\\[A-Za-z]+(?:\[[^\]]*\])?|\\[.$|!><^{}\\]")


def validate_mapping(
    prepared: dict[str, Any], mapping: Any, *, require_complete: bool = True
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    tasks = {task["id"]: task for task in prepared.get("tasks", [])}
    if not isinstance(mapping, dict):
        return {
            "ok": False,
            "issues": [{"code": "mapping_not_object", "evidence": type(mapping).__name__}],
            "review_tasks": [],
        }

    for identifier in sorted(set(mapping) - set(tasks)):
        issues.append({"code": "unknown_mapping_id", "id": identifier})
    if require_complete:
        for identifier in sorted(set(tasks) - set(mapping)):
            issues.append({"code": "missing_mapping_id", "id": identifier})

    glossary = prepared.get("glossary_subset", {})
    for identifier in sorted(set(tasks) & set(mapping)):
        task = tasks[identifier]
        translation = mapping[identifier]
        if not isinstance(translation, str):
            issues.append(
                {"code": "translation_not_string", "id": identifier, "evidence": type(translation).__name__}
            )
            continue
        if not translation.strip():
            issues.append({"code": "empty_translation", "id": identifier})
            continue
        source_signature = task["signature"]
        translated_signature = text_signature(translation)
        if source_signature["control_codes"] != translated_signature["control_codes"]:
            issues.append(
                {
                    "code": "control_code_mismatch",
                    "id": identifier,
                    "expected": source_signature["control_codes"],
                    "actual": translated_signature["control_codes"],
                }
            )
        if source_signature["placeholders"] != translated_signature["placeholders"]:
            issues.append(
                {
                    "code": "placeholder_mismatch",
                    "id": identifier,
                    "expected": source_signature["placeholders"],
                    "actual": translated_signature["placeholders"],
                }
            )
        if source_signature["linebreak_count"] != translated_signature["linebreak_count"]:
            issues.append(
                {
                    "code": "linebreak_mismatch",
                    "id": identifier,
                    "expected": source_signature["linebreak_count"],
                    "actual": translated_signature["linebreak_count"],
                }
            )
        for source_term, target_term in glossary.items():
            if source_term.casefold() in task["source"].casefold() and target_term not in translation:
                issues.append(
                    {
                        "code": "glossary_mismatch",
                        "id": identifier,
                        "source_term": source_term,
                        "expected": target_term,
                    }
                )
        visible = _CONTROL.sub("", translation)
        if _LATIN_WORD.search(visible) and not _CJK.search(visible):
            issues.append(
                {
                    "code": "source_language_residual",
                    "id": identifier,
                    "evidence": translation,
                }
            )

    review_tasks = []
    high_risk_contexts = {"choice", "choice_branch", "plugin_text"}
    for task in tasks.values():
        if any(
            occurrence.get("context") in high_risk_contexts
            for occurrence in task.get("occurrences", [])
        ):
            review_tasks.append(task)
    review_tasks.sort(key=lambda item: item["id"])
    return {"ok": not issues, "issues": issues, "review_tasks": review_tasks}
