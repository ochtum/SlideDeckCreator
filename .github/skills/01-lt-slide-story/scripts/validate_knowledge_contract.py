#!/usr/bin/env python3
"""Validate semantic knowledge, dual-use publication, and visible citation contracts."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
from typing import Any

import yaml


KNOWLEDGE_TYPES = {
    "claim", "definition", "evidence", "causal", "comparison",
    "procedure", "example", "caution", "decision", "reference",
}
DOCUMENT_TYPES = {
    "concept", "tutorial", "hands-on", "comparison", "design", "troubleshooting",
    "case-study", "retrospective", "research", "experiment", "opinion", "proposal",
}
IMPORTANCE = {"essential", "supporting", "reference"}
CHECK_KINDS = {"explain", "distinguish", "choose", "apply", "qualify"}
DELIVERY_SCOPES = {"live", "appendix", "reference"}
FACT_STATUSES = {"source-stated", "verified", "updated", "unverified"}
NON_BODY_ROLES = {"cover", "profile", "thanks"}


def text(value: Any) -> str:
    return str(value or "").strip()


def compact(value: Any) -> str:
    return re.sub(r"\s+", "", text(value)).casefold()


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text(item) for item in value if text(item)]


def enabled(story: dict) -> bool:
    return int((story.get("project") or {}).get("knowledge_contract_version") or 0) >= 1


def delivery_scope(slide: dict) -> str:
    return text(slide.get("delivery_scope") or "live")


def visible_plan_strings(slide: dict) -> list[str]:
    result: list[str] = []
    for key in ("title", "message", "support", "information_layers"):
        result.extend(flatten_strings(slide.get(key)))
    return result


def flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in flatten_strings(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in flatten_strings(child)]
    return []


def id_map(items: Any, label: str, path: Path, errors: list[str]) -> dict[str, dict]:
    if not isinstance(items, list):
        errors.append(f"{path}: {label} must be a list")
        return {}
    result: dict[str, dict] = {}
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            errors.append(f"{path}: {label}[{index}] must be a mapping")
            continue
        item_id = text(item.get("id"))
        if not item_id:
            errors.append(f"{path}: {label}[{index}].id is required")
        elif item_id in result:
            errors.append(f"{path}: duplicated {label} id: {item_id}")
        else:
            result[item_id] = item
    return result


def validate_story(path: Path, story: dict) -> list[str]:
    if not enabled(story):
        return []
    errors: list[str] = []
    project = story.get("project") or {}
    dual_use = text(project.get("delivery_profile")) == "dual-use"
    source = story.get("source") or {}
    narrative = story.get("narrative") or {}
    request = story.get("request")

    if not isinstance(request, dict):
        errors.append(f"{path}: request must record must_keep, out_of_scope, fact_check_policy, and assumptions")
    else:
        for key in ("must_keep", "out_of_scope", "fact_check_policy", "assumptions"):
            if key not in request:
                errors.append(f"{path}: request.{key} is required")
        if not isinstance(request.get("must_keep"), list) or not isinstance(request.get("out_of_scope"), list):
            errors.append(f"{path}: request.must_keep and request.out_of_scope must be lists")
        if text(request.get("fact_check_policy")) not in {"primary-sources", "source-only", "none"}:
            errors.append(f"{path}: request.fact_check_policy is invalid")
        if not isinstance(request.get("assumptions"), list):
            errors.append(f"{path}: request.assumptions must be a list")
        else:
            for index, assumption in enumerate(request.get("assumptions") or [], 1):
                if not isinstance(assumption, dict) or any(not text(assumption.get(key)) for key in ("field", "value", "reason")):
                    errors.append(f"{path}: request.assumptions[{index}] requires field, value, and reason")
    document_types = string_list(source.get("document_types"))
    if not document_types:
        errors.append(f"{path}: source.document_types must not be empty")
    for document_type in document_types:
        if document_type not in DOCUMENT_TYPES:
            errors.append(f"{path}: source.document_types contains unknown type '{document_type}'")
    if not text(narrative.get("archetype")):
        errors.append(f"{path}: narrative.archetype is required")
    phase_order = string_list(narrative.get("phase_order"))
    if not phase_order or len(set(phase_order)) != len(phase_order):
        errors.append(f"{path}: narrative.phase_order must contain unique phases")
    actual_phases = [text(item.get("phase")) for item in narrative.get("question_spine") or [] if isinstance(item, dict)]
    if phase_order and actual_phases != phase_order:
        errors.append(f"{path}: question_spine order must match narrative.phase_order")

    slides = id_map(story.get("slides"), "slides", path, errors)
    units = id_map(story.get("knowledge_units"), "knowledge_units", path, errors)
    checks = id_map(story.get("comprehension_checks"), "comprehension_checks", path, errors)
    citations = id_map(story.get("citations") or [], "citations", path, errors)

    reached_reader_only = False
    for sid, slide in slides.items():
        scope = delivery_scope(slide)
        if scope not in DELIVERY_SCOPES:
            errors.append(f"{path}:{sid}: delivery_scope must be one of {sorted(DELIVERY_SCOPES)}")
        if scope != "live" and text(slide.get("flow_phase")):
            errors.append(f"{path}:{sid}: appendix/reference slide must not consume a live flow_phase")
        if scope in {"appendix", "reference"}:
            reached_reader_only = True
        elif reached_reader_only:
            errors.append(f"{path}:{sid}: live slide must not appear after appendix/reference slides")

    live_body = sum(
        delivery_scope(slide) == "live" and text(slide.get("role")) not in NON_BODY_ROLES
        for slide in slides.values()
    )
    target = project.get("target_slide_count")
    if isinstance(target, int) and live_body != target:
        errors.append(f"{path}: live body slides={live_body}, target_slide_count={target}")
    appendix_count = sum(delivery_scope(slide) in {"appendix", "reference"} for slide in slides.values())
    declared_appendix = project.get("appendix_slide_count")
    if isinstance(declared_appendix, int) and appendix_count != declared_appendix:
        errors.append(f"{path}: appendix/reference slides={appendix_count}, appendix_slide_count={declared_appendix}")

    citation_labels = {cid: text(item.get("label")) for cid, item in citations.items()}
    for cid, item in citations.items():
        for key in ("label", "title", "url", "checked_at"):
            if not text(item.get(key)):
                errors.append(f"{path}:{cid}: citation.{key} is required")

    for sid, slide in slides.items():
        for uid in string_list(slide.get("knowledge_unit_ids")):
            if uid not in units:
                errors.append(f"{path}:{sid}: unknown knowledge_unit_id {uid}")
            elif sid not in string_list(units[uid].get("slide_ids")):
                errors.append(f"{path}:{sid}: knowledge unit {uid} must include the slide_id")
        for check_id in string_list(slide.get("comprehension_check_ids")):
            if check_id not in checks:
                errors.append(f"{path}:{sid}: unknown comprehension_check_id {check_id}")
            elif sid not in string_list(checks[check_id].get("slide_ids")):
                errors.append(f"{path}:{sid}: comprehension check {check_id} must include the slide_id")

    for uid, unit in units.items():
        unit_type = text(unit.get("type"))
        if unit_type not in KNOWLEDGE_TYPES:
            errors.append(f"{path}:{uid}: unknown knowledge type '{unit_type}'")
        importance = text(unit.get("importance"))
        if importance not in IMPORTANCE:
            errors.append(f"{path}:{uid}: importance must be one of {sorted(IMPORTANCE)}")
        if len(compact(unit.get("statement"))) < 4:
            errors.append(f"{path}:{uid}: statement must be concrete")
        if not string_list(unit.get("source_unit_ids")):
            errors.append(f"{path}:{uid}: source_unit_ids must not be empty")
        mapped = string_list(unit.get("slide_ids"))
        if not mapped:
            errors.append(f"{path}:{uid}: slide_ids must not be empty")
        mapped_slides = [slides[sid] for sid in mapped if sid in slides]
        for sid in mapped:
            if sid not in slides:
                errors.append(f"{path}:{uid}: unknown slide_id {sid}")
            elif uid not in string_list(slides[sid].get("knowledge_unit_ids")):
                errors.append(f"{path}:{uid}: slide {sid} must include the knowledge_unit_id")
        for prerequisite in string_list(unit.get("prerequisites")):
            if prerequisite not in units:
                errors.append(f"{path}:{uid}: unknown prerequisite {prerequisite}")
        for cid in string_list(unit.get("citation_ids")):
            if cid not in citations:
                errors.append(f"{path}:{uid}: unknown citation_id {cid}")
        if importance == "essential":
            useful = [
                slide for slide in mapped_slides
                if delivery_scope(slide) in {"live", "appendix"}
                and text(slide.get("role")) not in NON_BODY_ROLES
            ]
            if not useful:
                errors.append(f"{path}:{uid}: essential knowledge requires a visible live or appendix slide")

    require_checks = dual_use or text(project.get("content_fidelity")) == "full-equivalence"
    if require_checks and not 5 <= len(checks) <= 10:
        errors.append(f"{path}: dual-use/full-equivalence requires 5 to 10 comprehension_checks")
    for check_id, check in checks.items():
        if text(check.get("kind")) not in CHECK_KINDS:
            errors.append(f"{path}:{check_id}: unknown comprehension kind")
        if len(compact(check.get("prompt"))) < 8:
            errors.append(f"{path}:{check_id}: prompt must be a concrete question")
        check_units = string_list(check.get("knowledge_unit_ids"))
        check_slides = string_list(check.get("slide_ids"))
        if not check_units or not check_slides:
            errors.append(f"{path}:{check_id}: knowledge_unit_ids and slide_ids are required")
        for uid in check_units:
            if uid not in units:
                errors.append(f"{path}:{check_id}: unknown knowledge_unit_id {uid}")
        for sid in check_slides:
            if sid not in slides:
                errors.append(f"{path}:{check_id}: unknown slide_id {sid}")
            elif check_id not in string_list(slides[sid].get("comprehension_check_ids")):
                errors.append(f"{path}:{check_id}: slide {sid} must include the comprehension_check_id")
        if check_units and check_slides:
            mapped_units = {
                uid
                for sid in check_slides
                if sid in slides
                for uid in string_list(slides[sid].get("knowledge_unit_ids"))
            }
            if not set(check_units).issubset(mapped_units):
                errors.append(f"{path}:{check_id}: mapped slides do not visibly carry all checked knowledge units")

    used_citations: set[str] = set()
    for sid, slide in slides.items():
        visible = compact(" ".join(visible_plan_strings(slide)))
        for cid in string_list(slide.get("citation_ids")):
            used_citations.add(cid)
            if cid not in citations:
                errors.append(f"{path}:{sid}: unknown citation_id {cid}")
                continue
            label = citation_labels.get(cid, "")
            if dual_use and label and compact(label) not in visible:
                errors.append(f"{path}:{sid}: citation {cid} label {label} is not in the visible information plan")

    ledger = story.get("fact_ledger")
    if used_citations and not isinstance(ledger, list):
        errors.append(f"{path}: fact_ledger is required when citations are used")
        ledger = []
    for index, item in enumerate(ledger or [], 1):
        if not isinstance(item, dict):
            errors.append(f"{path}: fact_ledger[{index}] must be a mapping")
            continue
        uid = text(item.get("knowledge_unit_id"))
        if uid not in units:
            errors.append(f"{path}: fact_ledger[{index}] references unknown knowledge unit {uid}")
        if text(item.get("status")) not in FACT_STATUSES:
            errors.append(f"{path}: fact_ledger[{index}] has an invalid status")
        for cid in string_list(item.get("citation_ids")):
            if cid not in citations:
                errors.append(f"{path}: fact_ledger[{index}] references unknown citation {cid}")
    return errors


def validate_blueprint(path: Path, blueprint: dict, story: dict) -> list[str]:
    if not enabled(story):
        return []
    errors: list[str] = []
    story_slides = {text(slide.get("id")): slide for slide in story.get("slides") or []}
    blueprint_slides = {text(slide.get("id")): slide for slide in blueprint.get("slides") or []}
    citations = {text(item.get("id")): item for item in story.get("citations") or []}
    keys = ("delivery_scope", "knowledge_unit_ids", "comprehension_check_ids", "citation_ids")
    for sid, source in story_slides.items():
        slide = blueprint_slides.get(sid)
        if slide is None:
            errors.append(f"{path}:{sid}: Blueprint slide is missing")
            continue
        for key in keys:
            expected = source.get(key)
            if key == "delivery_scope" and expected is None:
                expected = "live"
            actual = slide.get(key)
            if key == "delivery_scope" and actual is None:
                actual = "live"
            if actual != expected:
                errors.append(f"{path}:{sid}: {key} must be copied unchanged from Story")
        visible = compact(" ".join(flatten_strings({
            "title": slide.get("title"),
            "message": slide.get("message"),
            "text": slide.get("text") or {},
            "content_model": slide.get("content_model") or {},
            "annotations": (slide.get("visual") or {}).get("annotations") or [],
        })))
        for cid in string_list(source.get("citation_ids")):
            label = text((citations.get(cid) or {}).get("label"))
            if label and compact(label) not in visible:
                errors.append(f"{path}:{sid}: visible citation label {label} is missing from Blueprint")
    return errors


class SlideParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.slides: dict[str, dict[str, Any]] = {}
        self.current: dict[str, Any] | None = None
        self.depth = 0
        self.skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "section" and "slide" in values.get("class", "").split() and self.current is None:
            self.current = {"attrs": values, "text": []}
            self.depth = 1
            return
        if self.current is not None:
            if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
                self.depth += 1
            if tag in {"script", "style"}:
                self.skip += 1

    def handle_endtag(self, tag: str) -> None:
        if self.current is None:
            return
        if tag in {"script", "style"} and self.skip:
            self.skip -= 1
        self.depth -= 1
        if self.depth == 0:
            sid = self.current["attrs"].get("data-slide-id")
            if sid:
                self.slides[sid] = self.current
            self.current = None

    def handle_data(self, data: str) -> None:
        if self.current is not None and not self.skip and data.strip():
            self.current["text"].append(data.strip())


def validate_html(path: Path, html: str, story: dict) -> list[str]:
    if not enabled(story):
        return []
    errors: list[str] = []
    parser = SlideParser()
    parser.feed(html)
    citations = {text(item.get("id")): item for item in story.get("citations") or []}
    attr_keys = {
        "knowledge_unit_ids": "data-knowledge-unit-ids",
        "comprehension_check_ids": "data-comprehension-check-ids",
        "citation_ids": "data-citation-ids",
    }
    for source in story.get("slides") or []:
        sid = text(source.get("id"))
        rendered = parser.slides.get(sid)
        if rendered is None:
            errors.append(f"{path}:{sid}: HTML slide is missing")
            continue
        attrs = rendered["attrs"]
        expected_scope = delivery_scope(source)
        if attrs.get("data-delivery-scope", "live") != expected_scope:
            errors.append(f"{path}:{sid}: data-delivery-scope does not match Story")
        for source_key, attr_key in attr_keys.items():
            expected = set(string_list(source.get(source_key)))
            actual = {item for item in re.split(r"[\s,]+", attrs.get(attr_key, "")) if item}
            if expected != actual:
                errors.append(f"{path}:{sid}: {attr_key} does not match Story")
        visible = compact(" ".join(rendered["text"]))
        for cid in string_list(source.get("citation_ids")):
            label = text((citations.get(cid) or {}).get("label"))
            if label and compact(label) not in visible:
                errors.append(f"{path}:{sid}: visible citation label {label} is missing from HTML")
    return errors


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_stories(path: Path) -> tuple[list[str], list[tuple[Path, dict]]]:
    story = load(path)
    if story.get("kind") != "lt-slide-series":
        return [], [(path, story)]
    errors: list[str] = []
    stories: list[tuple[Path, dict]] = []
    for part in story.get("parts") or []:
        child = (path.parent / text(part.get("story_file"))).resolve()
        if not child.is_file():
            errors.append(f"{path}: part story is missing: {child}")
            continue
        child_errors, child_stories = load_stories(child)
        errors.extend(child_errors)
        stories.extend(child_stories)
    return errors, stories


def main() -> int:
    parser = argparse.ArgumentParser(description="知識単位・理解確認・登壇兼閲覧・可視出典を検証する")
    parser.add_argument("--story", required=True, type=Path)
    parser.add_argument("--blueprint", type=Path)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()

    errors, stories = load_stories(args.story.resolve())
    for story_path, story in stories:
        errors.extend(validate_story(story_path, story))
    if (args.blueprint or args.html) and len(stories) != 1:
        errors.append("--blueprint and --html require a single part Story")
    elif stories:
        _, story = stories[0]
        if args.blueprint:
            errors.extend(validate_blueprint(args.blueprint.resolve(), load(args.blueprint.resolve()), story))
        if args.html:
            errors.extend(validate_html(args.html.resolve(), args.html.read_text(encoding="utf-8"), story))
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print(f"OK: {len(stories)}件の知識・理解確認・公開契約を検証しました")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
