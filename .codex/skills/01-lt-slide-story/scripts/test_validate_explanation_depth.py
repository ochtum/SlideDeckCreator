#!/usr/bin/env python3
import unittest
from pathlib import Path

import validate_explanation_depth as target


class ExplanationDepthTests(unittest.TestCase):
    def test_valid_long_form_story(self):
        slides = []
        for index in range(8):
            role = "goal" if index == 0 else "evidence"
            slides.append(
                {
                    "id": f"s{index + 1}",
                    "role": role,
                    "title": f"title {index}",
                    "message": f"message {index}",
                    "evidence_artifact_ids": [] if role == "goal" else [f"artifact-{index}"],
                    "delivery": {
                        "mode": "explain",
                        "estimated_seconds": 135,
                        "talking_points": [f"mechanism {index}", f"decision {index}"],
                        "visible_anchors": [f"file-{index}.json", f"value-{index}"],
                    },
                }
            )
        story = {
            "project": {
                "duration_minutes": 20,
                "time_budget": {
                    "content_seconds": 1080,
                    "demo_seconds": 0,
                    "interaction_seconds": 0,
                    "buffer_seconds": 120,
                },
            },
            "slides": slides,
        }
        self.assertEqual([], target.validate_story(Path("story.yaml"), story))

    def test_generic_checklist_fails(self):
        slide = {
            "id": "s1",
            "role": "evidence",
            "delivery": {"mode": "explain"},
            "content_model": {
                "type": "checklist",
                "source_artifacts": [],
                "data": {
                    "items": ["対象を確認する", "証拠を残す", "完了条件を確認する"]
                },
            },
        }
        errors = []
        target.validate_content_model(Path("blueprint.yaml"), slide, errors)
        self.assertTrue(any("generic" in error for error in errors))

    def test_qa_and_appendix_are_excluded_from_live_delivery_total(self):
        slides = []
        for index in range(5):
            slides.append({
                "id": f"s{index + 1}",
                "role": "evidence",
                "delivery_scope": "live",
                "title": f"比較 {index}",
                "message": f"判断 {index}",
                "evidence_artifact_ids": [f"artifact-{index}"],
                "delivery": {
                    "mode": "explain",
                    "estimated_seconds": 180,
                    "talking_points": [f"比較条件 {index}", f"判断結果 {index}"],
                    "visible_anchors": [f"条件 {index}", f"差分 {index}"],
                },
            })
        slides.append({
            "id": "a1",
            "role": "evidence",
            "delivery_scope": "appendix",
            "title": "補足",
            "message": "後読用の完全表",
        })
        story = {
            "project": {
                "duration_minutes": 20,
                "knowledge_contract_version": 1,
                "time_budget": {
                    "content_seconds": 900,
                    "demo_seconds": 0,
                    "interaction_seconds": 0,
                    "q_and_a_seconds": 120,
                    "buffer_seconds": 180,
                },
            },
            "slides": slides,
        }
        self.assertEqual([], target.validate_story(Path("story.yaml"), story))


if __name__ == "__main__":
    unittest.main()
