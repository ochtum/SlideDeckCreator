from pathlib import Path
import tempfile
import unittest

import yaml

from manage_design_system import add, load_registry, remove, update, validate_registry, validate_spec


def spec(version="1.0.0"):
    return {
        "schema_version": 1, "kind": "lt-design-system", "id": "test-blue", "name": "Test Blue", "version": version,
        "description": "test", "personality": ["trustworthy"],
        "tokens": {
            "canvas": {"width": 1280, "height": 720, "safe_margin": 48},
            "colors": {"background": "#FFFFFF", "surface": "#F5F9FF", "text": "#08224A", "muted_text": "#52637A", "primary": "#135FCA", "secondary": "#007F74", "accent": "#B64700", "border": "#C9D7EA", "success": "#08783E", "warning": "#9A5B00", "danger": "#B42318"},
            "typography": {"family": "system-ui", "mono_family": "monospace", "title_px": 68, "heading_px": 48, "body_px": 30, "detail_px": 24, "source_px": 18, "title_weight": 900, "body_weight": 600},
            "spacing": {"xs": 8, "sm": 16, "md": 24, "lg": 40, "xl": 64}, "shape": {"radius_card": 20},
        },
        "layouts": {"density": "standard", "preferred": ["flow"], "max_columns": 3},
        "components": {"code": {"background": "#07162C", "text": "#ECF4FF"}, "conclusion": {"text": "#FFFFFF"}},
        "motion": {"energy": "standard", "preferred_families": ["quiet-reveal"], "strong_moment_limit_percent": 20},
        "accessibility": {"body_contrast_min": 4.5, "large_text_contrast_min": 3.0, "reduced_motion": True, "color_only_meaning": False},
        "usage": {"do": [], "dont": []},
    }


class DesignSystemManagerTest(unittest.TestCase):
    def test_crud_keeps_history_and_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            project = Path(folder)
            root = project / "config" / "design-systems"
            first = project / "first.yaml"
            first.write_text(yaml.safe_dump(spec()), encoding="utf-8")
            add(root, first)
            self.assertEqual([], validate_registry(root))
            with self.assertRaises(ValueError):
                add(root, first)
            second = project / "second.yaml"
            second.write_text(yaml.safe_dump(spec("1.1.0")), encoding="utf-8")
            update(root, "test-blue", second)
            self.assertTrue(any((root / "test-blue" / "history").iterdir()))
            remove(root, project, "test-blue", True, False)
            self.assertEqual([], load_registry(root)["systems"])
            self.assertTrue(any((root / "_archive").iterdir()))

    def test_low_contrast_fails(self):
        value = spec()
        value["tokens"]["colors"]["text"] = "#EEEEEE"
        self.assertTrue(any("contrast" in error for error in validate_spec(value)))


if __name__ == "__main__":
    unittest.main()
