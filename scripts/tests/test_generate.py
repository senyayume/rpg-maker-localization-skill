import json
import tempfile
import unittest
from pathlib import Path

from rpg_localization.extract import extract_game
from rpg_localization.generate import generate_patch, verify_patch
from rpg_localization.tasks import prepare_tasks


class PatchGenerationTests(unittest.TestCase):
    def test_generate_changes_only_translatable_paths_and_verifies_structure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            game = root / "Game"
            data_dir = game / "data"
            data_dir.mkdir(parents=True)
            original = [
                None,
                {
                    "id": 1,
                    "name": "Potion",
                    "description": "Restore HP",
                    "price": 50,
                    "traits": [{"code": 11, "value": 0.5}],
                },
            ]
            (data_dir / "Items.json").write_text(json.dumps(original), encoding="utf-8")
            extracted = extract_game(game)
            prepared = prepare_tasks(extracted["tasks"])
            mapping = {
                task["id"]: {"Potion": "药水", "Restore HP": "恢复生命值"}[task["source"]]
                for task in prepared["tasks"]
            }
            output = root / "patch"

            result = generate_patch(game, prepared, mapping, output)
            verification = verify_patch(game, output, prepared)

            translated = json.loads((output / "data" / "Items.json").read_text(encoding="utf-8"))
            self.assertEqual(result["files"], 1)
            self.assertEqual(translated[1]["name"], "药水")
            self.assertEqual(translated[1]["description"], "恢复生命值")
            self.assertEqual(translated[1]["price"], 50)
            self.assertEqual(translated[1]["traits"], original[1]["traits"])
            self.assertTrue(verification["ok"])
            self.assertEqual(verification["issues"], [])


if __name__ == "__main__":
    unittest.main()
