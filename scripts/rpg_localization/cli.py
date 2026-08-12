import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .adapters import import_external_mapping
from .audit import audit_game
from .checkpoints import checkpoint_name, create_checkpoint, resume_checkpoints, task_set_hash
from .extract import extract_game
from .generate import generate_patch, verify_patch
from .profile import bind_workspace, init_workspace
from .tasks import prepare_tasks
from .validate import validate_mapping


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="RPG Maker MV/MZ localization workflow")
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--game", type=Path, required=True)
    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--workspace", type=Path, required=True)
    init_parser.add_argument("--engine", choices=("rpg-maker-mv", "rpg-maker-mz"), required=True)
    bind_parser = subparsers.add_parser("bind")
    bind_parser.add_argument("--workspace", type=Path, required=True)
    bind_parser.add_argument("--game", type=Path, required=True)
    for name in ("extract", "prepare"):
        child = subparsers.add_parser(name)
        child.add_argument("--workspace", type=Path, required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--workspace", type=Path, required=True)
    validate_parser.add_argument("--mapping", type=Path, required=True)
    checkpoint_parser = subparsers.add_parser("checkpoint")
    checkpoint_parser.add_argument("--workspace", type=Path, required=True)
    checkpoint_parser.add_argument("--mapping", type=Path, required=True)
    resume_parser = subparsers.add_parser("resume")
    resume_parser.add_argument("--workspace", type=Path, required=True)
    accept_parser = subparsers.add_parser("accept")
    accept_parser.add_argument("--workspace", type=Path, required=True)
    accept_parser.add_argument("--mapping", type=Path, required=True)
    for name in ("generate", "verify"):
        child = subparsers.add_parser(name)
        child.add_argument("--workspace", type=Path, required=True)
    export_parser = subparsers.add_parser("export-external")
    export_parser.add_argument("--workspace", type=Path, required=True)
    export_parser.add_argument("--output", type=Path, required=True)
    import_parser = subparsers.add_parser("import-external")
    import_parser.add_argument("--workspace", type=Path, required=True)
    import_parser.add_argument("--input", type=Path, required=True)
    arguments = parser.parse_args(argv)
    try:
        result = _dispatch(arguments)
    except Exception as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


def _dispatch(arguments: argparse.Namespace) -> dict[str, Any]:
    if arguments.command == "audit":
        return audit_game(arguments.game)
    if arguments.command == "init":
        return init_workspace(arguments.workspace, engine=arguments.engine)
    if arguments.command == "bind":
        return bind_workspace(arguments.workspace, arguments.game)
    machine = _read_json(arguments.workspace / ".local" / "machine.json")
    game = Path(machine["source"])
    if arguments.command == "extract":
        rules_document = _read_json(arguments.workspace / "rules" / "plugin-text.json")
        extracted = extract_game(game, plugin_rules=rules_document.get("rules", []))
        output = arguments.workspace / "translations" / "batches" / "occurrences.json"
        _write_json(output, extracted)
        return {"tasks": len(extracted["tasks"]), "discoveries": len(extracted["discoveries"]), "output": str(output)}
    if arguments.command == "prepare":
        extracted = _read_json(arguments.workspace / "translations" / "batches" / "occurrences.json")
        glossary = _read_json(arguments.workspace / "glossary.json")
        prepared = prepare_tasks(extracted["tasks"], glossary=glossary)
        prepared["source_fingerprint"] = machine["source_fingerprint"]
        prepared["task_set_hash"] = task_set_hash(prepared)
        output = arguments.workspace / "translations" / "batches" / "tasks.json"
        _write_json(output, prepared)
        return {"tasks": len(prepared["tasks"]), "memory_hits": len(prepared["memory_hits"]), "output": str(output)}
    prepared_path = arguments.workspace / "translations" / "batches" / "tasks.json"
    prepared = _read_json(prepared_path)
    if arguments.command == "checkpoint":
        document = create_checkpoint(
            prepared,
            _read_json(arguments.mapping),
            source_fingerprint=machine["source_fingerprint"],
        )
        output = (
            arguments.workspace
            / "translations"
            / "staging"
            / "checkpoints"
            / checkpoint_name(document)
        )
        _write_json(output, document)
        return {"completed": document["completed"], "output": str(output.resolve())}
    if arguments.command == "resume":
        checkpoint_dir = (
            arguments.workspace / "translations" / "staging" / "checkpoints"
        )
        checkpoint_paths = sorted(checkpoint_dir.glob("checkpoint-*.json"))
        if not checkpoint_paths:
            raise ValueError(f"no checkpoints found in {checkpoint_dir}")
        resumed = resume_checkpoints(
            prepared, [_read_json(path) for path in checkpoint_paths]
        )
        tasks_output = arguments.workspace / "translations" / "batches" / "resume-tasks.json"
        candidate_output = (
            arguments.workspace / "translations" / "staging" / "resume-candidate.json"
        )
        report_output = arguments.workspace / "reports" / "resume.json"
        remaining_document = resumed.pop("remaining_tasks")
        current_task_set_hash = task_set_hash(prepared)
        remaining_document["source_fingerprint"] = machine["source_fingerprint"]
        remaining_document["task_set_hash"] = current_task_set_hash
        _write_json(tasks_output, remaining_document)
        _write_json(candidate_output, resumed.pop("mapping"))
        result = {
            **resumed,
            "checkpoints": len(checkpoint_paths),
            "source_fingerprint": machine["source_fingerprint"],
            "task_set_hash": current_task_set_hash,
            "tasks_output": str(tasks_output.resolve()),
            "candidate_output": str(candidate_output.resolve()),
        }
        _write_json(report_output, result)
        return result
    if arguments.command == "export-external":
        document = {
            "schema_version": 1,
            "source_fingerprint": machine["source_fingerprint"],
            "entries": [
                {"id": task["id"], "source": task["source"], "translation": ""}
                for task in prepared.get("tasks", [])
            ],
        }
        _write_json(arguments.output, document)
        return {"exported": len(document["entries"]), "output": str(arguments.output.resolve())}
    if arguments.command == "import-external":
        external = _read_json(arguments.input)
        if external.get("source_fingerprint") != machine.get("source_fingerprint"):
            raise ValueError("external candidate source fingerprint mismatch")
        mapping = import_external_mapping(prepared, external)
        output = arguments.workspace / "translations" / "staging" / "external-candidate.json"
        _write_json(output, mapping)
        return {"imported": len(mapping), "output": str(output.resolve())}
    if arguments.command in {"validate", "accept"}:
        mapping = _read_json(arguments.mapping)
        report = validate_mapping(prepared, mapping)
        report_path = arguments.workspace / "reports" / "candidate-validation.json"
        _write_json(report_path, report)
        if arguments.command == "validate":
            if not report["ok"]:
                raise ValueError(f"candidate failed validation; see {report_path}")
            return report
        if not report["ok"]:
            raise ValueError(f"cannot accept invalid candidate; see {report_path}")
        accepted_path = arguments.workspace / "translations" / "accepted" / "mapping.json"
        _write_json(accepted_path, mapping)
        record = {
            "accepted": len(mapping),
            "quality_state": "technical-pass",
            "source_fingerprint": machine["source_fingerprint"],
            "tasks_file": str(prepared_path),
        }
        _write_json(arguments.workspace / "translations" / "accepted" / "record.json", record)
        return record
    accepted_path = arguments.workspace / "translations" / "accepted" / "mapping.json"
    if arguments.command == "generate":
        record = _read_json(arguments.workspace / "translations" / "accepted" / "record.json")
        if record.get("source_fingerprint") != machine.get("source_fingerprint"):
            raise ValueError("accepted mapping does not match the bound source fingerprint")
        return generate_patch(game, prepared, _read_json(accepted_path), arguments.workspace / "dist")
    if arguments.command == "verify":
        report = verify_patch(game, arguments.workspace / "dist", prepared)
        if not report["ok"]:
            report_path = arguments.workspace / "reports" / "dist-verification.json"
            _write_json(report_path, report)
            raise ValueError(f"dist failed verification; see {report_path}")
        return report
    raise ValueError(f"unsupported command: {arguments.command}")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
