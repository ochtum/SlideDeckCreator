#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path
from typing import Any

import yaml


GENERIC_LABELS = {"why", "what", "how", "demo", "takeaway"}


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def attrs(source: str) -> dict[str, str]:
    return {
        key.lower(): html.unescape(value)
        for key, _, value in re.findall(r"([\w:-]+)\s*=\s*([\"'])(.*?)\2", source, re.S)
    }


def visible_text(source: str) -> str:
    return normalize(html.unescape(re.sub(r"<[^>]+>", " ", source)))


def validate_yaml_contract(
    data: dict[str, Any], path: Path, *, require_top_level: bool = True
) -> tuple[list[str], dict[str, Any], list[dict[str, Any]]]:
    errors: list[str] = []
    slides = list(data.get("slides") or [])
    duration = int((data.get("project") or {}).get("duration_minutes") or 0)
    body_count = len(
        [item for item in slides if item.get("role") not in {"cover", "profile", "thanks"}]
    )
    required = duration >= 30 or body_count > 20
    roadmap = data.get("roadmap") or {}
    if not roadmap:
        if required and require_top_level:
            errors.append(f"{path}: long-form deck requires a top-level roadmap")
        return errors, {}, slides

    if roadmap.get("source") != "generated-from-slides":
        errors.append(f"{path}: roadmap.source must be generated-from-slides")
    roadmap_id = normalize(roadmap.get("slide_id"))
    slide_ids = [normalize(item.get("id")) for item in slides]
    if roadmap_id not in slide_ids:
        errors.append(f"{path}: roadmap.slide_id {roadmap_id!r} is not in slides")
        return errors, roadmap, slides

    roadmap_index = slide_ids.index(roadmap_id)
    goal_indexes = [index for index, item in enumerate(slides) if item.get("role") == "goal"]
    if goal_indexes and roadmap_index != goal_indexes[0] + 1:
        errors.append(f"{path}: roadmap slide must immediately follow the goal slide")

    items = list(roadmap.get("items") or [])
    if not 2 <= len(items) <= 7:
        errors.append(f"{path}: roadmap.items must contain 2..7 actual story milestones")

    thanks_index = next(
        (index for index, item in enumerate(slides[roadmap_index + 1 :], roadmap_index + 1) if item.get("role") == "thanks"),
        len(slides),
    )
    expected_slides = [
        item
        for item in slides[roadmap_index + 1 : thanks_index]
        if normalize(item.get("flow_phase"))
    ]
    expected_ids = [normalize(item.get("id")) for item in expected_slides]
    flattened_ids: list[str] = []

    for item_index, item in enumerate(items, 1):
        label = normalize(item.get("label"))
        summary = normalize(item.get("summary"))
        member_ids = [normalize(value) for value in item.get("slide_ids") or []]
        phase = normalize(item.get("phase"))
        if not label or label.lower() in GENERIC_LABELS:
            errors.append(
                f"{path}: roadmap item {item_index} needs a concrete milestone label, not {label!r}"
            )
        if not summary:
            errors.append(f"{path}: roadmap item {item_index} is missing summary")
        if not member_ids:
            errors.append(f"{path}: roadmap item {item_index} has no slide_ids")
            continue
        flattened_ids.extend(member_ids)
        if any(member_id not in slide_ids for member_id in member_ids):
            errors.append(f"{path}: roadmap item {item_index} references an unknown slide")
            continue
        positions = [slide_ids.index(member_id) for member_id in member_ids]
        if positions != list(range(positions[0], positions[-1] + 1)):
            errors.append(f"{path}: roadmap item {item_index} slide_ids are not contiguous")
        members = [slides[position] for position in positions]
        if phase and any(normalize(member.get("flow_phase")) != phase for member in members):
            errors.append(f"{path}: roadmap item {item_index} phase does not match its slides")
        expected_start = positions[0] + 1
        expected_end = positions[-1] + 1
        if item.get("page_start") != expected_start or item.get("page_end") != expected_end:
            errors.append(
                f"{path}: roadmap item {item_index} page range must be {expected_start}..{expected_end}"
            )
        if normalize(item.get("start_title")) != normalize(members[0].get("title")):
            errors.append(f"{path}: roadmap item {item_index} start_title is stale")
        if normalize(item.get("end_title")) != normalize(members[-1].get("title")):
            errors.append(f"{path}: roadmap item {item_index} end_title is stale")

    if flattened_ids != expected_ids:
        errors.append(
            f"{path}: roadmap slide_ids do not exactly match the generated story order; "
            f"expected={expected_ids}, actual={flattened_ids}"
        )

    roadmap_slide = slides[roadmap_index]
    steps = list((((roadmap_slide.get("content_model") or {}).get("data") or {}).get("steps") or []))
    if steps != items:
        errors.append(f"{path}: roadmap slide content_model.data.steps must equal roadmap.items")
    return errors, roadmap, slides


