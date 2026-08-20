from __future__ import annotations

import unittest

import validate_style_profile as target


class StyleProfileSlideCountTests(unittest.TestCase):
    def test_rejects_absolute_body_slide_floor(self):
        limits = "本文は各回28枚以上を品質下限とする。"
        self.assertTrue(target.absolute_slide_count_rules(limits))

    def test_allows_component_ratio_and_transition_range(self):
        limits = """
        - 10〜15分では感情や転換だけを担う独立スライドは1〜2枚を目安とする。
        duration_limits:
          thirty_minutes_or_more:
            statement_slides_max_ratio: 0.12
        """
        self.assertEqual([], target.absolute_slide_count_rules(limits))

    def test_rejects_structured_target_field(self):
        limits = "target_slide_count: 28"
        self.assertTrue(target.absolute_slide_count_rules(limits))


if __name__ == "__main__":
    unittest.main()
