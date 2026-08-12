import unittest

from rpg_localization.checkpoints import create_checkpoint, resume_checkpoints
from rpg_localization.tasks import prepare_tasks


class CheckpointTests(unittest.TestCase):
    def test_checkpoint_rejects_structurally_invalid_partial_translation(self) -> None:
        prepared = prepare_tasks(
            [
                {
                    "occurrence_id": "Map001.json#/dialogue",
                    "file": "Map001.json",
                    "path": "/dialogue",
                    "source": "Hello, \\N[1].",
                    "context": "dialogue",
                }
            ]
        )
        identifier = prepared["tasks"][0]["id"]

        with self.assertRaisesRegex(ValueError, "control_code_mismatch"):
            create_checkpoint(
                prepared, {identifier: "你好。"}, source_fingerprint="source-a"
            )

    def test_resume_invalidates_entry_when_source_binding_changed(self) -> None:
        prepared = prepare_tasks(
            [
                {
                    "occurrence_id": "Items.json#/1/name",
                    "file": "Items.json",
                    "path": "/1/name",
                    "source": "Potion",
                    "context": "item_name",
                }
            ]
        )
        identifier = prepared["tasks"][0]["id"]
        checkpoint = create_checkpoint(
            prepared, {identifier: "药水"}, source_fingerprint="source-a"
        )
        checkpoint["entries"][0]["source"] = "Changed source"

        result = resume_checkpoints(prepared, [checkpoint])

        self.assertEqual(result["completed"], 0)
        self.assertEqual(result["remaining"], 1)
        self.assertEqual(result["invalid"], 1)

    def test_resume_rejects_conflicting_translations_for_same_id(self) -> None:
        prepared = prepare_tasks(
            [
                {
                    "occurrence_id": "Items.json#/1/name",
                    "file": "Items.json",
                    "path": "/1/name",
                    "source": "Potion",
                    "context": "item_name",
                }
            ]
        )
        identifier = prepared["tasks"][0]["id"]
        first = create_checkpoint(
            prepared, {identifier: "药水"}, source_fingerprint="source-a"
        )
        second = create_checkpoint(
            prepared, {identifier: "回复药"}, source_fingerprint="source-a"
        )

        with self.assertRaisesRegex(ValueError, "conflict"):
            resume_checkpoints(prepared, [first, second])


if __name__ == "__main__":
    unittest.main()
