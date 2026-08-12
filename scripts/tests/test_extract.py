import json
import tempfile
import unittest
from pathlib import Path

from rpg_localization.extract import extract_game


class ExtractionTests(unittest.TestCase):
    def test_extracts_standard_fields_and_discovers_unconfirmed_plugin_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            game = Path(temporary) / "Game"
            data = game / "data"
            data.mkdir(parents=True)
            (data / "Items.json").write_text(
                json.dumps(
                    [None, {"name": "Potion", "description": "Restore %1 HP", "note": "<internal>"}]
                ),
                encoding="utf-8",
            )
            (data / "Map001.json").write_text(
                json.dumps(
                    {
                        "displayName": "Village",
                        "events": [
                            None,
                            {
                                "pages": [
                                    {
                                        "list": [
                                            {"code": 101, "parameters": ["", 0, 0, 2, "Atla"]},
                                            {"code": 401, "parameters": ["Wait, \\N[1]!"]},
                                            {"code": 102, "parameters": [["Save", "Leave"], 0, 0, 2, 0]},
                                            {"code": 402, "parameters": [0, "Save"]},
                                            {
                                                "code": 357,
                                                "parameters": [
                                                    "DTextPicture",
                                                    "dText",
                                                    "Display text",
                                                    {"text": "Status", "internalKey": "do_not_translate"},
                                                ],
                                            },
                                        ]
                                    }
                                ]
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            rules = [
                {
                    "plugin": "DTextPicture",
                    "command": "dText",
                    "argument": "text",
                    "context": "plugin_text",
                }
            ]

            report = extract_game(game, plugin_rules=rules)

            sources = {task["source"] for task in report["tasks"]}
            self.assertEqual(
                sources,
                {
                    "Potion",
                    "Restore %1 HP",
                    "Village",
                    "Atla",
                    "Wait, \\N[1]!",
                    "Save",
                    "Leave",
                    "Status",
                },
            )
            branch = next(
                task for task in report["tasks"] if task["path"].endswith("/3/parameters/1")
            )
            self.assertEqual(branch["context"], "choice_branch")
            self.assertTrue(
                any(item["value"] == "do_not_translate" for item in report["discoveries"])
            )
            self.assertFalse(any(task["source"] == "<internal>" for task in report["tasks"]))

    def test_extracts_extended_mv_mz_visible_text_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            game = Path(temporary) / "Game"
            data = game / "data"
            data.mkdir(parents=True)
            (data / "System.json").write_text(
                json.dumps({"variables": ["", "Quest status"], "terms": {}}),
                encoding="utf-8",
            )
            (data / "Items.json").write_text(
                json.dumps([None, {"name": "Book", "description": "Read", "note": "<SG説明: Lore text>"}]),
                encoding="utf-8",
            )
            (data / "CommonEvents.json").write_text(
                json.dumps(
                    [
                        None,
                        {
                            "name": "Quest update",
                            "list": [
                                {"code": 122, "parameters": [1, 1, 0, 4, '"Dynamic label"']},
                                {"code": 108, "parameters": ["選択肢ヘルプ"]},
                                {"code": 408, "parameters": ["Choose carefully"]},
                                {"code": 408, "parameters": ["\\>"]},
                            ],
                        },
                    ]
                ),
                encoding="utf-8",
            )
            (data / "Troops.json").write_text(
                json.dumps(
                    [
                        None,
                        {
                            "name": "Slime Group",
                            "pages": [{"list": [{"code": 401, "parameters": ["Slimes appear!"]}]}],
                        },
                    ]
                ),
                encoding="utf-8",
            )

            report = extract_game(game)
            sources = {task["source"] for task in report["tasks"]}

            self.assertTrue(
                {
                    "Quest status",
                    "<SG説明: Lore text>",
                    "Quest update",
                    '"Dynamic label"',
                    "Choose carefully",
                    "Slime Group",
                    "Slimes appear!",
                }.issubset(sources)
            )
            self.assertNotIn("\\>", sources)


if __name__ == "__main__":
    unittest.main()
