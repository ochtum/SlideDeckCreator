import unittest

from validate_animation_choreography import validate


class AnimationChoreographyTest(unittest.TestCase):
    def test_repetitive_long_deck_fails(self):
        slides = [{"id": f"s{i}", "animation": {
            "intent": "順序を示す", "family": "quiet-reveal",
            "entrance": [{"target": "title", "preset": "rise"}],
            "steps": [{"step": n, "targets": [f"x{n}"], "preset": "rise"} for n in range(1, 4)],
        }} for i in range(20)]
        errors, _ = validate({"slides": slides})
        self.assertTrue(any("at least 5 presets" in error for error in errors))
        self.assertTrue(any("pacing is too uniform" in error for error in errors))

    def test_blueprint_preset_loss_fails(self):
        blueprint = {"slides": [{"id": "s1", "animation": {
            "intent": "線を順に示す", "family": "structure",
            "entrance": [{"target": "title", "preset": "fade"}],
            "steps": [{"step": 1, "targets": ["line"], "preset": "draw"}],
        }}]}
        html = '<section class="slide"><h2 data-anim="rise"></h2></section>'
        errors, _ = validate(blueprint, html)
        self.assertTrue(any("lost or normalized" in error for error in errors))

    def test_strong_preset_on_non_completion_target_fails(self):
        blueprint = {"slides": [{"id": "s1", "animation": {
            "intent": "項目を順に示す", "family": "decision",
            "selection": {"rule_id": "content:checklist", "rationale": "判定順"},
            "entrance": [{"target": "title", "preset": "fade", "reason": "title"}],
            "steps": [{
                "step": 1, "targets": ["item-1"], "preset": "stamp", "reason": "too strong",
                "target_presets": {"item-1": "stamp"},
                "target_reasons": {"item-1": "too strong"},
            }],
            "sequence": {"mode": "item-by-item", "max_steps": 1, "completion_targets": []},
        }}]}
        errors, _ = validate(blueprint)
        self.assertTrue(any("not reserved for completion" in error for error in errors))

    def test_target_specific_connection_draw_passes_compatibility(self):
        blueprint = {"slides": [{"id": "s1", "animation": {
            "intent": "接続と工程を示す", "family": "structure",
            "selection": {"rule_id": "content:flow", "rationale": "接続から工程"},
            "entrance": [{"target": "title", "preset": "fade", "reason": "title"}],
            "steps": [{
                "step": 1, "targets": ["connection", "item-1"], "preset": "rise", "reason": "first item",
                "target_presets": {"connection": "draw", "item-1": "rise"},
                "target_reasons": {"connection": "line", "item-1": "ordered item"},
            }],
            "sequence": {"mode": "item-by-item", "max_steps": 1, "completion_targets": []},
        }}]}
        errors, _ = validate(blueprint)
        self.assertFalse(any("incompatible" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
