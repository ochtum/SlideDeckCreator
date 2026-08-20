#!/usr/bin/env python3
"""Validate visible subject, actor, target, and predicate contracts."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
from typing import Any

import yaml


VERSION = 1
KINDS = {"action", "change", "decision", "definition", "state"}
SURFACES = {"title", "message", "body"}
ACTOR_KINDS = {"human", "ai", "tool", "process", "organization", "system", "not-applicable"}
NON_APPLICABLE_FIELDS = {"actor", "target"}
EXEMPT_ROLES = {"cover", "profile", "thanks"}
SUBJECT_MARKERS = ("は", "が", "も")
ACTOR_MARKERS = ("は", "が", "も", "によって", "により")
TARGET_MARKERS = ("を", "へ", "に", "から", "まで", "について", "に対して")
AGENTIVE_PREDICATES = (
    "する", "しない", "できる", "できない", "させる", "始める", "始められる",
    "作る", "変える", "決める", "たどる", "戻す", "守る", "防ぐ", "分ける",
    "混ぜない", "上げる", "固定する", "定義する", "選別する", "整える", "読む",
    "読ませる", "残す", "示す", "使う", "検証する", "変更する", "判断する",
    "置く", "通す", "止める", "許可する", "禁止する", "求める", "選ぶ", "絞る",
    "揃える", "追う", "扱う", "追加する", "削除する", "更新する", "比較する",
)
ACTION_LIKE_ENDINGS = AGENTIVE_PREDICATES + (
    "なる", "見える", "見えない", "広がる", "持つ", "残る", "一致する", "不足している",
)


def text(value: Any) -> str:
    return str(value or "").strip()


def compact(value: Any) -> str:
    return re.sub(r"\s+", "", text(value)).casefold()


def flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in flatten_strings(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in flatten_strings(child)]
    return []


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text(item) for item in value if text(item)]


def rendered_content_model(value: Any) -> dict[str, Any]:
    """Return only content-model fields that the slide renderer is required to draw."""
    if not isinstance(value, dict):
        return {}
    data = value.get("data")
    if value.get("variant") == "roadmap" and isinstance(data, dict):
        # start_title/end_title/source_section_ids are traceability metadata.
        # The roadmap renderer draws only the public label, summary, page range,
        # input, and output, so semantic checks must not treat provenance fields
        # as visible body copy.
        steps = []
        for step in data.get("steps") or []:
            if not isinstance(step, dict):
                continue
            steps.append({
                key: step.get(key)
                for key in ("label", "summary", "page_start", "page_end")
                if step.get(key) not in (None, "", [], {})
            })
        data = {
            key: item
            for key, item in {
                "steps": steps,
                "input": data.get("input"),
                "output": data.get("output"),
            }.items()
            if item not in (None, "", [], {})
        }
    return {
        key: item
        for key, item in {
            "data": data,
            "focus": value.get("focus"),
            "highlight": value.get("highlight"),
        }.items()
        if item not in (None, "", [], {})
    }


def has_marked_phrase(clause: str, phrase: str, markers: tuple[str, ...]) -> bool:
    normalized_clause = compact(clause)
    normalized_phrase = compact(phrase)
    return bool(normalized_phrase) and any(
        f"{normalized_phrase}{compact(marker)}" in normalized_clause for marker in markers
    )


def is_action_like(value: str) -> bool:
    normalized = compact(value).rstrip("。！？!?）」』】〉》")
    normalized = re.sub(r"(?:\[[0-9,\-–—]+\])+$", "", normalized)
    return any(normalized.endswith(compact(ending)) for ending in ACTION_LIKE_ENDINGS)


def body_strings(slide: dict) -> list[str]:
    values: list[str] = []
    for key in ("support", "information_layers"):
        values.extend(flatten_strings(slide.get(key)))
    values.extend(flatten_strings(rendered_content_model(slide.get("content_model"))))
    title_message = {compact(slide.get("title")), compact(slide.get("message"))}
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = compact(value)
        if not normalized or normalized in title_message or normalized in seen:
            continue
        seen.add(normalized)
        result.append(text(value))
    return result


def visible_story_strings(slide: dict) -> list[str]:
    return [
        value
        for value in [text(slide.get("title")), text(slide.get("message")), *body_strings(slide)]
        if value
    ]


def claim_error_prefix(path: Path, slide_id: str, index: int) -> str:
    return f"{path}:{slide_id}:semantic_clarity.claims[{index}]"


def validate_claim(path: Path, slide_id: str, index: int, claim: Any) -> list[str]:
    prefix = claim_error_prefix(path, slide_id, index)
    if not isinstance(claim, dict):
        return [f"{prefix} must be a mapping"]
    errors: list[str] = []
    surface = text(claim.get("surface"))
    surface_text = text(claim.get("surface_text"))
    clause = text(claim.get("clause"))
    kind = text(claim.get("kind"))
    subject = text(claim.get("subject"))
    actor = text(claim.get("actor"))
    actor_kind = text(claim.get("actor_kind"))
    target = text(claim.get("target"))
    predicate = text(claim.get("predicate"))
    not_applicable = set(string_list(claim.get("not_applicable")))

    if surface not in SURFACES:
        errors.append(f"{prefix}.surface must be one of {sorted(SURFACES)}")
    if not surface_text:
        errors.append(f"{prefix}.surface_text is required")
    if not clause:
        errors.append(f"{prefix}.clause is required")
    elif surface_text and compact(clause) not in compact(surface_text):
        errors.append(f"{prefix}.clause must appear in surface_text")
    if kind not in KINDS:
        errors.append(f"{prefix}.kind must be one of {sorted(KINDS)}")
    if actor_kind not in ACTOR_KINDS:
        errors.append(f"{prefix}.actor_kind must be one of {sorted(ACTOR_KINDS)}")
    unknown_na = not_applicable - NON_APPLICABLE_FIELDS
    if unknown_na:
        errors.append(f"{prefix}.not_applicable contains unknown fields: {sorted(unknown_na)}")

    if not subject:
        errors.append(f"{prefix}.subject is required")
    elif clause:
        if compact(subject) not in compact(clause):
            errors.append(f"{prefix}.subject must appear in clause")
        elif not has_marked_phrase(clause, subject, SUBJECT_MARKERS):
            errors.append(f"{prefix}.subject must be visible with は/が/も")
    if not predicate:
        errors.append(f"{prefix}.predicate is required")
    elif clause and compact(predicate) not in compact(clause):
        errors.append(f"{prefix}.predicate must appear in clause")

    if kind in {"action", "change", "decision"}:
        if not_applicable:
            errors.append(f"{prefix}: action/change/decision cannot omit actor or target")
        if not actor:
            errors.append(f"{prefix}.actor is required for {kind}")
        elif clause:
            if compact(actor) not in compact(clause):
                errors.append(f"{prefix}.actor must appear in clause")
            elif not has_marked_phrase(clause, actor, ACTOR_MARKERS):
                errors.append(f"{prefix}.actor must be visible with は/が/も/によって/により")
        if actor_kind == "not-applicable":
            errors.append(f"{prefix}.actor_kind cannot be not-applicable for {kind}")
        if not target:
            errors.append(f"{prefix}.target is required for {kind}")
        elif clause:
            if compact(target) not in compact(clause):
                errors.append(f"{prefix}.target must appear in clause")
            elif compact(target) != compact(subject) and not has_marked_phrase(clause, target, TARGET_MARKERS):
                errors.append(f"{prefix}.target must be visible with を/へ/に/から/まで")
    elif kind in {"definition", "state"}:
        for field, value in (("actor", actor), ("target", target)):
            if value:
                if field in not_applicable:
                    errors.append(f"{prefix}.{field} has a value but is also not_applicable")
                if clause and compact(value) not in compact(clause):
                    errors.append(f"{prefix}.{field} must appear in clause")
            elif field not in not_applicable:
                errors.append(f"{prefix}.{field} must have a value or be listed in not_applicable")
        if actor:
            if actor_kind == "not-applicable":
                errors.append(f"{prefix}.actor_kind cannot be not-applicable when actor has a value")
            elif clause and not has_marked_phrase(clause, actor, ACTOR_MARKERS):
                errors.append(f"{prefix}.actor must be visible with は/が/も/によって/により")
        elif actor_kind != "not-applicable":
            errors.append(f"{prefix}.actor_kind must be not-applicable when actor is omitted")
        if not actor and any(compact(predicate).endswith(compact(value)) for value in AGENTIVE_PREDICATES):
            errors.append(f"{prefix}: agentive predicate cannot be classified as {kind} without an actor")
    return errors


def validate_label(
    path: Path,
    slide_id: str,
    index: int,
    label: Any,
    *,
    allow_source_heading: bool = False,
) -> list[str]:
    prefix = f"{path}:{slide_id}:semantic_clarity.labels[{index}]"
    if not isinstance(label, dict):
        return [f"{prefix} must be a mapping"]
    errors: list[str] = []
    surface = text(label.get("surface"))
    surface_text = text(label.get("surface_text"))
    reason = text(label.get("reason"))
    if surface not in {"title", "body"}:
        errors.append(f"{prefix}.surface must be title or body; message is always a claim")
    if not surface_text:
        errors.append(f"{prefix}.surface_text is required")
    if len(compact(reason)) < 8:
        errors.append(f"{prefix}.reason must explain why the text is only a label")
    source_heading = label.get("source_heading") is True
    if source_heading and (surface != "title" or not allow_source_heading):
        errors.append(f"{prefix}: source_heading is only valid for a section-faithful title")
    if is_action_like(surface_text) and not source_heading:
        errors.append(f"{prefix}: action-like text cannot be exempted as a label")
    return errors


def validate_slide(path: Path, slide: Any, index: int) -> list[str]:
    if not isinstance(slide, dict):
        return [f"{path}:slides[{index}] must be a mapping"]
    slide_id = text(slide.get("id")) or f"slide-{index}"
    role = text(slide.get("role"))
    scope = text(slide.get("delivery_scope") or "live")
    clarity = slide.get("semantic_clarity")
    if role in EXEMPT_ROLES:
        return []
    if not isinstance(clarity, dict):
        return [f"{path}:{slide_id}: semantic_clarity is required"]

    status = text(clarity.get("status"))
    if status == "exempt":
        reason = text(clarity.get("reason"))
        errors = []
        if scope != "reference":
            errors.append(f"{path}:{slide_id}: only delivery_scope=reference may use semantic_clarity.status=exempt")
        if len(compact(reason)) < 8:
            errors.append(f"{path}:{slide_id}: exempt semantic_clarity requires a concrete reason")
        return errors
    if status != "required":
        return [f"{path}:{slide_id}: semantic_clarity.status must be required or exempt"]

    claims = clarity.get("claims")
    labels = clarity.get("labels")
    errors: list[str] = []
    if not isinstance(claims, list) or not claims:
        errors.append(f"{path}:{slide_id}: semantic_clarity.claims must not be empty")
        claims = []
    if not isinstance(labels, list):
        errors.append(f"{path}:{slide_id}: semantic_clarity.labels must be a list")
        labels = []

    for claim_index, claim in enumerate(claims, 1):
        errors.extend(validate_claim(path, slide_id, claim_index, claim))
    allow_source_heading = bool(slide.get("source_section_ids"))
    for label_index, label in enumerate(labels, 1):
        errors.extend(
            validate_label(
                path,
                slide_id,
                label_index,
                label,
                allow_source_heading=allow_source_heading,
            )
        )

    claim_surfaces = {
        (text(item.get("surface")), compact(item.get("surface_text")))
        for item in claims if isinstance(item, dict)
    }
    label_surfaces = {
        (text(item.get("surface")), compact(item.get("surface_text")))
        for item in labels if isinstance(item, dict)
    }
    title = text(slide.get("title"))
    message = text(slide.get("message"))
    if title and ("title", compact(title)) not in claim_surfaces | label_surfaces:
        errors.append(f"{path}:{slide_id}: title is not accounted for by semantic_clarity claims or labels")
    if message and ("message", compact(message)) not in claim_surfaces:
        errors.append(f"{path}:{slide_id}: message is not accounted for by a semantic_clarity claim")

    for value in body_strings(slide):
        key = ("body", compact(value))
        if is_action_like(value) and key not in claim_surfaces | label_surfaces:
            errors.append(f"{path}:{slide_id}: action-like body text is not accounted for: {value}")

    visible = {compact(value) for value in visible_story_strings(slide)}
    for claim_index, claim in enumerate(claims, 1):
        if isinstance(claim, dict) and compact(claim.get("surface_text")) not in visible:
            errors.append(f"{claim_error_prefix(path, slide_id, claim_index)}.surface_text is not visible in Story")
    for label_index, label in enumerate(labels, 1):
        if isinstance(label, dict) and compact(label.get("surface_text")) not in visible:
            errors.append(f"{path}:{slide_id}:semantic_clarity.labels[{label_index}].surface_text is not visible in Story")
    return errors


def validate_story(path: Path, story: dict) -> list[str]:
    project = story.get("project") or {}
    version = int(project.get("semantic_clarity_version") or 0)
    if version < VERSION:
        return [f"{path}: project.semantic_clarity_version must be {VERSION} or greater"]
    slides = story.get("slides")
    if not isinstance(slides, list):
        return [f"{path}: slides must be a list"]
    errors: list[str] = []
    for index, slide in enumerate(slides, 1):
        errors.extend(validate_slide(path, slide, index))
    return errors


def slide_map(story: dict) -> dict[str, dict]:
    return {
        text(slide.get("id")): slide
        for slide in story.get("slides") or []
        if isinstance(slide, dict) and text(slide.get("id"))
    }


def required_surface_texts(slide: dict) -> list[tuple[str, str]]:
    clarity = slide.get("semantic_clarity") or {}
    return [
        (text(claim.get("surface")), text(claim.get("surface_text")))
        for claim in clarity.get("claims") or []
        if isinstance(claim, dict) and text(claim.get("surface_text"))
    ]


def validate_blueprint(path: Path, blueprint: dict, story: dict) -> list[str]:
    errors: list[str] = []
    blueprint_slides = slide_map(blueprint)
    for slide_id, source in slide_map(story).items():
        if text(source.get("role")) in EXEMPT_ROLES:
            continue
        rendered = blueprint_slides.get(slide_id)
        if rendered is None:
            errors.append(f"{path}:{slide_id}: Blueprint slide is missing")
            continue
        visible = compact(" ".join(flatten_strings({
            "title": rendered.get("title"),
            "message": rendered.get("message"),
            "text": rendered.get("text") or {},
            "content_model": rendered_content_model(rendered.get("content_model")),
            "annotations": (rendered.get("visual") or {}).get("annotations") or [],
        })))
        for surface, value in required_surface_texts(source):
            if compact(value) not in visible:
                errors.append(f"{path}:{slide_id}: {surface} clarity text is missing from Blueprint: {value}")
    return errors


class SlideParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.slides: dict[str, str] = {}
        self.current_id: str | None = None
        self.depth = 0
        self.skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "section" and "slide" in values.get("class", "").split() and self.current_id is None:
            self.current_id = values.get("data-slide-id") or ""
            self.depth = 1
            self.parts = []
            return
        if self.current_id is not None:
            if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
                self.depth += 1
            if tag in {"script", "style"}:
                self.skip += 1

    def handle_endtag(self, tag: str) -> None:
        if self.current_id is None:
            return
        if tag in {"script", "style"} and self.skip:
            self.skip -= 1
        self.depth -= 1
        if self.depth == 0:
            if self.current_id:
                self.slides[self.current_id] = " ".join(self.parts)
            self.current_id = None
            self.parts = []

    def handle_data(self, data: str) -> None:
        if self.current_id is not None and not self.skip and data.strip():
            self.parts.append(data.strip())


def validate_html(path: Path, html: str, story: dict) -> list[str]:
    parser = SlideParser()
    parser.feed(html)
    errors: list[str] = []
    for slide_id, source in slide_map(story).items():
        if text(source.get("role")) in EXEMPT_ROLES:
            continue
        visible = parser.slides.get(slide_id)
        if visible is None:
            errors.append(f"{path}:{slide_id}: HTML slide is missing")
            continue
        normalized = compact(visible)
        for surface, value in required_surface_texts(source):
            if compact(value) not in normalized:
                errors.append(f"{path}:{slide_id}: {surface} clarity text is missing from HTML: {value}")
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
    parser = argparse.ArgumentParser(description="可視文の主語・行為者・変更対象・述語を検証する")
    parser.add_argument("--story", required=True, type=Path)
    parser.add_argument("--blueprint", type=Path)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()

    try:
        errors, stories = load_stories(args.story.resolve())
    except (OSError, yaml.YAMLError, ValueError) as exc:
        print(f"ERROR: story を読めません: {exc}")
        return 1
    for story_path, story in stories:
        errors.extend(validate_story(story_path, story))
    if (args.blueprint or args.html) and len(stories) != 1:
        errors.append("--blueprint and --html require a single part Story")
    elif stories:
        _, story = stories[0]
        if args.blueprint:
            try:
                errors.extend(validate_blueprint(args.blueprint.resolve(), load(args.blueprint.resolve()), story))
            except (OSError, yaml.YAMLError) as exc:
                errors.append(f"blueprint を読めません: {exc}")
        if args.html:
            try:
                errors.extend(validate_html(args.html.resolve(), args.html.read_text(encoding="utf-8"), story))
            except OSError as exc:
                errors.append(f"HTMLを読めません: {exc}")
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print(f"OK: {len(stories)}件の主語・行為者・変更対象契約を検証しました")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
