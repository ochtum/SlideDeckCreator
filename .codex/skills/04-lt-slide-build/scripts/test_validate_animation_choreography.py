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


if __name__ == "__main__":
    unittest.main()
