from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import yaml

import validate_duration_floor as target


class DurationFloorTests(unittest.TestCase):
    def test_historical_floor_is_advisory_but_scoped_counts_are_contractual(self):
        story = {
            "project": {
                "duration_minutes": 30,
                "target_slide_count": 2,
                "appendix_slide_count": 1,
            },
            "slides": [
                {"id": "cover", "role": "cover", "delivery_scope": "live"},
                {"id": "evidence", "role": "evidence", "delivery_scope": "live"},
                {"id": "recap", "role": "recap", "delivery_scope": "live"},
                {"id": "thanks", "role": "thanks", "delivery_scope": "live"},
                {"id": "a1", "role": "evidence", "delivery_scope": "appendix"},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "story.yaml"
            path.write_text(yaml.safe_dump(story), encoding="utf-8")
            errors, parts = target.validate_story(path)
        self.assertEqual([], errors)
        self.assertEqual(1, len(parts))
        self.assertLess(target.body_count(story["slides"]), target.minimum_body_slides(30))

    def test_target_still_rejects_wrong_live_count(self):
        story = {
            "project": {"duration_minutes": 10, "target_slide_count": 2},
            "slides": [{"id": "s1", "role": "evidence", "delivery_scope": "live"}],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "story.yaml"
            path.write_text(yaml.safe_dump(story), encoding="utf-8")
            errors, _ = target.validate_story(path)
        self.assertTrue(any("target_slide_count" in error for error in errors))

    @staticmethod
    def series_part(source_count: int, timings: tuple[int, int, int] = (30, 45, 30)) -> dict:
        return {
            "project": {"duration_minutes": 30, "target_slide_count": 3},
            "slides": [
                {
                    "id": "goal",
                    "role": "goal",
                    "delivery_scope": "live",
                    "flow_phase": "",
                    "source_unit_ids": [],
                    "delivery": {"estimated_seconds": timings[0]},
                },
                {
                    "id": "example",
                    "role": "evidence",
                    "delivery_scope": "live",
                    "flow_phase": "explain",
                    "source_unit_ids": [f"u{index}" for index in range(source_count)],
                    "delivery": {"estimated_seconds": timings[1]},
                },
                {
                    "id": "recap",
                    "role": "recap",
                    "delivery_scope": "live",
                    "flow_phase": "explain",
                    "source_unit_ids": [],
                    "delivery": {"estimated_seconds": timings[2]},
                },
            ],
        }

    def test_rejects_mechanically_uniform_series_with_different_source_loads(self):
        manifest = {"kind": "lt-slide-series", "series_analysis": {}}
        parts = [
            (Path(f"part-{index}/01-story.yaml"), self.series_part(count))
            for index, count in enumerate((4, 11, 7), 1)
        ]
        errors = target.validate_series_uniformity(Path("01-story.yaml"), manifest, parts)
        self.assertTrue(any("mechanically uniform series" in error for error in errors))

    def test_allows_equal_counts_when_timing_structure_is_independently_derived(self):
        manifest = {"kind": "lt-slide-series", "series_analysis": {}}
        parts = [
            (Path("part-1/01-story.yaml"), self.series_part(4, (30, 45, 30))),
            (Path("part-2/01-story.yaml"), self.series_part(11, (30, 60, 30))),
            (Path("part-3/01-story.yaml"), self.series_part(7, (30, 50, 30))),
        ]
        self.assertEqual([], target.validate_series_uniformity(Path("01-story.yaml"), manifest, parts))

    def test_allows_explicit_user_requested_uniform_structure(self):
        manifest = {
            "kind": "lt-slide-series",
            "series_analysis": {
                "uniform_structure_request": {
                    "requested_by_user": True,
                    "reason": "同一研修フォーマットで配布するため",
                }
            },
        }
        parts = [
            (Path(f"part-{index}/01-story.yaml"), self.series_part(count))
            for index, count in enumerate((4, 11, 7), 1)
        ]
        self.assertEqual([], target.validate_series_uniformity(Path("01-story.yaml"), manifest, parts))


if __name__ == "__main__":
    unittest.main()
