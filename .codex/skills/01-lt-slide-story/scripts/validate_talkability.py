#!/usr/bin/env python3
"""Validate whether an LT deck can be narrated without inventing the talk live."""

from __future__ import annotations

import argparse
from collections import Counter
from html.parser import HTMLParser
import math
from pathlib import Path
import re
from typing import Any

import yaml

from validate_spoken_notes import GENERIC_SCRIPT, compact, validate_slides


PHASES = ("why", "what", "how", "demo", "takeaway")
NON_BODY_ROLES = {"cover", "profile", "thanks"}
NO_POINT_ROLES = NON_BODY_ROLES | {"goal"}
GENERIC_OBSERVATIONS = {
    "確認する",
    "結果を確認する",
    "画面を確認する",
    "理解する",
    "動作を確認する",
}


def text(value: Any) -> str:
    return str(value or "").strip()


def string_list(value: Any) -> list[str]:
    return [text(item) for item in value] if isinstance(value, list) else []


def matches_anchor(point: str, anchors: list[str]) -> bool:
    needle = compact(point)
    return any(needle == compact(anchor) or needle in compact(anchor) or compact(anchor) in needle for anchor in anchors)


def sentence_count(value: str) -> int:
    return len(re.findall(r"[。！？!?]", value))


def validate_question_spine(path: Path, story: dict, errors: list[str]) -> dict[str, dict]:
    project = story.get("project") or {}
    duration = int(project.get("duration_minutes") or 0)
    narrative = story.get("narrative") or {}
    for key in ("central_example", "opening_problem", "final_change"):
        if len(compact(narrative.get(key))) < 8:
            errors.append(f"{path}: narrative.{key} must be a concrete sentence")

    spine = narrative.get("question_spine")
    if not isinstance(spine, list):
        errors.append(f"{path}: narrative.question_spine must be a list")
        return {}
    by_phase = {text(item.get("phase")): item for item in spine if isinstance(item, dict)}
    required = PHASES if duration >= 20 else tuple(phase for phase in PHASES if phase not in {
        text(item.get("phase")) for item in (narrative.get("omitted_phases") or []) if isinstance(item, dict)
    })
    actual_order = [text(item.get("phase")) for item in spine if isinstance(item, dict)]
    if actual_order != list(required):
        errors.append(f"{path}: question_spine phase order must be {', '.join(required)}")

    signatures: Counter[str] = Counter()
    phase_seconds = 0
    for phase in required:
        item = by_phase.get(phase)
        if not isinstance(item, dict):
            errors.append(f"{path}: question_spine is missing {phase}")
            continue
        for key in ("audience_question", "answer", "transition_to_next"):
            value = text(item.get(key))
            if len(compact(value)) < 8:
                errors.append(f"{path}:{phase}: {key} must be a concrete spoken sentence")
            signatures[compact(value)] += 1
        seconds = item.get("time_seconds")
        if not isinstance(seconds, int) or seconds <= 0:
            errors.append(f"{path}:{phase}: time_seconds must be a positive integer")
        else:
            phase_seconds += seconds
        if not string_list(item.get("source_items")):
            errors.append(f"{path}:{phase}: source_items must not be empty")

    if any(signature and count > 1 for signature, count in signatures.items()):
        errors.append(f"{path}: question_spine contains duplicated questions, answers, or transitions")

    framing = narrative.get("framing_seconds")
    if not isinstance(framing, int) or framing < 0:
        errors.append(f"{path}: narrative.framing_seconds must be a non-negative integer")
    budget = project.get("time_budget") or {}
    timed = sum(int(budget.get(key) or 0) for key in ("content_seconds", "demo_seconds", "interaction_seconds"))
    if timed and isinstance(framing, int) and phase_seconds + framing != timed:
        errors.append(f"{path}: framing + question_spine={phase_seconds + framing}s, expected {timed}s excluding buffer")
    return by_phase


def validate_demo(path: Path, story: dict, errors: list[str]) -> None:
    runbook = story.get("demo_runbook")
    if not isinstance(runbook, dict):
        errors.append(f"{path}: demo_runbook is required")
        return
    for key in ("starting_state", "end_state", "fallback"):
        if len(compact(runbook.get(key))) < 8:
            errors.append(f"{path}: demo_runbook.{key} must be concrete")
    if not string_list(runbook.get("source_items")):
        errors.append(f"{path}: demo_runbook.source_items must not be empty")
    steps = runbook.get("steps")
    if not isinstance(steps, list) or len(steps) < 3:
        errors.append(f"{path}: demo_runbook.steps requires at least three observable steps")
        return
    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            errors.append(f"{path}: demo step {index} must be a mapping")
            continue
        for key in ("action", "visible_result", "talk_line"):
            if len(compact(step.get(key))) < 6:
                errors.append(f"{path}: demo step {index}.{key} must be concrete")
        if compact(step.get("visible_result")) in {compact(value) for value in GENERIC_OBSERVATIONS}:
            errors.append(f"{path}: demo step {index}.visible_result is not observable")


