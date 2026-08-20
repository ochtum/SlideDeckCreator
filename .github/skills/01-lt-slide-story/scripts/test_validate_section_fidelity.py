from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from validate_section_fidelity import (
    build_manifest,
    validate_blueprint,
    validate_html,
    validate_story,
)


SECTION_ID = "guide-a1b2c3-section-001"
POINT_ID = "section-001-p01"


def manifest() -> dict:
    return {
        "schema_version": 1,
        "kind": "lt-source-sections",
        "sections": [{
            "id": SECTION_ID,
            "source": "guide.md",
            "order": 1,
            "heading_level": 1,
            "heading": "記事の結論",
            "kind": "content",
            "char_count": 30,
            "asset_kinds": [],
        }],
    }


def story() -> dict:
    spoken = "保守担当者は四つの正本を役割で分けます。"
    visible = "四つの正本を役割で分ける"
    return {
        "project": {"authoring_mode": "section-faithful"},
        "section_coverage": [{
            "section_id": SECTION_ID,
            "slide_ids": ["s01"],
            "coverage": "full",
            "abridgement_note": "",
            "split_reason": "",
            "points": [{
                "id": POINT_ID,
                "text": "四つの正本は役割で分ける",
                "importance": "essential",
            }],
        }],
        "slides": [{
            "id": "s01",
            "role": "action",
            "delivery_scope": "live",
            "title": "記事の結論",
            "message": visible,
            "support": [],
            "source_section_ids": [SECTION_ID],
            "talk_track": {
                "source_section_id": SECTION_ID,
                "beats": [{
                    "point_id": POINT_ID,
                    "spoken_text": spoken,
                    "visible_text": visible,
                }],
            },
            "speaker_cue": {"script": spoken},
            "spoken_note": (
                "橋渡し: 前提から結論へ進みます。\n"
                f"話す内容: {spoken}\n"
                f"指差し: {visible}\n"
                "次の一言: 次の節へ進みます。"
            ),
        }],
    }


class SectionFidelityTests(unittest.TestCase):
    def test_manifest_ignores_headings_inside_code_fences(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "guide.md"
            source.write_text(
                "# 文書タイトル\n導入です。\n\n"
                "## 本文\n説明です。\n\n"
                "```markdown\n# コード内見出し\n```\n\n"
                "### 補足\n注意です。\n",
                encoding="utf-8",
            )
            result = build_manifest([source], root)
            self.assertEqual(["文書タイトル", "本文", "補足"], [item["heading"] for item in result["sections"]])
            self.assertEqual([1, 2, 3], [item["heading_level"] for item in result["sections"]])

    def test_good_story_passes(self) -> None:
        self.assertEqual([], validate_story(Path("story.yaml"), manifest(), story()))

    def test_multiple_sections_cannot_share_one_slide(self) -> None:
        source_manifest = manifest()
        second = deepcopy(source_manifest["sections"][0])
        second.update({"id": "guide-a1b2c3-section-002", "order": 2, "heading": "次の節"})
        source_manifest["sections"].append(second)
        value = story()
        value["section_coverage"].append({
            "section_id": second["id"],
            "slide_ids": ["s01"],
            "coverage": "full",
            "points": [{"id": "section-002-p01", "text": "次の要点", "importance": "essential"}],
        })
        value["slides"][0]["source_section_ids"] = [SECTION_ID, second["id"]]
        errors = validate_story(Path("story.yaml"), source_manifest, value)
        self.assertTrue(any("cannot merge multiple source sections" in error for error in errors))

    def test_every_section_point_requires_a_talk_track_beat(self) -> None:
        value = story()
        value["section_coverage"][0]["points"].append({
            "id": "section-001-p02",
            "text": "正本を複製しない",
            "importance": "essential",
        })
        errors = validate_story(Path("story.yaml"), manifest(), value)
        self.assertTrue(any("points are missing" in error for error in errors))

    def test_blueprint_ignores_validator_only_content_model_keys(self) -> None:
        value = story()
        source = value["slides"][0]
        visible = source["talk_track"]["beats"][0]["visible_text"]
        blueprint = {"slides": [{
            "id": "s01",
            "source_section_ids": source["source_section_ids"],
            "talk_track": source["talk_track"],
            "title": source["title"],
            "message": "短縮して消した文",
            "text": {},
            "visual": {"annotations": []},
            "content_model": {"semantic_support": [visible]},
        }]}
        errors = validate_blueprint(Path("blueprint.yaml"), blueprint, value)
        self.assertTrue(any("not rendered by Blueprint" in error for error in errors))

        blueprint["slides"][0]["content_model"] = {"data": {"label": visible}}
        self.assertEqual([], validate_blueprint(Path("blueprint.yaml"), blueprint, value))

    def test_html_requires_visible_text_and_source_section_attribute(self) -> None:
        value = story()
        visible = value["slides"][0]["talk_track"]["beats"][0]["visible_text"]
        good = (
            f'<section class="slide" data-slide-id="s01" data-source-section-ids="{SECTION_ID}">'
            f"<h1>{visible}</h1></section>"
        )
        self.assertEqual([], validate_html(Path("index.html"), good, value))
        errors = validate_html(Path("index.html"), good.replace(visible, "別の要約"), value)
        self.assertTrue(any("missing from HTML" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
