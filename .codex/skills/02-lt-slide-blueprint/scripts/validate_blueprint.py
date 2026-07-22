#!/usr/bin/env python3
import sys
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required: python -m pip install pyyaml")
    raise SystemExit(2)

CANVAS_W = 1280
CANVAS_H = 720
MIN_GAP = 8
REQUIRED_ZONES = ("title_zone", "footer_zone")


def compact(value):
    return re.sub(r"\s+", "", str(value or "")).casefold()


def flatten_strings(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in flatten_strings(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in flatten_strings(child)]
    return []


def matches_anchor(point, values):
    needle = compact(point)
    return any(needle == compact(value) or needle in compact(value) or compact(value) in needle for value in values)


def rect(value):
    return tuple(int(value[key]) for key in ("x", "y", "w", "h"))


def intersects(a, b, gap=MIN_GAP):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (
        ax + aw + gap <= bx
        or bx + bw + gap <= ax
        or ay + ah + gap <= by
        or by + bh + gap <= ay
    )


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_blueprint.py <02-blueprint.yaml>")
        return 2

    path = Path(sys.argv[1])
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    errors = []
    duration = 0
    story = {}
    source_story = data.get("source_story")
    if source_story:
        story_path = (path.parent / source_story).resolve()
        if story_path.exists():
            story = yaml.safe_load(story_path.read_text(encoding="utf-8")) or {}
            duration = int((story.get("project") or {}).get("duration_minutes", 0))
    talkability_version = int((story.get("project") or {}).get("talkability_version", 0) or 0)
    story_slides = {str(slide.get("id")): slide for slide in story.get("slides") or []}
    question_spine = {
        str(item.get("phase")): item
        for item in (story.get("narrative") or {}).get("question_spine") or []
        if isinstance(item, dict)
    }

    canvas = data.get("canvas", {})
    if canvas.get("width") != CANVAS_W or canvas.get("height") != CANVAS_H:
        errors.append("canvas must be 1280x720")

    slides = data.get("slides") or []
    if not slides:
        errors.append("slides must not be empty")

    for slide in slides:
        sid = slide.get("id", "<missing-id>")
        if "spoken_note" not in slide or not isinstance(slide.get("spoken_note"), str):
            errors.append(f"{sid}: spoken_note must be present as a string")
        if talkability_version == 2:
            source = story_slides.get(str(sid))
            if not source:
                errors.append(f"{sid}: slide does not exist in source Story")
            else:
                if slide.get("speaker_cue") != source.get("speaker_cue"):
                    errors.append(f"{sid}: speaker_cue must be copied unchanged from Story")
                if slide.get("spoken_note") != source.get("spoken_note"):
                    errors.append(f"{sid}: spoken_note must be copied unchanged from Story")
                phase = str(source.get("flow_phase") or "")
                if phase:
                    context = slide.get("phase_context") or {}
                    expected_context = question_spine.get(phase) or {}
                    for key in ("audience_question", "answer", "transition_to_next"):
                        if str(context.get(key) or "") != str(expected_context.get(key) or ""):
                            errors.append(f"{sid}: phase_context.{key} must match question_spine")
                point_at = (source.get("speaker_cue") or {}).get("point_at") or []
                visible = flatten_strings({
                    "delivery": slide.get("delivery") or {},
                    "text": slide.get("text") or {},
                    "content_model": slide.get("content_model") or {},
                    "annotations": (slide.get("visual") or {}).get("annotations") or [],
                })
                for point in point_at:
                    if compact(point) != "none" and not matches_anchor(point, visible):
                        errors.append(f"{sid}: speaker_cue.point_at '{point}' is not implemented")
        zones = slide.get("zones") or {}
        if slide.get("role") == "profile":
            if "conclusion_zone" in zones:
                errors.append(f"{sid}: profile must not define conclusion_zone")
            profile_text = slide.get("text") or {}
            if str(profile_text.get("conclusion") or "").strip():
                errors.append(f"{sid}: profile text.conclusion must be empty")
            for key in ("bullets", "details", "anchor_labels"):
                if profile_text.get(key):
                    errors.append(f"{sid}: profile text.{key} must be empty; render presenter.json directly")
        for name in REQUIRED_ZONES:
            if name not in zones:
                errors.append(f"{sid}: missing {name}")

        parsed = {}
        for name, value in zones.items():
            try:
                current = rect(value)
            except (KeyError, TypeError, ValueError):
                errors.append(f"{sid}: invalid zone {name}")
                continue
            x, y, w, h = current
            if min(x, y, w, h) < 0 or x + w > CANVAS_W or y + h > CANVAS_H:
                errors.append(f"{sid}: {name} exceeds canvas")
            parsed[name] = current

        names = list(parsed)
        for index, left_name in enumerate(names):
            if left_name in ("footer_zone", "connector_zone"):
                continue
            for right_name in names[index + 1 :]:
                if right_name in ("footer_zone", "connector_zone"):
                    continue
                if intersects(parsed[left_name], parsed[right_name]):
                    errors.append(f"{sid}: {left_name} intersects {right_name}")

        typography = slide.get("typography") or {}
        for key in ("body_px", "message_px"):
            value = typography.get(key)
            minimum = 24 if duration >= 20 and key == "body_px" else 28
            if value is not None and int(value) < minimum:
                errors.append(f"{sid}: {key} must be at least {minimum}")
        source_px = typography.get("source_px")
        if source_px is not None and int(source_px) < 18:
            errors.append(f"{sid}: source_px must be at least 18")

        animation = slide.get("animation") or {}
        steps = animation.get("steps") or []
        selection = animation.get("selection") or {}
        if not str(selection.get("rule_id") or "").strip() or not str(selection.get("rationale") or "").strip():
            errors.append(f"{sid}: animation.selection rule_id and rationale are required")
        for item in (animation.get("entrance") or []) + steps:
            if isinstance(item, dict) and not str(item.get("reason") or "").strip():
                errors.append(f"{sid}: every animation entrance/step needs a semantic reason")
        for item in steps:
            if not isinstance(item, dict):
                continue
            targets = {str(target) for target in item.get("targets") or []}
            if targets != set((item.get("target_presets") or {}).keys()):
                errors.append(f"{sid}: target_presets must cover every step target")
            if targets != set((item.get("target_reasons") or {}).keys()):
                errors.append(f"{sid}: target_reasons must cover every step target")
        sequence = animation.get("sequence") or {}
        completion_targets = set(sequence.get("completion_targets") or [])
        for item in steps:
            if not isinstance(item, dict):
                continue
            for target, preset in (item.get("target_presets") or {}).items():
                if preset in {"stamp", "stomp", "flip-in"} and target not in completion_targets:
                    errors.append(f"{sid}: strong preset {preset} is not reserved for completion target {target}")
                if preset == "draw" and target not in {"connection", "harness-map"}:
                    errors.append(f"{sid}: draw is incompatible with target {target}")
                if preset == "slide-left" and target != "left-state":
                    errors.append(f"{sid}: slide-left is incompatible with target {target}")
                if preset == "slide-right" and target != "right-state":
                    errors.append(f"{sid}: slide-right is incompatible with target {target}")
        sequence_mode = str(sequence.get("mode") or "staged")
        step_limit = 9 if sequence_mode == "item-by-item" else 6
        if len(steps) > step_limit:
            errors.append(f"{sid}: animation steps exceed {step_limit} for {sequence_mode}")
        if int(sequence.get("max_steps") or -1) != len(steps):
            errors.append(f"{sid}: animation.sequence.max_steps must equal the declared step count")
        initial_targets = sequence.get("initial_targets") or []
        if "title" not in initial_targets:
            errors.append(f"{sid}: animation.sequence.initial_targets must include title")
        ordered_targets = sequence.get("ordered_targets") or []
        if slide.get("role") == "profile":
            if "conclusion" in ordered_targets:
                errors.append(f"{sid}: profile animation must not target a conclusion")
        elif not ordered_targets or ordered_targets[-1] != "conclusion":
            errors.append(f"{sid}: animation.sequence.ordered_targets must end with conclusion")
        if sequence.get("coverage") != "all-meaningful-siblings":
            errors.append(f"{sid}: animation.sequence.coverage must be all-meaningful-siblings")
        if not str(animation.get("intent") or "").strip():
            errors.append(f"{sid}: animation.intent is required")
        if animation.get("family") not in {"quiet-reveal", "direction", "structure", "focus", "decision"}:
            errors.append(f"{sid}: animation.family is invalid")
        if (story.get("project") or {}).get("content_fidelity") == "full-equivalence":
            source = story_slides.get(str(sid)) or {}
            if slide.get("source_unit_ids") != source.get("source_unit_ids"):
                errors.append(f"{sid}: source_unit_ids must be copied unchanged from Story")

        budget = slide.get("text_budget") or {}
        bullets = ((slide.get("text") or {}).get("bullets")) or []
        if len(bullets) > int(budget.get("bullets_max", 4)):
            errors.append(f"{sid}: bullet count exceeds text budget")

    roles = [slide.get("role") for slide in slides]
    if len(roles) < 2 or roles[-2:] != ["recap", "thanks"]:
        errors.append("last two slides must be recap and thanks")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"OK: {len(slides)} slides validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
