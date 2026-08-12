import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "rpg_localize.py"


class CliTests(unittest.TestCase):
    def test_cli_resume_emits_only_unfinished_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            game = root / "Game"
            (game / "data").mkdir(parents=True)
            (game / "js").mkdir()
            (game / "js" / "rmmz_core.js").write_text("// MZ", encoding="utf-8")
            (game / "data" / "Items.json").write_text(
                '[null,{"name":"Potion","description":"Restore HP"}]', encoding="utf-8"
            )
            workspace = root / "workspace"
            self._run("init", "--workspace", str(workspace), "--engine", "rpg-maker-mz")
            self._run("bind", "--workspace", str(workspace), "--game", str(game))
            self._run("extract", "--workspace", str(workspace))
            self._run("prepare", "--workspace", str(workspace))
            prepared = json.loads(
                (workspace / "translations" / "batches" / "tasks.json").read_text(encoding="utf-8")
            )
            potion = next(task for task in prepared["tasks"] if task["source"] == "Potion")
            partial = workspace / "translations" / "staging" / "partial.json"
            partial.write_text(
                json.dumps({potion["id"]: "药水"}, ensure_ascii=False), encoding="utf-8"
            )
            self._run("checkpoint", "--workspace", str(workspace), "--mapping", str(partial))

            result = subprocess.run(
                ["python", str(SCRIPT), "resume", "--workspace", str(workspace)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            remaining = json.loads(Path(summary["tasks_output"]).read_text(encoding="utf-8"))
            candidate = json.loads(Path(summary["candidate_output"]).read_text(encoding="utf-8"))
            self.assertEqual(summary["completed"], 1)
            self.assertEqual(summary["remaining"], 1)
            self.assertEqual(summary["invalid"], 0)
            self.assertIn("source_fingerprint", remaining)
            self.assertIn("task_set_hash", remaining)
            self.assertEqual(len(remaining["source_fingerprint"]), 64)
            self.assertEqual(remaining["source_fingerprint"], summary["source_fingerprint"])
            self.assertEqual(len(remaining["task_set_hash"]), 64)
            self.assertEqual(remaining["task_set_hash"], summary["task_set_hash"])
            self.assertEqual([task["source"] for task in remaining["tasks"]], ["Restore HP"])
            self.assertEqual(candidate, {potion["id"]: "药水"})

    def test_cli_saves_partial_mapping_as_provisional_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            game = root / "Game"
            (game / "data").mkdir(parents=True)
            (game / "js").mkdir()
            (game / "js" / "rmmz_core.js").write_text("// MZ", encoding="utf-8")
            (game / "data" / "Items.json").write_text(
                '[null,{"name":"Potion","description":"Restore HP"}]', encoding="utf-8"
            )
            workspace = root / "workspace"
            self._run("init", "--workspace", str(workspace), "--engine", "rpg-maker-mz")
            self._run("bind", "--workspace", str(workspace), "--game", str(game))
            self._run("extract", "--workspace", str(workspace))
            self._run("prepare", "--workspace", str(workspace))
            prepared = json.loads(
                (workspace / "translations" / "batches" / "tasks.json").read_text(encoding="utf-8")
            )
            potion = next(task for task in prepared["tasks"] if task["source"] == "Potion")
            partial = workspace / "translations" / "staging" / "partial.json"
            partial.write_text(
                json.dumps({potion["id"]: "药水"}, ensure_ascii=False), encoding="utf-8"
            )

            result = subprocess.run(
                [
                    "python",
                    str(SCRIPT),
                    "checkpoint",
                    "--workspace",
                    str(workspace),
                    "--mapping",
                    str(partial),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            document = json.loads(Path(json.loads(result.stdout)["output"]).read_text(encoding="utf-8"))
            self.assertEqual(document["quality_state"], "provisional")
            self.assertEqual(document["completed"], 1)
            self.assertEqual(document["entries"][0]["source"], "Potion")

    def test_cli_audit_init_bind_extract_and_prepare(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            game = root / "中文 Game"
            (game / "data").mkdir(parents=True)
            (game / "js").mkdir()
            (game / "js" / "rmmz_core.js").write_text("// MZ", encoding="utf-8")
            (game / "data" / "Items.json").write_text(
                '[null,{"name":"Potion","description":"Restore HP"}]', encoding="utf-8"
            )
            workspace = root / "汉化 workspace"

            audit = self._run("audit", "--game", str(game))
            init = self._run("init", "--workspace", str(workspace), "--engine", "rpg-maker-mz")
            bind = self._run("bind", "--workspace", str(workspace), "--game", str(game))
            extract = self._run("extract", "--workspace", str(workspace))
            prepare = self._run("prepare", "--workspace", str(workspace))

            self.assertEqual(json.loads(audit.stdout)["engine"], "rpg-maker-mz")
            self.assertEqual(json.loads(init.stdout)["engine"], "rpg-maker-mz")
            self.assertFalse(json.loads(bind.stdout)["reused"])
            self.assertEqual(json.loads(extract.stdout)["tasks"], 2)
            self.assertEqual(json.loads(prepare.stdout)["tasks"], 2)
            self.assertTrue((workspace / "translations" / "batches" / "tasks.json").is_file())
            task_document = json.loads(
                (workspace / "translations" / "batches" / "tasks.json").read_text(encoding="utf-8")
            )
            self.assertIn("source_fingerprint", task_document)
            self.assertIn("task_set_hash", task_document)

    def test_cli_validates_accepts_generates_and_verifies_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            game = root / "Game"
            (game / "data").mkdir(parents=True)
            (game / "js").mkdir()
            (game / "js" / "rmmz_core.js").write_text("// MZ", encoding="utf-8")
            (game / "data" / "Items.json").write_text(
                '[null,{"name":"Potion","description":"Restore HP","price":50}]', encoding="utf-8"
            )
            workspace = root / "workspace"
            self._run("init", "--workspace", str(workspace), "--engine", "rpg-maker-mz")
            self._run("bind", "--workspace", str(workspace), "--game", str(game))
            self._run("extract", "--workspace", str(workspace))
            self._run("prepare", "--workspace", str(workspace))
            prepared = json.loads(
                (workspace / "translations" / "batches" / "tasks.json").read_text(encoding="utf-8")
            )
            mapping = {
                task["id"]: {"Potion": "药水", "Restore HP": "恢复生命值"}[task["source"]]
                for task in prepared["tasks"]
            }
            candidate = workspace / "translations" / "staging" / "candidate.json"
            candidate.write_text(json.dumps(mapping, ensure_ascii=False), encoding="utf-8")

            validation = self._run(
                "validate", "--workspace", str(workspace), "--mapping", str(candidate)
            )
            acceptance = self._run(
                "accept", "--workspace", str(workspace), "--mapping", str(candidate)
            )
            generation = self._run("generate", "--workspace", str(workspace))
            verification = self._run("verify", "--workspace", str(workspace))

            self.assertTrue(json.loads(validation.stdout)["ok"])
            self.assertEqual(json.loads(acceptance.stdout)["accepted"], 2)
            self.assertEqual(json.loads(acceptance.stdout).get("quality_state"), "technical-pass")
            self.assertEqual(json.loads(generation.stdout)["files"], 1)
            self.assertTrue(json.loads(verification.stdout)["ok"])
            self.assertTrue((workspace / "translations" / "accepted" / "mapping.json").is_file())
            self.assertTrue((workspace / "dist" / "data" / "Items.json").is_file())

            translated_path = workspace / "dist" / "data" / "Items.json"
            translated = json.loads(translated_path.read_text(encoding="utf-8"))
            translated[1]["price"] = 999
            translated_path.write_text(json.dumps(translated), encoding="utf-8")
            failed = subprocess.run(
                ["python", str(SCRIPT), "verify", "--workspace", str(workspace)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertNotEqual(failed.returncode, 0)

    def test_cli_exports_and_imports_external_candidate_through_staging(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            game = root / "Game"
            (game / "data").mkdir(parents=True)
            (game / "js").mkdir()
            (game / "js" / "rmmz_core.js").write_text("// MZ", encoding="utf-8")
            (game / "data" / "Items.json").write_text(
                '[null,{"name":"Potion","description":""}]', encoding="utf-8"
            )
            workspace = root / "workspace"
            self._run("init", "--workspace", str(workspace), "--engine", "rpg-maker-mz")
            self._run("bind", "--workspace", str(workspace), "--game", str(game))
            self._run("extract", "--workspace", str(workspace))
            self._run("prepare", "--workspace", str(workspace))
            exchange = root / "external.json"

            self._run("export-external", "--workspace", str(workspace), "--output", str(exchange))
            document = json.loads(exchange.read_text(encoding="utf-8"))
            document["entries"][0]["translation"] = "药水"
            exchange.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
            imported = self._run(
                "import-external", "--workspace", str(workspace), "--input", str(exchange)
            )

            result = json.loads(imported.stdout)
            self.assertEqual(result["imported"], 1)
            candidate = Path(result["output"])
            self.assertTrue(candidate.is_file())
            self.assertIn(candidate, (workspace / "translations" / "staging").iterdir())

    def _run(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python", str(SCRIPT), *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )


if __name__ == "__main__":
    unittest.main()
