from copy import deepcopy
from pathlib import Path
import unittest

from speaker_notes import parse_note, render_note
from validate_spoken_notes import validate_slides
from validate_talkability import validate_story, validate_html
from html import escape
import tempfile
from validate_section_fidelity import validate_story as validate_sections
from test_validate_talkability import good_story
from test_validate_section_fidelity import story as section_story, manifest


def cue_story():
    story = good_story()
    story["project"]["talkability_version"] = 3
    for slide in story["slides"]:
        cue = slide["speaker_cue"]
        cue.update(mode="cue", cues=[f"{slide['id']}：比較する時刻をそろえる"], script="", transition="")
        slide["connection_from_previous"]["bridge"] = ""
        slide["spoken_note"] = render_note(slide)
    return story


class SpeakerNotesTests(unittest.TestCase):
    def test_short_cues_pass_long_talk_without_padding(self):
        self.assertEqual([], validate_story(Path("story.yaml"), cue_story()))

    def test_hybrid_roundtrip_and_optional_transition(self):
        slide = cue_story()["slides"][3]
        slide["speaker_cue"].update(mode="hybrid", script="気温と時刻をそろえて比べます。", transition="差分を見ます。", next_slide_id="why-2")
        slide["spoken_note"] = render_note(slide)
        parsed, bridge = parse_note(slide["spoken_note"])
        self.assertEqual(slide["speaker_cue"]["script"], parsed["script"])
        self.assertEqual("", bridge)
        errors, _ = validate_slides([slide, cue_story()["slides"][4]], 3)
        self.assertEqual([], errors)

    def test_wrong_next_slide_and_last_page_transition_fail(self):
        story = cue_story()
        slide = story["slides"][-1]
        slide["speaker_cue"].update(transition="存在しないページへ進みます。", next_slide_id="missing")
        slide["spoken_note"] = render_note(slide)
        self.assertTrue(any("次のスライド" in err for err in validate_story(Path("story.yaml"), story)))

    def test_deliberate_reading_time_is_not_missing_note(self):
        story = cue_story()
        slide = story["slides"][3]
        slide["speaker_cue"].update(cues=[], silence_reason="二つの値を見比べる時間を取る")
        slide["spoken_note"] = render_note(slide)
        self.assertEqual([], validate_story(Path("story.yaml"), story))
        slide["speaker_cue"]["silence_reason"] = ""
        slide["spoken_note"] = render_note(slide)
        self.assertTrue(validate_story(Path("story.yaml"), story))

    def test_note_cannot_drift_from_structured_cue(self):
        story = cue_story()
        story["slides"][3]["spoken_note"] += "\n要点: 構造データにない追加"
        self.assertTrue(any("一致" in err for err in validate_story(Path("story.yaml"), story)))

    def test_ambiguous_or_unknown_lines_fail(self):
        for note in ("形式: cue\n要点: 一つ\n余計な行", "形式: cue\n形式: hybrid\n要点: 一つ", "形式: unknown\n要点: 一つ"):
            with self.subTest(note=note), self.assertRaises(ValueError):
                parse_note(note)

    def test_malformed_structured_cue_is_reported_without_crashing(self):
        story = cue_story()
        story["slides"][3]["speaker_cue"]["cues"] = "配列ではない"
        errors, _ = validate_slides(story["slides"], 3)
        self.assertTrue(any("配列" in err for err in errors))

    def test_short_talk_checks_actual_visible_point(self):
        slide = cue_story()["slides"][3]
        slide["flow_phase"] = ""
        story = {"project": {"talkability_version": 3, "duration_minutes": 5}, "slides": [slide]}
        self.assertEqual([], validate_story(Path("story.yaml"), story))
        attrs = f'data-slide-id="{slide["id"]}" data-flow-phase="" data-speaker-purpose="{escape(slide["speaker_cue"]["purpose"])}" data-spoken-note="{escape(slide["spoken_note"], quote=True)}"'
        with tempfile.TemporaryDirectory() as folder:
            html = Path(folder) / "index.html"
            html.write_text(f'<section class="slide" {attrs}>別の表示</section>', encoding="utf-8")
            self.assertTrue(any("point_at" in err for err in validate_html(html, story)))
            html.write_text(f'<section class="slide" {attrs}>夜20時の使用量</section>', encoding="utf-8")
            self.assertEqual([], validate_html(html, story))

    def test_visual_beat_does_not_need_to_be_spoken(self):
        story = section_story()
        story["project"]["talkability_version"] = 3
        beat = story["slides"][0]["talk_track"]["beats"][0]
        beat.update(delivery="visual", spoken_text="")
        self.assertEqual([], validate_sections(Path("story.yaml"), manifest(), story))
        beat["visible_text"] = ""
        self.assertTrue(any("visual beat" in err for err in validate_sections(Path("story.yaml"), manifest(), story)))

    def test_spoken_beat_can_use_cue_without_script(self):
        story = section_story()
        story["project"]["talkability_version"] = 3
        slide = story["slides"][0]
        beat = slide["talk_track"]["beats"][0]
        beat.update(delivery="spoken", spoken_text="役割を分ける")
        slide["speaker_cue"] = {"mode": "cue", "cues": ["役割を分ける"]}
        slide["spoken_note"] = render_note(slide)
        self.assertEqual([], validate_sections(Path("story.yaml"), manifest(), story))
        beat["spoken_text"] = "ノートにない説明"
        self.assertTrue(validate_sections(Path("story.yaml"), manifest(), story))

    def test_v2_behavior_is_preserved(self):
        story = good_story()
        self.assertEqual([], validate_story(Path("story.yaml"), story))
        slide = story["slides"][3]
        slide["speaker_cue"]["script"] = "短い旧台本"
        slide["spoken_note"] = slide["spoken_note"].replace(slide["spoken_note"].splitlines()[1], "話す内容: 短い旧台本")
        self.assertTrue(any("too short" in err for err in validate_story(Path("story.yaml"), story)))


if __name__ == "__main__":
    unittest.main()
