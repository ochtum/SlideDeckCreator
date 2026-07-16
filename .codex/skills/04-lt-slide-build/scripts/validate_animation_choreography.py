#!/usr/bin/env python3
"""Validate motion variety, semantic choreography, and blueprint-to-HTML preservation."""

from __future__ import annotations

import argparse
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import yaml


FAMILIES = {
    "fade": "quiet-reveal", "rise": "quiet-reveal", "blur-in": "quiet-reveal",
    "slide-left": "direction", "slide-right": "direction", "wipe": "direction",
    "draw": "structure", "marker": "structure",
    "pop": "focus", "zoom-focus": "focus", "flip-in": "focus",
    "stamp": "decision", "stomp": "decision",
}
STRONG = {"stamp", "stomp", "flip-in"}


def text(value: Any) -> str:
    return str(value or "").strip()


def animation_items(slide: dict[str, Any]) -> list[dict[str, Any]]:
    animation = slide.get("animation") or {}
    items: list[dict[str, Any]] = []
    for item in animation.get("entrance") or []:
        if isinstance(item, dict):
            items.append({**item, "step": 0})
    for item in animation.get("steps") or []:
        if isinstance(item, dict):
            items.append(item)
    return items


class MotionHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.slides: list[list[str]] = []
        self.current: list[str] | None = None
        self.section_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag.casefold() == "section" and "slide" in values.get("class", "").split():
            self.current = []
            self.slides.append(self.current)
            self.section_depth = 1
        elif self.current is not None and tag.casefold() == "section":
            self.section_depth += 1
        if self.current is not None and values.get("data-anim"):
            self.current.append(values["data-anim"])

    def handle_endtag(self, tag: str) -> None:
        if self.current is None or tag.casefold() != "section":
            return
        self.section_depth -= 1
        if self.section_depth <= 0:
            self.current = None


def validate(blueprint: dict[str, Any], html_text: str | None = None) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    slides = blueprint.get("slides") or []
    preset_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    step_counts: list[int] = []
    signatures: list[str] = []

    for index, slide in enumerate(slides, start=1):
        sid = text(slide.get("id")) or f"slide-{index}"
        animation = slide.get("animation") or {}
        intent = text(animation.get("intent"))
        declared_family = text(animation.get("family"))
        items = animation_items(slide)
        presets = [text(item.get("preset")) for item in items if text(item.get("preset"))]
        if not intent:
            errors.append(f"{sid}: animation.intent is required")
        if not declared_family:
            errors.append(f"{sid}: animation.family is required")
        for preset in presets:
            if preset not in FAMILIES:
                errors.append(f"{sid}: unsupported preset '{preset}'")
                continue
            preset_counts[preset] += 1
            family_counts[FAMILIES[preset]] += 1
        explicit_steps = sorted({int(item.get("step") or 0) for item in (animation.get("steps") or []) if isinstance(item, dict)})
        step_count = max(explicit_steps, default=0)
        step_counts.append(step_count)
        signatures.append(f"{step_count}:" + ">".join(presets))
        if step_count > 6:
            errors.append(f"{sid}: maximum step is {step_count}; must be <= 6")
        if declared_family and declared_family not in set(FAMILIES.values()):
            errors.append(f"{sid}: unknown animation.family '{declared_family}'")

    substantive = len(slides) >= 20
    total = sum(preset_counts.values())
    if substantive:
        if len(preset_counts) < 5:
            errors.append(f"deck: use at least 5 presets; found {len(preset_counts)} ({', '.join(sorted(preset_counts))})")
        if len(family_counts) < 4:
            errors.append(f"deck: use at least 4 motion families; found {len(family_counts)}")
        if len(set(step_counts)) < 3:
            errors.append(f"deck: use at least 3 different step counts; found {sorted(set(step_counts))}")
        most_common_steps = Counter(step_counts).most_common(1)[0]
        if most_common_steps[1] / len(step_counts) > 0.65:
            errors.append(f"deck: {most_common_steps[1]}/{len(step_counts)} slides use {most_common_steps[0]} steps; pacing is too uniform")
        for start in range(max(0, len(signatures) - 2)):
            if len(set(signatures[start:start + 3])) == 1:
                errors.append(f"deck: identical motion signature repeats on slides {start + 1}-{start + 3}")
                break
        if total:
            preset, count = preset_counts.most_common(1)[0]
            if count / total > 0.65:
                errors.append(f"deck: preset '{preset}' is {count}/{total} ({count / total:.0%}); motion is too repetitive")
            strong = sum(preset_counts[preset] for preset in STRONG)
            if strong / total > 0.20:
                errors.append(f"deck: strong presets are {strong}/{total} ({strong / total:.0%}); reserve them for key moments")

    html_counts: Counter[str] = Counter()
    if html_text is not None:
        parser = MotionHTMLParser()
        parser.feed(html_text)
        html_counts.update(preset for slide in parser.slides for preset in slide)
        unknown = sorted(set(html_counts) - set(FAMILIES))
        if unknown:
            errors.append(f"html: unsupported data-anim values: {', '.join(unknown)}")
        missing = sorted(set(preset_counts) - set(html_counts))
        if missing:
            errors.append(f"html: blueprint presets were lost or normalized: {', '.join(missing)}")
        if substantive and len(html_counts) < 5:
            errors.append(f"html: only {len(html_counts)} presets are implemented ({', '.join(sorted(html_counts))})")
        html_total = sum(html_counts.values())
        if substantive and html_total:
            preset, count = html_counts.most_common(1)[0]
            if count / html_total > 0.65:
                errors.append(f"html: data-anim '{preset}' is {count}/{html_total} ({count / html_total:.0%}); final motion is monotonous")

    return errors, {
        "slides": len(slides), "preset_counts": dict(preset_counts),
        "family_counts": dict(family_counts), "step_counts": dict(Counter(step_counts)),
        "html_preset_counts": dict(html_counts),
    }


def write_report(path: Path, stats: dict[str, Any], errors: list[str]) -> None:
    lines = [
        "# アニメーション演出レポート", "",
        f"- 判定: {'不合格' if errors else '合格'}",
        f"- スライド数: {stats['slides']}",
        f"- Blueprint presets: {stats['preset_counts']}",
        f"- Motion families: {stats['family_counts']}",
        f"- Step数分布: {stats['step_counts']}",
        f"- HTML presets: {stats['html_preset_counts']}",
        "", "## Findings", "",
    ]
    lines.extend([f"- {error}" for error in errors] or ["- なし"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="LTデッキのmotion choreographyを検証する")
    parser.add_argument("--blueprint", required=True, type=Path)
    parser.add_argument("--html", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    blueprint = yaml.safe_load(args.blueprint.read_text(encoding="utf-8")) or {}
    html_text = args.html.read_text(encoding="utf-8") if args.html else None
    errors, stats = validate(blueprint, html_text)
    if args.report:
        write_report(args.report, stats, errors)
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print(f"OK: {stats['slides']} slides; {len(stats['preset_counts'])} presets; {len(stats['family_counts'])} families")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
