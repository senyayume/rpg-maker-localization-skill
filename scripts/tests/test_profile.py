import tempfile
import unittest
from pathlib import Path

from rpg_localization.profile import bind_workspace, init_workspace


class WorkspaceProfileTests(unittest.TestCase):
    def test_init_creates_portable_workspace_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "示例-localization"

            result = init_workspace(workspace, engine="rpg-maker-mz")

            self.assertEqual(result["engine"], "rpg-maker-mz")
            self.assertTrue((workspace / "localization.yaml").is_file())
            self.assertTrue((workspace / "glossary.json").is_file())
            self.assertTrue((workspace / "style-guide.md").is_file())
            self.assertTrue((workspace / "rules" / "plugin-text.json").is_file())
            for directory in (
                "translations/memory",
                "translations/batches",
                "translations/staging",
                "translations/accepted",
                "reports",
                ".local",
                "dist",
            ):
                self.assertTrue((workspace / directory).is_dir(), directory)

    def test_bind_reuses_identical_source_at_a_new_absolute_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first_game = root / "电脑甲" / "Game"
            second_game = root / "电脑乙" / "Game"
            workspace = root / "localization"
            for game in (first_game, second_game):
                (game / "data").mkdir(parents=True)
                (game / "data" / "System.json").write_text(
                    '{"gameTitle":"Example"}', encoding="utf-8"
                )
            init_workspace(workspace, engine="rpg-maker-mz")

            first = bind_workspace(workspace, first_game)
            second = bind_workspace(workspace, second_game)

            self.assertEqual(first["source_fingerprint"], second["source_fingerprint"])
            self.assertTrue(second["reused"])
            self.assertEqual(second["source"], str(second_game.resolve()))


if __name__ == "__main__":
    unittest.main()
