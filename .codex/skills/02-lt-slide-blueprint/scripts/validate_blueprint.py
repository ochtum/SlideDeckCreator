#!/usr/bin/env python3
import sys
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
        zones = slide.get("zones") or {}
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
            if value is not None and int(value) < 28:
                errors.append(f"{sid}: {key} must be at least 28")
        source_px = typography.get("source_px")
        if source_px is not None and int(source_px) < 18:
            errors.append(f"{sid}: source_px must be at least 18")

        steps = (slide.get("animation") or {}).get("steps") or []
        if len(steps) > 4:
            errors.append(f"{sid}: animation steps exceed 4")

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