def validate_takeaway(path: Path, story: dict, errors: list[str]) -> None:
    action = story.get("tomorrow_action")
    if not isinstance(action, dict):
        errors.append(f"{path}: tomorrow_action is required")
        return
    for key in ("timebox", "action", "artifact", "done_when", "first_step"):
        if len(compact(action.get(key))) < 3:
            errors.append(f"{path}: tomorrow_action.{key} must be concrete")
    if compact(action.get("action")) in {"試してみる", "検討する", "確認する"}:
        errors.append(f"{path}: tomorrow_action.action must name an actual operation")


def validate_page_cues(path: Path, story: dict, spine: dict[str, dict], errors: list[str]) -> None:
    slides = story.get("slides") or []
    note_errors, _ = validate_slides(slides, talkability_version=2)
    errors.extend(f"{path}:{error}" for error in note_errors)
    script_signatures: dict[str, str] = {}
    phase_totals = Counter()
    framing_total = 0
    body_timings: list[int] = []

    for index, slide in enumerate(slides, start=1):
        sid = text(slide.get("id")) or f"slide-{index}"
        role = text(slide.get("role"))
        phase = text(slide.get("flow_phase"))
        cue = slide.get("speaker_cue")
        if not isinstance(cue, dict):
            continue
        for key in ("purpose", "audience_state_before", "audience_state_after", "script", "transition"):
            if len(compact(cue.get(key))) < 8:
                errors.append(f"{path}:{sid}: speaker_cue.{key} must be concrete")
        if compact(cue.get("audience_state_before")) == compact(cue.get("audience_state_after")):
            errors.append(f"{path}:{sid}: audience state must change across the slide")

        script = text(cue.get("script"))
        signature = compact(script)
        if signature in script_signatures:
            errors.append(f"{path}:{sid}: speaker_cue.script duplicates {script_signatures[signature]}")
        elif signature:
            script_signatures[signature] = sid
        if any(compact(phrase) in signature for phrase in GENERIC_SCRIPT):
            errors.append(f"{path}:{sid}: speaker_cue.script is a meta-explanation template")

        delivery = slide.get("delivery") or {}
        seconds = delivery.get("estimated_seconds")
        if role not in NON_BODY_ROLES and isinstance(seconds, int):
            body_timings.append(seconds)
            expected_chars = min(240, max(50, math.ceil(seconds * 1.5)))
            if len(compact(script)) < expected_chars:
                errors.append(f"{path}:{sid}: script is too short for {seconds}s; need about {expected_chars}+ characters")
            if seconds >= 45 and sentence_count(script) < 2:
                errors.append(f"{path}:{sid}: 45+ second script must contain multiple spoken sentences")
            if phase:
                phase_totals[phase] += seconds
            else:
                framing_total += seconds

        points = string_list(cue.get("point_at"))
        mode = text(delivery.get("mode"))
        allow_none = role in NO_POINT_ROLES or mode == "transition"
        real_points = [point for point in points if compact(point) != "none"]
        if not points or (not real_points and not allow_none):
            errors.append(f"{path}:{sid}: substantive slide requires speaker_cue.point_at")
        anchors = string_list(delivery.get("visible_anchors"))
        for point in real_points:
            if not matches_anchor(point, anchors):
                errors.append(f"{path}:{sid}: point_at '{point}' is not in delivery.visible_anchors")
        if phase and phase not in spine:
            errors.append(f"{path}:{sid}: flow_phase '{phase}' is missing from question_spine")

    for phase, item in spine.items():
        seconds = item.get("time_seconds")
        if isinstance(seconds, int) and phase_totals[phase] != seconds:
            errors.append(f"{path}:{phase}: slide time={phase_totals[phase]}s, question_spine={seconds}s")
    framing = (story.get("narrative") or {}).get("framing_seconds")
    if isinstance(framing, int) and framing_total != framing:
        errors.append(f"{path}: framing slide time={framing_total}s, narrative.framing_seconds={framing}s")
    if len(body_timings) >= 6 and len(set(body_timings)) == 1:
        errors.append(f"{path}: all body slides use {body_timings[0]}s; vary pacing by explanation role")


def validate_story(path: Path, story: dict) -> list[str]:
    errors: list[str] = []
    project = story.get("project") or {}
    duration = int(project.get("duration_minutes") or 0)
    version = int(project.get("talkability_version") or 0)
    if duration >= 20 and version != 2:
        errors.append(f"{path}: 20+ minute deck requires project.talkability_version: 2")
        return errors
    if version != 2:
        return errors
    spine = validate_question_spine(path, story, errors)
    validate_demo(path, story, errors)
    validate_takeaway(path, story, errors)
    validate_page_cues(path, story, spine, errors)
    return errors


