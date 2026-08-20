import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("validate_roadmap.py")
SPEC = importlib.util.spec_from_file_location("validate_roadmap", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def sample_story():
    items = [
        {
            "phase": "why",
            "label": "判断できない理由",
            "summary": "コード外の知識を確認する",
            "slide_ids": ["s04", "s05"],
            "page_start": 4,
            "page_end": 5,
            "start_title": "コードだけでは決められない",
            "end_title": "暗黙知は検索できない",
        },
        {
            "phase": "takeaway",
            "label": "明日始める",
            "summary": "一機能の地図を残す",
            "slide_ids": ["s06"],
            "page_start": 6,
            "page_end": 6,
            "start_title": "一機能の地図を作る",
            "end_title": "一機能の地図を作る",
        },
    ]
    return {
        "project": {"duration_minutes": 30},
        "roadmap": {"source": "generated-from-slides", "slide_id": "s03", "items": items},
        "slides": [
            {"id": "s01", "role": "cover", "flow_phase": "", "title": "表紙"},
            {"id": "s02", "role": "goal", "flow_phase": "", "title": "ゴール"},
            {
                "id": "s03",
                "role": "flow",
                "flow_phase": "",
                "title": "道筋",
                "content_model": {"data": {"steps": items}},
            },
            {"id": "s04", "role": "problem", "flow_phase": "why", "title": "コードだけでは決められない"},
            {"id": "s05", "role": "evidence", "flow_phase": "why", "title": "暗黙知は検索できない"},
            {"id": "s06", "role": "recap", "flow_phase": "takeaway", "title": "一機能の地図を作る"},
            {"id": "s07", "role": "thanks", "flow_phase": "", "title": "Thank you"},
        ],
    }


class RoadmapValidationTests(unittest.TestCase):
    def test_accepts_story_derived_roadmap(self):
        errors, _, _ = MODULE.validate_yaml_contract(sample_story(), Path("story.yaml"))
        self.assertEqual([], errors)

    def test_rejects_phase_name_as_visible_label(self):
        story = sample_story()
        story["roadmap"]["items"][0]["label"] = "Why"
        story["slides"][2]["content_model"]["data"]["steps"] = story["roadmap"]["items"]
        errors, _, _ = MODULE.validate_yaml_contract(story, Path("story.yaml"))
        self.assertTrue(any("concrete milestone label" in error for error in errors))

    def test_rejects_stale_page_range(self):
        story = sample_story()
        story["roadmap"]["items"][0]["page_end"] = 99
        story["slides"][2]["content_model"]["data"]["steps"] = story["roadmap"]["items"]
        errors, _, _ = MODULE.validate_yaml_contract(story, Path("story.yaml"))
        self.assertTrue(any("page range must be" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
