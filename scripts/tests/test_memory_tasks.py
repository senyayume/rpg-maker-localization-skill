import unittest

from rpg_localization.tasks import prepare_tasks


class TaskPreparationTests(unittest.TestCase):
    def test_exact_sources_are_deduplicated_with_all_occurrences_and_term_subset(self) -> None:
        occurrences = [
            {
                "occurrence_id": "Map001.json#/a",
                "file": "Map001.json",
                "path": "/a",
                "source": "Use Potion, \\N[1].",
                "context": "dialogue",
            },
            {
                "occurrence_id": "Map002.json#/b",
                "file": "Map002.json",
                "path": "/b",
                "source": "Use Potion, \\N[1].",
                "context": "dialogue",
            },
            {
                "occurrence_id": "Map003.json#/c",
                "file": "Map003.json",
                "path": "/c",
                "source": "Leave",
                "context": "choice",
            },
        ]

        first = prepare_tasks(occurrences, glossary={"Potion": "药水"})
        second = prepare_tasks(list(reversed(occurrences)), glossary={"Potion": "药水"})

        self.assertEqual(first, second)
        self.assertEqual(len(first["tasks"]), 2)
        potion = next(task for task in first["tasks"] if "Potion" in task["source"])
        self.assertEqual(len(potion["occurrences"]), 2)
        self.assertEqual(potion["signature"]["control_codes"], ["\\N[1]"])
        self.assertEqual(first["glossary_subset"], {"Potion": "药水"})
        self.assertTrue(potion["id"].startswith("text-"))


if __name__ == "__main__":
    unittest.main()
