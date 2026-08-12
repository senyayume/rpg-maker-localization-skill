import tempfile
import unittest
from pathlib import Path

from rpg_localization.audit import audit_game


FIXTURES = Path(__file__).parents[2] / "assets" / "fixtures"


class AuditTests(unittest.TestCase):
    def test_audit_identifies_mz_and_reports_encrypted_assets_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            game = Path(temporary) / "Game"
            (game / "data").mkdir(parents=True)
            (game / "js").mkdir()
            (game / "img").mkdir()
            (game / "data" / "System.json").write_text("{}", encoding="utf-8")
            (game / "data" / "Map001.json").write_text("{}", encoding="utf-8")
            (game / "js" / "rmmz_core.js").write_text("// MZ", encoding="utf-8")
            (game / "img" / "secret.png_").write_bytes(b"encrypted")
            before = sorted(path.relative_to(game).as_posix() for path in game.rglob("*"))

            report = audit_game(game)

            after = sorted(path.relative_to(game).as_posix() for path in game.rglob("*"))
            self.assertEqual(report["engine"], "rpg-maker-mz")
            self.assertEqual(report["json_files"], 2)
            self.assertEqual(report["encrypted_assets"], ["img/secret.png_"])
            self.assertEqual(before, after)

    def test_bundled_mv_and_mz_fixtures_are_self_contained(self) -> None:
        mv = audit_game(FIXTURES / "mv-minimal")
        mz = audit_game(FIXTURES / "mz-minimal")

        self.assertEqual(mv["engine"], "rpg-maker-mv")
        self.assertEqual(mz["engine"], "rpg-maker-mz")
        self.assertEqual(mv["issues"], [])
        self.assertEqual(mz["issues"], [])


if __name__ == "__main__":
    unittest.main()
