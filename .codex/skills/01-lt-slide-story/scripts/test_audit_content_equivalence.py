from pathlib import Path
import tempfile
import unittest

import yaml

from audit_content_equivalence import build_inventory, validate


class ContentEquivalenceTest(unittest.TestCase):
    def test_inventory_and_full_trace(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "guide.md"
            source.write_text("## 手順\n説明です。\n\n| Key | Value |\n| --- | --- |\n| A | B |\n\n```yaml\na: b\n```\n", encoding="utf-8")
            inventory = build_inventory([source], root)
            self.assertEqual({"section", "table", "config"}, {unit["kind"] for unit in inventory["units"]})
            matrix = []
            for unit in inventory["units"]:
                structured = unit["kind"] != "section"
                matrix.append({
                    "unit_id": unit["id"], "parts": ["p1"], "slide_ids": ["s1"],
                    "delivery_surfaces": ["visible"],
                    "preservation": "structure-preserved" if structured else "explain",
                    "artifact_ids": ["a1"] if structured else [], "status": "covered",
                })
            story = {"project": {"content_fidelity": "full-equivalence"}, "coverage_matrix": matrix}
            errors, result = validate(inventory, story, [], True)
            self.assertEqual([], errors)
            self.assertEqual(3, result["covered_units"])

    def test_topic_only_coverage_fails(self):
        inventory = {"units": [{"id": "x-table-001", "kind": "table"}]}
        story = {"project": {"content_fidelity": "full-equivalence"}, "coverage_matrix": [{
            "unit_id": "x-table-001", "parts": ["p"], "slide_ids": ["s"],
            "preservation": "explain", "artifact_ids": [], "status": "covered",
        }]}
        errors, _ = validate(inventory, story, [], True)
        self.assertTrue(any("does not preserve" in error for error in errors))
        self.assertTrue(any("artifact_ids" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