def validate_blueprint(
    path: Path, story_roadmap: dict[str, Any]
) -> tuple[list[str], list[dict[str, Any]]]:
    data = load_yaml(path)
    errors: list[str] = []
    if data.get("roadmap") != story_roadmap:
        errors.append(f"{path}: top-level roadmap must be copied unchanged from Story")
    blueprint_errors, _, slides = validate_yaml_contract(data, path)
    errors.extend(blueprint_errors)
    return errors, slides


def validate_html(path: Path, roadmap: dict[str, Any], story_slides: list[dict[str, Any]]) -> list[str]:
    source = path.read_text(encoding="utf-8")
    errors: list[str] = []
    slide_matches = re.findall(
        r"<section\b([^>]*class=[\"'][^\"']*\bslide\b[^>]*)>", source, re.I | re.S
    )
    html_slide_ids = [attrs(match).get("data-slide-id", "") for match in slide_matches]
    story_ids = [normalize(item.get("id")) for item in story_slides]
    if html_slide_ids != story_ids:
        errors.append(f"{path}: HTML slide order differs from Story")

    nodes = re.findall(
        r"<div\b([^>]*class=[\"'][^\"']*\broadmap-node\b[^>]*)>(.*?)</div>",
        source,
        re.I | re.S,
    )
    items = list(roadmap.get("items") or [])
    if len(nodes) != len(items):
        errors.append(f"{path}: expected {len(items)} roadmap nodes, found {len(nodes)}")
        return errors
    flattened: list[str] = []
    for index, ((raw_attrs, body), item) in enumerate(zip(nodes, items), 1):
        values = attrs(raw_attrs)
        member_ids = normalize(values.get("data-roadmap-slide-ids")).split()
        flattened.extend(member_ids)
        if member_ids != [normalize(value) for value in item.get("slide_ids") or []]:
            errors.append(f"{path}: roadmap node {index} slide IDs differ from Story")
        if values.get("data-roadmap-page-start") != str(item.get("page_start")):
            errors.append(f"{path}: roadmap node {index} page start differs from Story")
        if values.get("data-roadmap-page-end") != str(item.get("page_end")):
            errors.append(f"{path}: roadmap node {index} page end differs from Story")
        node_text = visible_text(body)
        for required in (item.get("label"), item.get("summary"), f"{item.get('page_start')}–{item.get('page_end')}"):
            if normalize(required) not in node_text:
                errors.append(f"{path}: roadmap node {index} does not visibly contain {required!r}")
    expected = [normalize(value) for item in items for value in item.get("slide_ids") or []]
    if flattened != expected:
        errors.append(f"{path}: roadmap HTML coverage/order differs from Story")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--story", type=Path, required=True)
    parser.add_argument("--blueprint", type=Path)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()

    story = load_yaml(args.story)
    errors, roadmap, story_slides = validate_yaml_contract(story, args.story)
    if args.blueprint:
        blueprint_errors, _ = validate_blueprint(args.blueprint, roadmap)
        errors.extend(blueprint_errors)
    if args.html:
        errors.extend(validate_html(args.html, roadmap, story_slides))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    if roadmap:
        print(f"OK: {len(roadmap.get('items') or [])} roadmap milestones match the generated story")
    else:
        print("OK: roadmap is not required for this deck")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
