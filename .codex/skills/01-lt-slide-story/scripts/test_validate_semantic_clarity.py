from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from validate_semantic_clarity import validate_blueprint, validate_html, validate_story


def claim(
    surface: str,
    value: str,
    subject: str,
    actor: str,
    target: str,
    predicate: str,
    *,
    kind: str = "action",
    actor_kind: str = "ai",
    not_applicable: list[str] | None = None,
) -> dict:
    return {
        "surface": surface,
        "surface_text": value,
        "clause": value,
        "kind": kind,
        "subject": subject,
        "actor": actor,
        "actor_kind": actor_kind,
        "target": target,
        "predicate": predicate,
        "not_applicable": not_applicable or [],
    }


def good_story() -> dict:
    title = "Copilotが設定ファイルを確認する"
    message = "保守担当者が完了条件を先に決める"
    body = "Copilotが変更前後の値を比較する"
    return {
        "project": {"semantic_clarity_version": 1},
        "slides": [
            {"id": "cover", "role": "cover", "title": "表紙", "message": "副題"},
            {
                "id": "s02",
                "role": "action",
                "title": title,
                "message": message,
                "support": [body],
                "semantic_clarity": {
                    "status": "required",
                    "claims": [
                        claim("title", title, "Copilot", "Copilot", "設定ファイル", "確認する"),
                        claim("message", message, "保守担当者", "保守担当者", "完了条件", "決める", actor_kind="human"),
                        claim("body", body, "Copilot", "Copilot", "変更前後の値", "比較する"),
                    ],
                    "labels": [],
                },
            },
            {"id": "thanks", "role": "thanks", "title": "Thank you", "message": "終了"},
        ],
    }


class SemanticClarityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.story_path = Path("story.yaml")

    def test_good_story_passes(self) -> None:
        self.assertEqual([], validate_story(self.story_path, good_story()))

    def test_missing_version_fails(self) -> None:
        story = good_story()
        story["project"].pop("semantic_clarity_version")
        errors = validate_story(self.story_path, story)
        self.assertTrue(any("semantic_clarity_version" in error for error in errors))

    def test_implicit_subject_fails(self) -> None:
        story = good_story()
        slide = story["slides"][1]
        value = "最初に設定ファイルを確認する"
        slide["title"] = value
        slide["semantic_clarity"]["claims"][0].update({
            "surface_text": value,
            "clause": value,
            "subject": "Copilot",
        })
        errors = validate_story(self.story_path, story)
        self.assertTrue(any("subject must appear" in error for error in errors))

    def test_actor_cannot_be_supplied_only_in_metadata(self) -> None:
        story = good_story()
        slide = story["slides"][1]
        value = "大規模リポジトリは文脈を選別する"
        slide["title"] = value
        slide["semantic_clarity"]["claims"][0].update({
            "surface_text": value,
            "clause": value,
            "subject": "大規模リポジトリ",
            "actor": "Copilot",
            "target": "文脈",
            "predicate": "選別する",
        })
        errors = validate_story(self.story_path, story)
        self.assertTrue(any("actor must appear" in error for error in errors))

    def test_change_target_is_required(self) -> None:
        story = good_story()
        story["slides"][1]["semantic_clarity"]["claims"][0]["target"] = ""
        errors = validate_story(self.story_path, story)
        self.assertTrue(any("target is required" in error for error in errors))

    def test_definition_can_mark_actor_and_target_not_applicable(self) -> None:
        story = good_story()
        slide = story["slides"][1]
        title = "ハーネスはAIの変更経路を支える開発環境である"
        slide["title"] = title
        slide["semantic_clarity"]["claims"][0] = claim(
            "title",
            title,
            "ハーネス",
            "",
            "",
            "開発環境である",
            kind="definition",
            actor_kind="not-applicable",
            not_applicable=["actor", "target"],
        )
        self.assertEqual([], validate_story(self.story_path, story))

    def test_message_cannot_be_hidden_as_a_label(self) -> None:
        story = good_story()
        slide = story["slides"][1]
        slide["semantic_clarity"]["claims"] = [slide["semantic_clarity"]["claims"][0], slide["semantic_clarity"]["claims"][2]]
        slide["semantic_clarity"]["labels"] = [{
            "surface": "message",
            "surface_text": slide["message"],
            "reason": "中心メッセージではなく見出しだから",
        }]
        errors = validate_story(self.story_path, story)
        self.assertTrue(any("message is always a claim" in error for error in errors))
        self.assertTrue(any("message is not accounted" in error for error in errors))

    def test_action_like_body_text_must_be_accounted(self) -> None:
        story = good_story()
        story["slides"][1]["semantic_clarity"]["claims"].pop()
        errors = validate_story(self.story_path, story)
        self.assertTrue(any("action-like body text" in error for error in errors))

    def test_action_like_body_with_citation_must_be_accounted(self) -> None:
        story = good_story()
        slide = story["slides"][1]
        slide["support"][0] = "Copilotが変更前後の値を比較する [1]"
        slide["semantic_clarity"]["claims"].pop()
        errors = validate_story(self.story_path, story)
        self.assertTrue(any("action-like body text" in error for error in errors))

    def test_section_faithful_source_heading_can_remain_a_title_label(self) -> None:
        story = good_story()
        slide = story["slides"][1]
        title = "再現可能な開発・検証環境を用意する"
        slide["title"] = title
        slide["source_section_ids"] = ["article-section-008"]
        slide["semantic_clarity"]["claims"] = slide["semantic_clarity"]["claims"][1:]
        slide["semantic_clarity"]["labels"] = [{
            "surface": "title",
            "surface_text": title,
            "source_heading": True,
            "reason": "原稿の見出しをsection-faithful契約でそのまま保持するため",
        }]
        self.assertEqual([], validate_story(self.story_path, story))

        slide.pop("source_section_ids")
        errors = validate_story(self.story_path, story)
        self.assertTrue(any("source_heading is only valid" in error for error in errors))

    def test_blueprint_and_html_must_preserve_clarity_text(self) -> None:
        story = good_story()
        slide = story["slides"][1]
        blueprint = {
            "slides": [{
                "id": "s02",
                "title": slide["title"],
                "message": slide["message"],
                "text": {"details": slide["support"]},
            }]
        }
        self.assertEqual([], validate_blueprint(Path("blueprint.yaml"), blueprint, story))
        html = (
            '<section class="slide" data-slide-id="s02">'
            f'<h1>{slide["title"]}</h1><p>{slide["message"]}</p><p>{slide["support"][0]}</p>'
            "</section>"
        )
        self.assertEqual([], validate_html(Path("index.html"), html, story))

        broken = deepcopy(blueprint)
        broken["slides"][0]["message"] = "完了条件を先に決める"
        errors = validate_blueprint(Path("blueprint.yaml"), broken, story)
        self.assertTrue(any("clarity text is missing" in error for error in errors))

        errors = validate_html(Path("index.html"), html.replace(slide["message"], "完了条件を先に決める"), story)
        self.assertTrue(any("clarity text is missing" in error for error in errors))

    def test_blueprint_does_not_treat_unknown_content_model_key_as_visible(self) -> None:
        story = good_story()
        slide = story["slides"][1]
        body = slide["support"][0]
        blueprint = {
            "slides": [{
                "id": "s02",
                "title": slide["title"],
                "message": slide["message"],
                "text": {},
                "content_model": {"semantic_support": [body]},
            }]
        }
        errors = validate_blueprint(Path("blueprint.yaml"), blueprint, story)
        self.assertTrue(any("clarity text is missing" in error for error in errors))

        blueprint["slides"][0]["content_model"] = {"data": {"label": body}}
        self.assertEqual([], validate_blueprint(Path("blueprint.yaml"), blueprint, story))

    def test_roadmap_provenance_titles_are_not_treated_as_visible_copy(self) -> None:
        story = good_story()
        slide = story["slides"][1]
        slide["support"] = []
        slide["semantic_clarity"]["claims"] = slide["semantic_clarity"]["claims"][:2]
        slide["content_model"] = {
            "type": "flow",
            "variant": "roadmap",
            "data": {
                "steps": [{
                    "label": "環境",
                    "summary": "再現可能な検証基盤",
                    "page_start": 8,
                    "page_end": 13,
                    "start_title": "再現可能な開発・検証環境を用意する",
                    "end_title": "権限・安全性・レビューを設計する",
                    "source_section_ids": ["article-section-008"],
                }],
                "input": "既存システム",
                "output": "安全な変更経路",
            },
        }
        self.assertEqual([], validate_story(self.story_path, story))


if __name__ == "__main__":
    unittest.main()
