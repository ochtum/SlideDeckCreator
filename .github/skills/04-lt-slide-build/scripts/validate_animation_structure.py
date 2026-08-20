#!/usr/bin/env python3
"""Validate complete reveal coverage and semantic reading order in built HTML."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path


MEANINGFUL_CLASSES = {
    "flow-node",
    "input-terminal",
    "output-terminal",
    "compare-card",
    "criteria-strip",
    "file-card",
    "code-frame",
    "code-highlight",
    "code-validation",
    "playbook-card",
    "check-row",
    "table-evidence-foot",
    "conclusion-bar",
    "avatar-card",
    "profile-copy",
    "qr-card",
    "harness-orbit",
    "cover-evidence",
    "thanks-message",
    "thanks-anchor",
}


def integer(value: str, default: int = -1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass
class Element:
    tag: str
    classes: set[str]
    attrs: dict[str, str]
    order_in_dom: int

    @property
    def step(self) -> int:
        return integer(self.attrs.get("data-step", ""))

    @property
    def reading_order(self) -> int:
        return integer(self.attrs.get("data-reading-order", ""))

    @property
    def label(self) -> str:
        name = sorted(self.classes.intersection(MEANINGFUL_CLASSES))
        return name[0] if name else self.tag


@dataclass
class Slide:
    sid: str
    role: str = ""
    elements: list[Element] = field(default_factory=list)
    title: Element | None = None
    conclusions: list[Element] = field(default_factory=list)


class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.slides: list[Slide] = []
        self.current: Slide | None = None
        self.section_depth = 0
        self.tbody_depth = 0
        self.dom_order = 0
        self.duplicate_attrs: list[tuple[str, str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        classes = set(values.get("class", "").split())
        tag_name = tag.casefold()
        if tag_name == "section" and "slide" in classes:
            self.current = Slide(
                values.get("data-slide-id") or f"slide-{len(self.slides) + 1}",
                values.get("data-role", ""),
            )
            self.slides.append(self.current)
            self.section_depth = 1
            self.tbody_depth = 0
            self.dom_order = 0
            return
        if self.current is None:
            return
        duplicates = [name for name, count in Counter(key for key, _ in attrs).items() if count > 1]
        self.duplicate_attrs.extend((self.current.sid, tag_name, name) for name in duplicates)
        if tag_name == "section":
            self.section_depth += 1
        if tag_name == "tbody":
            self.tbody_depth += 1
        self.dom_order += 1
        element = Element(tag_name, classes, values, self.dom_order)
        is_meaningful = bool(classes.intersection(MEANINGFUL_CLASSES)) or (
            tag_name == "tr" and self.tbody_depth > 0
        )
        if is_meaningful or values.get("data-reveal-item") == "true" or values.get("data-anim"):
            self.current.elements.append(element)
        if "slide-title" in classes:
            self.current.title = element
        if "conclusion-bar" in classes or "thanks-anchor" in classes:
            self.current.conclusions.append(element)

    def handle_endtag(self, tag: str) -> None:
        if self.current is None:
            return
        tag_name = tag.casefold()
        if tag_name == "tbody" and self.tbody_depth:
            self.tbody_depth -= 1
        if tag_name == "section":
            self.section_depth -= 1
            if self.section_depth <= 0:
                self.current = None


def validate(html_text: str) -> tuple[list[str], dict[str, int]]:
    parser = Parser()
    parser.feed(html_text)
    errors: list[str] = []
    stats = {"slides": len(parser.slides), "reveal_items": 0, "groups": 0, "max_step": 0}

    for sid, tag, name in parser.duplicate_attrs:
        errors.append(f"{sid}: <{tag}> has duplicate '{name}' attributes")

    for slide in parser.slides:
        title = slide.title
        if title is None:
            errors.append(f"{slide.sid}: .slide-title is missing")
        elif not title.attrs.get("data-static-intentional"):
            if not title.attrs.get("data-anim") or title.step != 0:
                errors.append(f"{slide.sid}: title must be static or animated at step 0")

        meaningful = [
            item for item in slide.elements
            if item.classes.intersection(MEANINGFUL_CLASSES) or (item.tag == "tr")
        ]
        for item in meaningful:
            animated = bool(item.attrs.get("data-anim"))
            intentional = bool(item.attrs.get("data-static-intentional"))
            if not animated and not intentional:
                errors.append(
                    f"{slide.sid}: meaningful {item.label} at DOM {item.order_in_dom} "
                    "is neither animated nor data-static-intentional"
                )

        reveal_items = [item for item in slide.elements if item.attrs.get("data-reveal-item") == "true"]
        stats["reveal_items"] += len(reveal_items)
        groups: dict[str, list[Element]] = defaultdict(list)
        for item in reveal_items:
            if not item.attrs.get("data-anim"):
                errors.append(f"{slide.sid}: reveal item {item.label} has no data-anim")
            if item.step < 1:
                errors.append(f"{slide.sid}: reveal item {item.label} must use step >= 1")
            group = item.attrs.get("data-reveal-group")
            if not group:
                errors.append(f"{slide.sid}: reveal item {item.label} has no data-reveal-group")
                continue
            if item.reading_order < 1:
                errors.append(f"{slide.sid}: reveal item {item.label} has invalid data-reading-order")
            if not item.attrs.get("data-sequence-mode"):
                errors.append(f"{slide.sid}: reveal item {item.label} has no data-sequence-mode")
            if not item.attrs.get("data-motion-reason"):
                errors.append(f"{slide.sid}: reveal item {item.label} has no data-motion-reason")
            groups[group].append(item)

        stats["groups"] += len(groups)
        positive_steps = sorted({
            item.step for item in slide.elements if item.attrs.get("data-anim") and item.step > 0
        })
        max_step = max(positive_steps, default=0)
        stats["max_step"] = max(stats["max_step"], max_step)
        if max_step > 9:
            errors.append(f"{slide.sid}: maximum runtime step is {max_step}; must be <= 9")
        if positive_steps and positive_steps != list(range(1, max_step + 1)):
            errors.append(f"{slide.sid}: runtime steps are not contiguous: {positive_steps}")

        for group_name, items in groups.items():
            ordered = sorted(items, key=lambda item: item.reading_order)
            orders = [item.reading_order for item in ordered]
            if orders != list(range(1, len(ordered) + 1)):
                errors.append(f"{slide.sid}: group {group_name} reading orders are not 1..N: {orders}")
            dom_orders = [item.order_in_dom for item in ordered]
            if dom_orders != sorted(dom_orders):
                errors.append(f"{slide.sid}: group {group_name} DOM order disagrees with reading order")
            steps = [item.step for item in ordered]
            modes = {item.attrs.get("data-sequence-mode") for item in ordered}
            if len(modes) != 1:
                errors.append(f"{slide.sid}: group {group_name} mixes sequence modes: {sorted(modes)}")
            elif "item-by-item" in modes and any(right <= left for left, right in zip(steps, steps[1:])):
                errors.append(f"{slide.sid}: group {group_name} item-by-item steps must increase: {steps}")
            elif any(right < left for left, right in zip(steps, steps[1:])):
                errors.append(f"{slide.sid}: group {group_name} steps move backwards: {steps}")

        if slide.role != "profile" and not slide.conclusions:
            errors.append(f"{slide.sid}: conclusion element is missing")
        for conclusion in slide.conclusions:
            if conclusion.step != max_step:
                errors.append(
                    f"{slide.sid}: conclusion must be last; step {conclusion.step}, max step {max_step}"
                )

    return errors, stats


def main() -> int:
    arguments = argparse.ArgumentParser(description="Validate semantic animation structure")
    arguments.add_argument("--html", required=True, type=Path)
    args = arguments.parse_args()
    errors, stats = validate(args.html.read_text(encoding="utf-8"))
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print(
        f"OK: {stats['slides']} slides; {stats['reveal_items']} reveal items; "
        f"{stats['groups']} groups; max step {stats['max_step']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
