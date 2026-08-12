import unittest

from rpg_localization.tasks import prepare_tasks
from rpg_localization.validate import validate_mapping


class MappingValidationTests(unittest.TestCase):
    def test_validation_reports_structural_and_translation_quality_issues(self) -> None:
        prepared = prepare_tasks(
            [
                {
                    "occurrence_id": "Map001.json#/a",
                    "file": "Map001.json",
                    "path": "/a",
                    "source": "Use Potion, \\N[1].",
                    "context": "dialogue",
                },
                {
                    "occurrence_id": "Map001.json#/b",
                    "file": "Map001.json",
                    "path": "/b",
                    "source": "Leave",
                    "context": "choice",
                },
            ],
            glossary={"Potion": "药水"},
        )
        potion = next(task for task in prepared["tasks"] if "Potion" in task["source"])
        leave = next(task for task in prepared["tasks"] if task["source"] == "Leave")
        mapping = {
            potion["id"]: "使用恢复剂。",
            leave["id"]: "Leave",
            "text-unknown": "未知",
        }

        report = validate_mapping(prepared, mapping)

        codes = {issue["code"] for issue in report["issues"]}
        self.assertIn("unknown_mapping_id", codes)
        self.assertIn("control_code_mismatch", codes)
        self.assertIn("glossary_mismatch", codes)
        self.assertIn("source_language_residual", codes)
        self.assertFalse(report["ok"])
        self.assertEqual(report["review_tasks"][0]["id"], leave["id"])

    def test_valid_mapping_passes(self) -> None:
        prepared = prepare_tasks(
            [
                {
                    "occurrence_id": "Map001.json#/a",
                    "file": "Map001.json",
                    "path": "/a",
                    "source": "Use Potion, \\N[1].",
                    "context": "dialogue",
                }
            ],
            glossary={"Potion": "药水"},
        )
        task = prepared["tasks"][0]

        report = validate_mapping(prepared, {task["id"]: "使用药水，\\N[1]。"})

        self.assertTrue(report["ok"])
        self.assertEqual(report["issues"], [])


if __name__ == "__main__":
    unittest.main()
