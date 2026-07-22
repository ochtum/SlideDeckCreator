#!/usr/bin/env python3
"""Validate live slide counts while treating duration ranges as advisories.

Slide count is not a proxy for explanation time.  The historical floor remains
as a warning, while target counts and live/appendix separation stay contractual.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

import yaml

NON_BODY_ROLES = {"cover", "profile", "thanks"}


def minimum_body_slides(duration_minutes: int) -> int:
    """Return the safety floor; cover/profile/thanks are excluded."""
    if duration_minutes <= 5:
        return 6
    if duration_minutes <= 10:
        return 8
    if duration_minutes <= 15:
        return 10
    if duration_minutes < 30:
        return 14
    return 16


def body_count(slides: list[dict]) -> int:
    return sum(
        (slide.get("delivery_scope") or "live") == "live"
        and slide.get("role") not in NON_BODY_ROLES
        for slide in slides
    )


def appendix_count(slides: list[dict]) -> int:
    return sum((slide.get("delivery_scope") or "live") in {"appendix", "reference"} for slide in slides)


def live_body_slides(story: dict) -> list[dict]:
    return [
        slide
        for slide in story.get("slides", [])
        if (slide.get("delivery_scope") or "live") == "live"
        and slide.get("role") not in NON_BODY_ROLES
    ]


def phase_length_signature(slides: list[dict]) -> tuple[int, ...]:
    lengths: list[int] = []
    current = None
    count = 0
    for slide in slides:
        phase = slide.get("flow_phase") or ""
        if not phase:
            continue
        if phase != current:
            if count:
                lengths.append(count)
            current = phase
            count = 1
        else:
            count += 1
    if count:
        lengths.append(count)
    return tuple(lengths)


def source_unit_count(slides: list[dict]) -> int:
    return len({unit for slide in slides for unit in slide.get("source_unit_ids", [])})


def uniform_structure_requested(manifest: dict) -> bool:
    request = (manifest.get("series_analysis") or {}).get("uniform_structure_request") or {}
    return request.get("requested_by_user") is True and bool(str(request.get("reason") or "").strip())


def validate_series_uniformity(manifest_path: Path, manifest: dict, parts: list[tuple[Path, dict]]) -> list[str]:
    """Reject a shared slide template that masks materially different source loads."""
    if len(parts) < 3 or uniform_structure_requested(manifest):
        return []
    stories = [story for _, story in parts]
    targets = [int(story.get("project", {}).get("target_slide_count", -1)) for story in stories]
    if len(set(targets)) != 1:
        return []

    bodies = [live_body_slides(story) for story in stories]
    role_signatures = [tuple(slide.get("role") or "" for slide in slides) for slides in bodies]
    phase_signatures = [phase_length_signature(slides) for slides in bodies]
    timing_signatures = [
        tuple((slide.get("delivery") or {}).get("estimated_seconds") for slide in slides)
        for slides in bodies
    ]
    timings_complete = all(all(value is not None for value in signature) for signature in timing_signatures)
    identical_template = (
        len(set(role_signatures)) == 1
        and len(set(phase_signatures)) == 1
        and timings_complete
        and len(set(timing_signatures)) == 1
    )
    if not identical_template:
        return []

    source_counts = [source_unit_count(slides) for slides in bodies]
    if not source_counts or min(source_counts) <= 0:
        return []
    material_gap = max(source_counts) - min(source_counts)
    material_threshold = max(4, math.ceil(min(source_counts) * 0.25))
    if material_gap < material_threshold:
        return []

    part_labels = [path.parent.name for path, _ in parts]
    return [
        f"{manifest_path}: mechanically uniform series detected: all {len(parts)} parts declare "
        f"target_slide_count={targets[0]} and share the same live role, phase-length, and timing signatures, "
        f"while unique source-unit counts differ ({', '.join(f'{label}={count}' for label, count in zip(part_labels, source_counts))}). "
        "Derive each part from its own learning blocks, or record an explicit user request in "
        "series_analysis.uniform_structure_request."
    ]


def find_parent_series_manifest(story_path: Path) -> tuple[Path, dict] | None:
    resolved_story = story_path.resolve()
    for parent in resolved_story.parents:
        candidate = parent / "01-story.yaml"
        if candidate == resolved_story or not candidate.is_file():
            continue
        try:
            data = yaml.safe_load(candidate.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            continue
        if data.get("kind") != "lt-slide-series":
            continue
        child_paths = {
            (candidate.parent / part["story_file"]).resolve()
            for part in data.get("parts", [])
            if part.get("story_file")
        }
        if resolved_story in child_paths:
            return candidate, data
    return None


def validate_story(path: Path) -> tuple[list[str], list[tuple[Path, dict]]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data.get("kind") == "lt-slide-series":
        errors: list[str] = []
        parts: list[tuple[Path, dict]] = []
        for part in data.get("parts", []):
            story = path.parent / part["story_file"]
            child_errors, child_parts = validate_story(story)
            errors.extend(child_errors)
            parts.extend(child_parts)
        return errors, parts

    project = data.get("project", {})
    actual = body_count(data.get("slides", []))
    target = int(project["target_slide_count"])
    errors = []
    if actual != target:
        errors.append(f"{path}: body slides={actual}, but target_slide_count={target}")
    declared_appendix = project.get("appendix_slide_count")
    if isinstance(declared_appendix, int) and appendix_count(data.get("slides", [])) != declared_appendix:
        errors.append(
            f"{path}: appendix/reference slides={appendix_count(data.get('slides', []))}, "
            f"but appendix_slide_count={declared_appendix}"
        )
    return errors, [(path, data)]


def validate_blueprint(path: Path, story: dict) -> list[str]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    actual = body_count(data.get("slides", []))
    target = int(story["project"]["target_slide_count"])
    errors = []
    if actual != target:
        errors.append(f"{path}: body slides={actual}, but story target_slide_count={target}")
    declared_appendix = story["project"].get("appendix_slide_count")
    if isinstance(declared_appendix, int) and appendix_count(data.get("slides", [])) != declared_appendix:
        errors.append(f"{path}: appendix/reference slide count does not match story appendix_slide_count")
    return errors


def validate_html(path: Path, story: dict) -> list[str]:
    html = path.read_text(encoding="utf-8")
    sections = re.findall(r'<section\b[^>]*class=["\'][^"\']*\bslide\b[^"\']*["\'][^>]*>', html, re.I)
    actual = 0
    appendix_actual = 0
    for section in sections:
        role_match = re.search(r'data-role=["\']([^"\']+)', section, re.I)
        scope_match = re.search(r'data-delivery-scope=["\']([^"\']+)', section, re.I)
        role = role_match.group(1) if role_match else ""
        scope = scope_match.group(1) if scope_match else "live"
        if scope == "live" and role not in NON_BODY_ROLES:
            actual += 1
        if scope in {"appendix", "reference"}:
            appendix_actual += 1
    target = int(story["project"]["target_slide_count"])
    errors = []
    if actual != target:
        errors.append(f"{path}: body slides={actual}, but story target_slide_count={target}")
    declared_appendix = story["project"].get("appendix_slide_count")
    if isinstance(declared_appendix, int) and appendix_actual != declared_appendix:
        errors.append(f"{path}: appendix/reference slides={appendix_actual}, story appendix_slide_count={declared_appendix}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--story", required=True, type=Path)
    parser.add_argument("--blueprint", type=Path)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()

    root_data = yaml.safe_load(args.story.read_text(encoding="utf-8"))
    errors, stories = validate_story(args.story)
    if root_data.get("kind") == "lt-slide-series":
        errors.extend(validate_series_uniformity(args.story, root_data, stories))
    else:
        parent_series = find_parent_series_manifest(args.story)
        if parent_series:
            manifest_path, manifest = parent_series
            _, series_parts = validate_story(manifest_path)
            errors.extend(validate_series_uniformity(manifest_path, manifest, series_parts))
    if (args.blueprint or args.html) and len(stories) != 1:
        errors.append("--blueprint and --html require one part story, not a series manifest")
    elif stories:
        _, story = stories[0]
        if args.blueprint:
            errors.extend(validate_blueprint(args.blueprint, story))
        if args.html:
            errors.extend(validate_html(args.html, story))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    warnings = []
    for story_path, story in stories:
        duration = int(story["project"]["duration_minutes"])
        actual = body_count(story.get("slides", []))
        floor = minimum_body_slides(duration)
        if actual < floor:
            warnings.append(
                f"WARNING: {story_path}: live body slides={actual}, historical {duration}-minute advisory={floor}; "
                "accept when time and explanation-depth validation pass"
            )
    if warnings:
        print("\n".join(warnings))
    print("OK: live target and appendix counts passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
