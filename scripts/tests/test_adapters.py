import json
import tempfile
import unittest
from pathlib import Path

from rpg_localization.adapters import import_external_mapping, run_rvpacker_coverage


class AdapterTests(unittest.TestCase):
    def test_external_mapping_is_rebound_to_current_sources(self) -> None:
        prepared = {
            "tasks": [{"id": "text-a", "source": "Hello", "occurrences": []}]
        }
        external = {"entries": [{"id": "text-a", "source": "Hello", "translation": "你好"}]}

        result = import_external_mapping(prepared, external)

        self.assertEqual(result, {"text-a": "你好"})

    def test_rvpacker_receives_only_a_temporary_mirror_and_never_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            game = root / "Original Game"
            data = game / "data"
            data.mkdir(parents=True)
            (data / "System.json").write_text('{"gameTitle":"Example"}', encoding="utf-8")
            log = root / "args.json"
            fake = root / "rvpacker-txt-rs.py"
            fake.write_text(
                "import json, pathlib, sys\n"
                f"pathlib.Path({str(log)!r}).write_text(json.dumps(sys.argv[1:]), encoding='utf-8')\n",
                encoding="utf-8",
            )

            report = run_rvpacker_coverage(game, ["python", str(fake)])
            arguments = json.loads(log.read_text(encoding="utf-8"))

            self.assertTrue(report["available"])
            self.assertEqual(arguments[0], "read")
            self.assertNotIn("write", arguments)
            self.assertNotIn(str(game.resolve()), arguments)
            self.assertFalse(Path(arguments[2]).exists())


if __name__ == "__main__":
    unittest.main()
