from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

import validate_knowledge_contract as target


def valid_story() -> dict:
    checks = [
        {
            "id": f"check-{index}",
            "kind": kind,
            "prompt": f"判断条件を使って具体例{index}を説明できるか",
            "knowledge_unit_ids": ["ku-1"],
            "slide_ids": ["s1"],
        }
        for index, kind in enumerate(("explain", "distinguish", "choose", "apply", "qualify"), 1)
    ]
    check_ids = [item["id"] for item in checks]
    return {
        "project": {
            "delivery_profile": "dual-use",
            "content_fidelity": "full-equivalence",
            "knowledge_contract_version": 1,
            "target_slide_count": 2,
            "appendix_slide_count": 1,
        },
        "source": {"document_types": ["comparison"]},
        "request": {
            "must_keep": ["選択の判断基準"],
            "out_of_scope": [],
            "fact_check_policy": "primary-sources",
            "assumptions": [],
        },
        "narrative": {
            "archetype": "criteria-comparison-decision",
            "phase_order": ["comparison"],
            "question_spine": [{"phase": "comparison"}],
        },
        "knowledge_units": [{
            "id": "ku-1",
            "source_unit_ids": ["source-1"],
            "type": "comparison",
            "statement": "二つの選択肢を同じ条件で比較する",
            "importance": "essential",
            "prerequisites": [],
            "citation_ids": ["ref-1"],
            "slide_ids": ["s1", "a1"],
        }],
        "comprehension_checks": checks,
        "citations": [{
            "id": "ref-1",
            "label": "[1]",
            "title": "一次資料",
            "url": "https://example.com/source",
            "checked_at": "2026-07-22",
        }],
        "fact_ledger": [{
            "knowledge_unit_id": "ku-1",
            "status": "verified",
            "citation_ids": ["ref-1"],
        }],
        "slides": [
            {
                "id": "s1",
                "role": "comparison",
                "delivery_scope": "live",
                "flow_phase": "comparison",
                "title": "同じ条件で比べる",
                "message": "判断基準をそろえる",
                "information_layers": {"reader_support": ["一次資料 [1]"]},
                "knowledge_unit_ids": ["ku-1"],
                "comprehension_check_ids": check_ids,
                "citation_ids": ["ref-1"],
            },
            {
                "id": "recap",
                "role": "recap",
                "delivery_scope": "live",
                "flow_phase": "comparison",
                "knowledge_unit_ids": [],
                "comprehension_check_ids": [],
                "citation_ids": [],
            },
            {
                "id": "thanks",
                "role": "thanks",
                "delivery_scope": "live",
                "flow_phase": "",
                "knowledge_unit_ids": [],
                "comprehension_check_ids": [],
                "citation_ids": [],
            },
            {
                "id": "a1",
                "role": "evidence",
                "delivery_scope": "appendix",
                "flow_phase": "",
                "knowledge_unit_ids": ["ku-1"],
                "comprehension_check_ids": [],
                "citation_ids": [],
            },
        ],
    }


def valid_blueprint(story: dict) -> dict:
    slides = []
    for source in story["slides"]:
        slide = {
            key: deepcopy(source.get(key))
            for key in ("id", "delivery_scope", "knowledge_unit_ids", "comprehension_check_ids", "citation_ids")
        }
        slide["title"] = source.get("title", source["id"])
        slide["message"] = source.get("message", "補足")
        if source["id"] == "s1":
            slide["text"] = {"details": ["一次資料 [1]"]}
        slides.append(slide)
    return {"slides": slides}


def valid_html(story: dict) -> str:
    sections = []
    for slide in story["slides"]:
        attrs = {
            "class": "slide",
            "data-slide-id": slide["id"],
            "data-delivery-scope": slide["delivery_scope"],
            "data-knowledge-unit-ids": " ".join(slide["knowledge_unit_ids"]),
            "data-comprehension-check-ids": " ".join(slide["comprehension_check_ids"]),
            "data-citation-ids": " ".join(slide["citation_ids"]),
        }
        attr_text = " ".join(f'{key}="{value}"' for key, value in attrs.items())
        visible = "一次資料 [1]" if slide["id"] == "s1" else slide["id"]
        sections.append(f"<section {attr_text}><p>{visible}</p></section>")
    return "<!doctype html><html><body>" + "".join(sections) + "</body></html>"


class KnowledgeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.path = Path("story.yaml")

    def test_valid_dual_use_contract_passes_all_surfaces(self):
        story = valid_story()
        self.assertEqual([], target.validate_story(self.path, story))
        self.assertEqual([], target.validate_blueprint(Path("blueprint.yaml"), valid_blueprint(story), story))
        self.assertEqual([], target.validate_html(Path("index.html"), valid_html(story), story))

    def test_visible_citation_is_required(self):
        story = valid_story()
        story["slides"][0]["information_layers"] = {"reader_support": ["一次資料"]}
        errors = target.validate_story(self.path, story)
        self.assertTrue(any("not in the visible information plan" in error for error in errors))

    def test_essential_knowledge_cannot_live_only_on_reference_slide(self):
        story = valid_story()
        story["knowledge_units"][0]["slide_ids"] = ["a1"]
        story["slides"][0]["knowledge_unit_ids"] = []
        story["slides"][3]["delivery_scope"] = "reference"
        errors = target.validate_story(self.path, story)
        self.assertTrue(any("essential knowledge requires" in error for error in errors))

    def test_live_slide_after_appendix_fails(self):
        story = valid_story()
        story["slides"].append(story["slides"].pop(1))
        errors = target.validate_story(self.path, story)
        self.assertTrue(any("live slide must not appear after" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
