#!/usr/bin/env python3
"""Fail LT artifacts that are implausibly short for their duration.

The floor is deliberately lower than the recommended range.  Slide count is a
safety rail, not a target: long talks must earn their duration through examples,
speaker cues, demos, and evidence rather than one sparse statement per minute.
"""

from __future__ import annotations

import argparse
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
    return sum(slide.get("role") not in NON_BODY_ROLES for slide in slides)


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
    duration = int(project["duration_minutes"])
    floor = minimum_body_slides(duration)
    actual = body_count(data.get("slides", []))
    target = int(project["target_slide_count"])
    errors = []
    if actual != target:
        errors.append(f"{path}: body slides={actual}, but target_slide_count={target}")
    if actual < floor:
        errors.append(
            f"{path}: {duration} minutes requires at least {floor} body slides; found {actual}. "
            "Add only substantive examples, comparisons, exercises, or demos, or shorten the duration."
        )
    return errors, [(path, data)]


def validate_blueprint(path: Path, story: dict) -> list[str]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    duration = int(story["project"]["duration_minutes"])
    floor = minimum_body_slides(duration)
    actual = body_count(data.get("slides", []))
    target = int(story["project"]["target_slide_count"])
    errors = []
    if actual != target:
        errors.append(f"{path}: body slides={actual}, but story target_slide_count={target}")
    if actual < floor:
        errors.append(f"{path}: {duration} minutes requires at least {floor} body slides; found {actual}")
    return errors


def validate_html(path: Path, story: dict) -> list[str]:
    html = path.read_text(encoding="utf-8")
    roles = re.findall(r'<section\b[^>]*class=["\'][^"\']*\bslide\b[^"\']*["\'][^>]*data-role=["\']([^"\']+)', html, re.I)
    if not roles:
        roles = re.findall(r'<section\b[^>]*data-role=["\']([^"\']+)', html, re.I)
    duration = int(story["project"]["duration_minutes"])
    floor = minimum_body_slides(duration)
    actual = sum(role not in NON_BODY_ROLES for role in roles)
    target = int(story["project"]["target_slide_count"])
    errors = []
    if actual != target:
        errors.append(f"{path}: body slides={actual}, but story target_slide_count={target}")
    if actual < floor:
        errors.append(f"{path}: {duration} minutes requires at least {floor} body slides; found {actual}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--story", required=True, type=Path)
    parser.add_argument("--blueprint", type=Path)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()

    errors, stories = validate_story(args.story)
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
    print("OK: duration-based body-slide floor passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
