from copy import deepcopy
from html import escape
from pathlib import Path
import sys
import unittest

from export_note_revisions import propose
from speaker_notes import render_note


def fixtures():
    slide = {"id": "s01", "speaker_cue": {"mode": "cue", "cues": ["更新するファイルを決める"], "purpose": "更新する場所を説明する", "point_at": ["AGENTS.md"]}}
    slide["spoken_note"] = render_note(slide)
    story = {"project": {"talkability_version": 3}, "slides": [slide]}
    plan = deepcopy(story)
    changed = deepcopy(slide)
    changed["speaker_cue"]["cues"] = ["読む順序と共通ルールに絞る"]
    html = f'<section class="slide" data-slide-id="s01" data-original-spoken-note="{escape(slide["spoken_note"], quote=True)}" data-spoken-note="{escape(render_note(changed), quote=True)}"></section>'
    return story, plan, html


class NoteRevisionTests(unittest.TestCase):
    def test_updates_both_candidates_without_mutating_sources(self):
        story, plan, html = fixtures()
        before = deepcopy(story)
        result, blueprint, ids = propose(story, plan, html)
        self.assertEqual(["s01"], ids)
        self.assertEqual(["読む順序と共通ルールに絞る"], result["slides"][0]["speaker_cue"]["cues"])
        self.assertEqual(result["slides"][0]["spoken_note"], blueprint["slides"][0]["spoken_note"])
        self.assertEqual(before, story)
        self.assertEqual(before, plan)

    def test_concurrent_source_edit_is_rejected(self):
        story, plan, html = fixtures()
        story["slides"][0]["spoken_note"] += "\n要点: 別の編集"
        plan = deepcopy(story)
        with self.assertRaisesRegex(ValueError, "競合"):
            propose(story, plan, html)

    def test_missing_baseline_is_rejected(self):
        story, plan, html = fixtures()
        with self.assertRaisesRegex(ValueError, "競合"):
            propose(story, plan, html.replace("data-original-spoken-note", "data-old-note"))

    def test_duplicate_or_missing_slide_is_rejected(self):
        story, plan, html = fixtures()
        for value in (html + html, ""):
            with self.subTest(html=value), self.assertRaises(ValueError):
                propose(story, plan, value)

    def test_existing_story_blueprint_drift_is_rejected(self):
        story, plan, html = fixtures()
        plan["slides"][0]["speaker_cue"]["purpose"] = "別の目的"
        with self.assertRaisesRegex(ValueError, "既に不一致"):
            propose(story, plan, html)


if __name__ == "__main__":
    unittest.main()