def load_stories(path: Path) -> tuple[list[str], list[tuple[Path, dict]]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if data.get("kind") != "lt-slide-series":
        return [], [(path, data)]
    errors: list[str] = []
    stories: list[tuple[Path, dict]] = []
    for part in data.get("parts") or []:
        child = (path.parent / text(part.get("story_file"))).resolve()
        if not child.is_file():
            errors.append(f"{path}: part story is missing: {child}")
            continue
        child_errors, child_stories = load_stories(child)
        errors.extend(child_errors)
        stories.extend(child_stories)
    return errors, stories


def flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for value_item in value for item in flatten_strings(value_item)]
    if isinstance(value, dict):
        return [item for value_item in value.values() for item in flatten_strings(value_item)]
    return []


def validate_blueprint(path: Path, story: dict) -> list[str]:
    blueprint = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    expected = {text(slide.get("id")): slide for slide in story.get("slides") or []}
    errors: list[str] = []
    for slide in blueprint.get("slides") or []:
        sid = text(slide.get("id"))
        source = expected.get(sid)
        if not source:
            errors.append(f"{path}:{sid}: slide is not present in Story")
            continue
        if slide.get("speaker_cue") != source.get("speaker_cue"):
            errors.append(f"{path}:{sid}: speaker_cue was not copied unchanged")
        if slide.get("spoken_note") != source.get("spoken_note"):
            errors.append(f"{path}:{sid}: spoken_note was not copied unchanged")
        phase = text(source.get("flow_phase"))
        if phase:
            spine = {text(item.get("phase")): item for item in (story.get("narrative") or {}).get("question_spine") or []}
            expected_context = spine.get(phase) or {}
            actual_context = slide.get("phase_context") or {}
            for key in ("audience_question", "answer", "transition_to_next"):
                if text(actual_context.get(key)) != text(expected_context.get(key)):
                    errors.append(f"{path}:{sid}: phase_context.{key} does not match question_spine")
        points = [point for point in string_list((source.get("speaker_cue") or {}).get("point_at")) if compact(point) != "none"]
        visible = flatten_strings({
            "delivery": slide.get("delivery") or {},
            "text": slide.get("text") or {},
            "content_model": slide.get("content_model") or {},
            "annotations": (slide.get("visual") or {}).get("annotations") or [],
        })
        for point in points:
            if not matches_anchor(point, visible):
                errors.append(f"{path}:{sid}: point_at '{point}' is not implemented in the Blueprint")
    missing = sorted(set(expected) - {text(slide.get("id")) for slide in blueprint.get("slides") or []})
    if missing:
        errors.append(f"{path}: Blueprint is missing Story slides: {', '.join(missing)}")
    return errors


class DeckParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.slides: dict[str, dict[str, str]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "section":
            return
        values = {key: value or "" for key, value in attrs}
        classes = values.get("class", "").split()
        if "slide" in classes and values.get("data-slide-id"):
            self.slides[values["data-slide-id"]] = values


def validate_html(path: Path, story: dict) -> list[str]:
    parser = DeckParser()
    parser.feed(path.read_text(encoding="utf-8"))
    spine = {text(item.get("phase")): item for item in (story.get("narrative") or {}).get("question_spine") or []}
    errors: list[str] = []
    for slide in story.get("slides") or []:
        sid = text(slide.get("id"))
        attrs = parser.slides.get(sid)
        if attrs is None:
            errors.append(f"{path}:{sid}: data-slide-id is missing")
            continue
        expected = {
            "data-flow-phase": text(slide.get("flow_phase")),
            "data-speaker-purpose": text((slide.get("speaker_cue") or {}).get("purpose")),
            "data-spoken-note": text(slide.get("spoken_note")),
        }
        phase = text(slide.get("flow_phase"))
        if phase:
            expected["data-phase-question"] = text((spine.get(phase) or {}).get("audience_question"))
        for key, value in expected.items():
            if key not in attrs:
                errors.append(f"{path}:{sid}: {key} is missing")
            elif attrs.get(key, "") != value:
                errors.append(f"{path}:{sid}: {key} does not match Story")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="LTの問い・台本・実演・明日の一手を検証する")
    parser.add_argument("--story", required=True, type=Path)
    parser.add_argument("--blueprint", type=Path)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()

    try:
        errors, stories = load_stories(args.story.resolve())
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: story を読めません: {exc}")
        return 1
    for story_path, story in stories:
        errors.extend(validate_story(story_path, story))
    if (args.blueprint or args.html) and len(stories) != 1:
        errors.append("--blueprint and --html require a single part Story")
    elif stories:
        _, story = stories[0]
        if int((story.get("project") or {}).get("talkability_version") or 0) == 2:
            if args.blueprint:
                errors.extend(validate_blueprint(args.blueprint.resolve(), story))
            if args.html:
                errors.extend(validate_html(args.html.resolve(), story))
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print(f"OK: {len(stories)}件の問い・台本・Demo・Takeaway契約を検証しました")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
