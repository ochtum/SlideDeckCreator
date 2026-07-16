#!/usr/bin/env python3
"""Validate time coverage and explanation depth for long-form LT artifacts."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import yaml

NON_BODY_ROLES = {"cover", "profile", "thanks"}
LOW_DENSITY_ROLES = {"transition", "statement", "section", "goal"}
ALLOWED_MODES = {"explain", "demo", "interaction", "transition", "recap"}
GENERIC_CHECK_ITEMS = {
    "対象を確認する",
    "証拠を残す",
    "完了条件を確認する",
    "影響を確認する",
    "次の判断を確認する",
}
TIME_KEYS = ("content_seconds", "demo_seconds", "interaction_seconds", "buffer_seconds")


def compact(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).casefold()


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def is_long_form(story: dict) -> bool:
    return int((story.get("project") or {}).get("duration_minutes", 0)) >= 20


def substantive(slide: dict) -> bool:
    role = str(slide.get("role", ""))
    delivery = slide.get("delivery") or {}
    return role not in NON_BODY_ROLES | LOW_DENSITY_ROLES and delivery.get("mode") != "transition"


def validate_time_budget(path: Path, story: dict, errors: list[str]) -> None:
    project = story.get("project") or {}
    duration = int(project.get("duration_minutes", 0))
    if duration < 20:
        return
    budget = project.get("time_budget")
    if not isinstance(budget, dict):
        errors.append(f"{path}: 20+ minute deck requires project.time_budget")
        return
    missing = [key for key in TIME_KEYS if not isinstance(budget.get(key), int)]
    if missing:
        errors.append(f"{path}: time_budget missing integer fields: {', '.join(missing)}")
        return
    expected = duration * 60
    actual = sum(int(budget[key]) for key in TIME_KEYS)
    if actual != expected:
        errors.append(f"{path}: time_budget total={actual}s, expected {expected}s")


def validate_story(path: Path, story: dict) -> list[str]:
    errors: list[str] = []
    if not is_long_form(story):
        return errors

    validate_time_budget(path, story, errors)
    slides = story.get("slides") or []
    timed_total = 0
    transition_ids: list[str] = []
    substantive_count = 0
    previous_transition = False
    point_signatures: dict[str, list[str]] = defaultdict(list)

    for slide in slides:
        sid = str(slide.get("id", "<missing-id>"))
        role = str(slide.get("role", ""))
        if role in NON_BODY_ROLES:
            continue
        delivery = slide.get("delivery")
        if not isinstance(delivery, dict):
            errors.append(f"{path}:{sid}: long-form body slide requires delivery")
            previous_transition = False
            continue

        mode = delivery.get("mode")
        if mode not in ALLOWED_MODES:
            errors.append(f"{path}:{sid}: delivery.mode must be one of {sorted(ALLOWED_MODES)}")
        seconds = delivery.get("estimated_seconds")
        if not isinstance(seconds, int) or seconds <= 0:
            errors.append(f"{path}:{sid}: delivery.estimated_seconds must be a positive integer")
        else:
            timed_total += seconds
            if mode == "transition" and seconds > 45:
                errors.append(f"{path}:{sid}: transition should not consume more than 45 seconds")
            maximum = 300 if mode in {"demo", "interaction"} else 180
            if seconds > maximum:
                errors.append(f"{path}:{sid}: {mode} slide exceeds {maximum} seconds; split the explanation")

        points = string_list(delivery.get("talking_points"))
        anchors = string_list(delivery.get("visible_anchors"))
        minimum = 1 if mode == "transition" or role in LOW_DENSITY_ROLES else 2
        if len(points) < minimum:
            errors.append(f"{path}:{sid}: requires at least {minimum} concrete talking_points")
        if len(anchors) < minimum:
            errors.append(f"{path}:{sid}: requires at least {minimum} visible_anchors")

        title_and_message = {compact(slide.get("title")), compact(slide.get("message"))}
        repeated = [anchor for anchor in anchors if compact(anchor) in title_and_message]
        if repeated and len(anchors) <= minimum:
            errors.append(f"{path}:{sid}: visible_anchors only repeat title/message: {repeated}")

        if points:
            signature = "|".join(sorted(compact(point) for point in points))
            point_signatures[signature].append(sid)

        current_transition = mode == "transition"
        if current_transition:
            transition_ids.append(sid)
            if previous_transition:
                errors.append(f"{path}:{sid}: consecutive transition slides are not allowed")
        previous_transition = current_transition

        if substantive(slide):
            substantive_count += 1
            visible_dimensions = 0
            if anchors:
                visible_dimensions += 1
            if slide.get("evidence_artifact_ids"):
                visible_dimensions += 1
            if slide.get("decision") or slide.get("done_condition"):
                visible_dimensions += 1
            if visible_dimensions < 1:
                errors.append(f"{path}:{sid}: substantive slide lacks a visible explanation anchor")

    body_count = sum(slide.get("role") not in NON_BODY_ROLES for slide in slides)
    if body_count and len(transition_ids) / body_count > 0.15:
        errors.append(
            f"{path}: transition slides={len(transition_ids)} exceed 15% of {body_count} body slides"
        )
    if body_count and substantive_count / body_count < 0.70:
        errors.append(
            f"{path}: substantive slides={substantive_count} are below 70% of {body_count} body slides"
        )

    budget = (story.get("project") or {}).get("time_budget") or {}
    if all(isinstance(budget.get(key), int) for key in TIME_KEYS):
        expected_timed = sum(int(budget[key]) for key in TIME_KEYS[:-1])
        if timed_total != expected_timed:
            errors.append(f"{path}: slide delivery total={timed_total}s, expected {expected_timed}s excluding buffer")

    for ids in point_signatures.values():
        if len(ids) > 1:
            errors.append(f"{path}: duplicated talking_points across slides: {', '.join(ids)}")
    return errors


def content_items(data: dict) -> list[Any]:
    for key in ("rows", "steps", "nodes", "layers", "items", "entries"):
        value = data.get(key)
        if isinstance(value, list):
            return value
    return []


def validate_content_model(path: Path, slide: dict, errors: list[str]) -> None:
    sid = str(slide.get("id", "<missing-id>"))
    model = slide.get("content_model")
    if not isinstance(model, dict):
        return
    kind = model.get("type")
    data = model.get("data")
    if not kind or not isinstance(data, dict) or not data:
        errors.append(f"{path}:{sid}: content_model requires non-empty type and data")
        return

    sources = model.get("source_artifacts")
    if substantive(slide) and not string_list(sources):
        errors.append(f"{path}:{sid}: substantive content_model requires source_artifacts")

    items = content_items(data)
    if kind == "table":
        columns = data.get("columns") or []
        rows = data.get("rows") or []
        if len(columns) < 2 or len(rows) < 2:
            errors.append(f"{path}:{sid}: table requires at least 2 columns and 2 representative rows")
    elif kind == "flow":
        if len(items) < 3:
            errors.append(f"{path}:{sid}: flow requires at least 3 nodes/layers/steps")
        if not any(key in data for key in ("edges", "input", "output", "decision", "done_when")):
            errors.append(f"{path}:{sid}: flow requires an input/output, edge, or decision gate")
    elif kind == "checklist":
        if len(items) < 3:
            errors.append(f"{path}:{sid}: checklist requires at least 3 actionable items")
        normalized = {compact(item) for item in items if isinstance(item, str)}
        generic_hits = {compact(item) for item in GENERIC_CHECK_ITEMS} & normalized
        if len(generic_hits) >= 2:
            errors.append(f"{path}:{sid}: checklist is generic and not specific to the slide")
    elif kind == "comparison":
        if not ((data.get("left") and data.get("right")) or len(items) >= 2):
            errors.append(f"{path}:{sid}: comparison requires two targets on shared criteria")
    elif kind in {"code", "config"}:
        code = str(data.get("code") or data.get("snippet") or "")
        if len([line for line in code.splitlines() if line.strip()]) < 2:
            errors.append(f"{path}:{sid}: {kind} requires a readable multi-line snippet")
        if not (data.get("filename") or data.get("location") or data.get("language")):
            errors.append(f"{path}:{sid}: {kind} requires filename/location/language context")
    elif kind == "implementation-playbook":
        steps = data.get("steps") or []
        if len(steps) < 3:
            errors.append(f"{path}:{sid}: implementation-playbook requires at least 3 steps")
        for index, step in enumerate(steps, 1):
            if not isinstance(step, dict) or not all(step.get(key) for key in ("artifact", "owner", "done_when")):
                errors.append(f"{path}:{sid}: playbook step {index} requires artifact, owner, done_when")
    elif kind == "file-map" and len(items) < 3:
        errors.append(f"{path}:{sid}: file-map requires at least 3 concrete entries")


def validate_blueprint(path: Path, blueprint: dict, story: dict) -> list[str]:
    errors: list[str] = []
    if not is_long_form(story):
        return errors
    story_by_id = {slide.get("id"): slide for slide in story.get("slides") or []}
    reused: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for slide in blueprint.get("slides") or []:
        sid = str(slide.get("id", "<missing-id>"))
        expected = story_by_id.get(slide.get("id")) or {}
        if expected.get("role") not in NON_BODY_ROLES:
            if slide.get("delivery") != expected.get("delivery"):
                errors.append(f"{path}:{sid}: delivery must be copied unchanged from story")
        validate_content_model(path, slide, errors)

        model = slide.get("content_model")
        if isinstance(model, dict) and isinstance(model.get("data"), dict):
            digest = json.dumps(
                {"type": model.get("type"), "data": model.get("data")},
                ensure_ascii=False,
                sort_keys=True,
            )
            reused[digest].append((sid, str(model.get("focus") or "")))

        if substantive(expected):
            text = slide.get("text") or {}
            details = string_list(text.get("details")) + string_list(text.get("bullets"))
            annotations = string_list((slide.get("visual") or {}).get("annotations"))
            if not slide.get("content_model") and len(details) + len(annotations) < 2:
                errors.append(f"{path}:{sid}: long-form substantive slide lacks projected explanation detail")

    for instances in reused.values():
        if len(instances) <= 1:
            continue
        ids = [sid for sid, _ in instances]
        focuses = [focus for _, focus in instances]
        if any(not focus for focus in focuses) or len(set(focuses)) != len(focuses):
            errors.append(
                f"{path}: identical content_model reused without unique focus/highlight: {', '.join(ids)}"
            )
    return errors


class SlideHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.slides: list[dict[str, Any]] = []
        self.current: dict[str, Any] | None = None
        self.depth = 0
        self.skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        classes = set(attributes.get("class", "").split())
        if tag == "section" and "slide" in classes and self.current is None:
            self.current = {"attrs": attributes, "text": []}
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
            self.slides.append(self.current)
            self.current = None

    def handle_data(self, data: str) -> None:
        if self.current is not None and not self.skip and data.strip():
            self.current["text"].append(data.strip())


def validate_html(path: Path, html: str, story: dict, blueprint: dict | None) -> list[str]:
    errors: list[str] = []
    if not is_long_form(story):
        return errors
    parser = SlideHTMLParser()
    parser.feed(html)
    story_by_id = {slide.get("id"): slide for slide in story.get("slides") or []}
    html_by_id = {
        slide["attrs"].get("data-slide-id") or slide["attrs"].get("data-id"): slide
        for slide in parser.slides
    }

    for sid, expected in story_by_id.items():
        if expected.get("role") in NON_BODY_ROLES:
            continue
        rendered = html_by_id.get(sid)
        if not rendered:
            errors.append(f"{path}:{sid}: slide not found by data-slide-id/data-id")
            continue
        attrs = rendered["attrs"]
        delivery = expected.get("delivery") or {}
        if delivery:
            if attrs.get("data-estimated-seconds") != str(delivery.get("estimated_seconds", "")):
                errors.append(f"{path}:{sid}: data-estimated-seconds does not match story")
            if attrs.get("data-delivery-mode") != str(delivery.get("mode", "")):
                errors.append(f"{path}:{sid}: data-delivery-mode does not match story")
        visible = compact(" ".join(rendered["text"]))
        missing = [anchor for anchor in string_list(delivery.get("visible_anchors")) if compact(anchor) not in visible]
        if missing:
            errors.append(f"{path}:{sid}: visible anchors missing from HTML: {missing}")

    if blueprint:
        for slide in blueprint.get("slides") or []:
            model = slide.get("content_model")
            if not isinstance(model, dict):
                continue
            sid = slide.get("id")
            rendered = html_by_id.get(sid)
            if not rendered:
                continue
            attrs = rendered["attrs"]
            if attrs.get("data-content-model-type") != str(model.get("type", "")):
                errors.append(f"{path}:{sid}: missing or mismatched data-content-model-type")
            source_ids = string_list(model.get("source_artifacts"))
            rendered_ids = {item for item in re.split(r"[\s,]+", attrs.get("data-evidence-artifact-ids", "")) if item}
            if source_ids and not set(source_ids).issubset(rendered_ids):
                errors.append(f"{path}:{sid}: data-evidence-artifact-ids does not preserve source artifacts")
    return errors


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--story", required=True, type=Path)
    parser.add_argument("--blueprint", type=Path)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()

    root_story = load(args.story)
    if root_story.get("kind") == "lt-slide-series":
        if args.blueprint or args.html:
            print("ERROR: --blueprint/--html require a part story, not a series manifest")
            return 1
        errors: list[str] = []
        for part in root_story.get("parts") or []:
            child_path = args.story.parent / part["story_file"]
            errors.extend(validate_story(child_path, load(child_path)))
    else:
        errors = validate_story(args.story, root_story)
        blueprint = load(args.blueprint) if args.blueprint else None
        if blueprint is not None:
            errors.extend(validate_blueprint(args.blueprint, blueprint, root_story))
        if args.html:
            errors.extend(validate_html(args.html, args.html.read_text(encoding="utf-8"), root_story, blueprint))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("OK: explanation depth and time coverage passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
