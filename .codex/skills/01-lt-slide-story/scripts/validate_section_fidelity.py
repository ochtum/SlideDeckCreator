#!/usr/bin/env python3
"""Build and validate section-faithful article-to-slide traceability."""

from __future__ import annotations

import argparse
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
from math import ceil
from pathlib import Path
import re
from typing import Any

import yaml


AUTHORING_MODE = "section-faithful"
COVERAGE_MODES = {"full", "abridged", "appendix", "reference"}
POINT_IMPORTANCE = {"essential", "supporting", "reference"}
EXEMPT_SYNTHETIC_ROLES = {"profile", "goal", "roadmap", "recap", "thanks"}


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


def slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return result or "article"


def relpath(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def clean_heading(value: str) -> str:
    result = unescape(re.sub(r"<[^>]+>", "", value))
    result = re.sub(r"^[\s🔷🔹💡❓✅▸▶︎▶]+", "", result)
    return re.sub(r"\s+", " ", result).strip()


def prose_text(lines: list[str]) -> str:
    output: list[str] = []
    fenced = False
    for line in lines:
        if re.match(r"^\s*```", line):
            fenced = not fenced
            continue
        if fenced:
            continue
        if re.match(r"^\s*\|.*\|\s*$", line):
            continue
        value = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", line)
        value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
        value = re.sub(r"<[^>]+>", "", value)
        value = re.sub(r"^[\s>*+-]+", "", value)
        value = re.sub(r"[*_`#]", "", value)
        if value.strip():
            output.append(value.strip())
    return "\n".join(output)


def asset_kinds(lines: list[str]) -> list[str]:
    kinds: set[str] = set()
    fenced = False
    language = ""
    for index, line in enumerate(lines):
        fence = re.match(r"^\s*```\s*([\w.+-]*)", line)
        if fence:
            if not fenced:
                fenced = True
                language = fence.group(1).casefold()
                if language == "mermaid":
                    kinds.add("mermaid")
                elif language in {"yaml", "yml", "json", "toml", "ini", "xml", "env"}:
                    kinds.add("config")
                else:
                    kinds.add("code")
            else:
                fenced = False
                language = ""
            continue
        if fenced:
            continue
        if re.search(r"!\[[^\]]*\]\([^)]*\)", line):
            kinds.add("image")
        if re.match(r"^\s*[-*]\s+\[[ xX]\]\s+", line):
            kinds.add("checklist")
        if (
            re.match(r"^\s*\|.*\|\s*$", line)
            and index + 1 < len(lines)
            and re.match(r"^\s*\|?\s*:?-{3,}", lines[index + 1])
        ):
            kinds.add("table")
    return sorted(kinds)


def extract_sections(path: Path, root: Path) -> list[dict[str, Any]]:
    source_text = path.read_text(encoding="utf-8-sig")
    lines = source_text.splitlines()
    headings: list[tuple[int, int, str]] = []
    fenced = False
    for index, line in enumerate(lines):
        if re.match(r"^\s*```", line):
            fenced = not fenced
            continue
        if fenced:
            continue
        match = re.match(r"^(#{1,4})\s+(.+?)\s*$", line)
        if match:
            headings.append((index, len(match.group(1)), match.group(2)))

    source = relpath(path, root)
    prefix = f"{slug(path.stem)[:28]}-{sha256(source.encode('utf-8')).hexdigest()[:6]}"
    sections: list[dict[str, Any]] = []
    for order, (start, level, raw_heading) in enumerate(headings, 1):
        end = headings[order][0] - 1 if order < len(headings) else len(lines) - 1
        body = lines[start + 1 : end + 1]
        prose = prose_text(body)
        assets = asset_kinds(body)
        heading = clean_heading(raw_heading)
        if order == 1 and level == 1:
            kind = "document-title"
        elif re.search(r"(?:参考資料|references?)", heading, re.IGNORECASE):
            kind = "reference"
        elif prose or assets:
            kind = "content"
        else:
            kind = "structural"
        chars = len(re.sub(r"\s+", "", prose))
        sections.append({
            "id": f"{prefix}-section-{order:03d}",
            "source": source,
            "order": order,
            "heading_level": level,
            "heading": heading,
            "heading_raw": raw_heading,
            "line_start": start + 1,
            "line_end": end + 1,
            "kind": kind,
            "char_count": chars,
            "source_read_seconds": ceil(chars / 5.5) if chars else 0,
            "asset_kinds": assets,
            "body_sha256": sha256("\n".join(body).encode("utf-8")).hexdigest(),
        })
    return sections


def build_manifest(sources: list[Path], root: Path) -> dict[str, Any]:
    resolved = [source.resolve() for source in sources]
    return {
        "schema_version": 1,
        "kind": "lt-source-sections",
        "speech_estimate": {
            "chars_per_second": 5.5,
            "usage": "feasibility-warning-only",
        },
        "sources": [
            {"path": relpath(source, root), "sha256": sha256(source.read_bytes()).hexdigest()}
            for source in resolved
        ],
        "sections": [section for source in resolved for section in extract_sections(source, root)],
    }


def rendered_content_model(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        key: value.get(key)
        for key in ("data", "focus", "highlight")
        if value.get(key) not in (None, "", [], {})
    }


def story_visible_strings(slide: dict[str, Any]) -> list[str]:
    return flatten_strings({
        "title": slide.get("title"),
        "message": slide.get("message"),
        "support": slide.get("support") or [],
        "information_layers": slide.get("information_layers") or {},
        "content_model": rendered_content_model(slide.get("content_model")),
    })


def blueprint_visible_strings(slide: dict[str, Any]) -> list[str]:
    return flatten_strings({
        "title": slide.get("title"),
        "message": slide.get("message"),
        "text": slide.get("text") or {},
        "content_model": rendered_content_model(slide.get("content_model")),
        "annotations": (slide.get("visual") or {}).get("annotations") or [],
    })


def note_talking_content(note: Any) -> str:
    for line in text(note).splitlines():
        match = re.match(r"^\s*話す内容\s*[:：]\s*(.*?)\s*$", line)
        if match:
            return match.group(1)
    return ""


def slide_map(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        text(slide.get("id")): slide
        for slide in data.get("slides") or []
        if isinstance(slide, dict) and text(slide.get("id"))
    }


def omission_map(story: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in story.get("approved_omissions") or []:
        if not isinstance(item, dict):
            continue
        section_id = text(item.get("section_id") or item.get("unit_id"))
        if section_id:
            result[section_id] = item
    return result


def validate_story(path: Path, manifest: dict[str, Any], story: dict[str, Any]) -> list[str]:
    if text((story.get("project") or {}).get("authoring_mode")) != AUTHORING_MODE:
        return []

    errors: list[str] = []
    sections = {
        text(section.get("id")): section
        for section in manifest.get("sections") or []
        if isinstance(section, dict) and text(section.get("id"))
    }
    if not sections:
        return [f"{path}: section-faithful requires a non-empty source section manifest"]

    scope = [text(value) for value in story.get("section_scope") or [] if text(value)]
    if scope:
        unknown_scope = sorted(set(scope) - set(sections))
        if unknown_scope:
            errors.append(f"{path}: section_scope contains unknown sections: {unknown_scope}")
        expected_ids = [section_id for section_id in sections if section_id in set(scope)]
    else:
        expected_ids = list(sections)

    coverage_items = story.get("section_coverage")
    if not isinstance(coverage_items, list):
        return errors + [f"{path}: section_coverage must be a list in section-faithful mode"]
    coverage = {
        text(item.get("section_id")): item
        for item in coverage_items
        if isinstance(item, dict) and text(item.get("section_id"))
    }
    omissions = omission_map(story)
    slides = slide_map(story)
    slide_positions = {slide_id: index for index, slide_id in enumerate(slides)}
    point_owners: dict[str, str] = {}
    first_positions: list[tuple[str, int]] = []

    for section_id in expected_ids:
        section = sections[section_id]
        if section_id in omissions:
            if len(compact(omissions[section_id].get("reason"))) < 8:
                errors.append(f"{path}:{section_id}: approved omission requires a concrete reason")
            continue
        item = coverage.get(section_id)
        if not item:
            errors.append(f"{path}:{section_id}: section coverage is missing")
            continue
        mode = text(item.get("coverage"))
        if mode not in COVERAGE_MODES:
            errors.append(f"{path}:{section_id}: coverage must be one of {sorted(COVERAGE_MODES)}")
        if mode == "abridged" and len(compact(item.get("abridgement_note"))) < 8:
            errors.append(f"{path}:{section_id}: abridged coverage requires abridgement_note")
        slide_ids = [text(value) for value in item.get("slide_ids") or [] if text(value)]
        if not slide_ids:
            errors.append(f"{path}:{section_id}: slide_ids must not be empty")
            continue
        if len(slide_ids) > 1 and len(compact(item.get("split_reason"))) < 8:
            errors.append(f"{path}:{section_id}: one section split across slides requires split_reason")
        missing_slides = [slide_id for slide_id in slide_ids if slide_id not in slides]
        if missing_slides:
            errors.append(f"{path}:{section_id}: unknown slide_ids: {missing_slides}")
            continue
        first_positions.append((section_id, min(slide_positions[slide_id] for slide_id in slide_ids)))

        points = item.get("points")
        if not isinstance(points, list) or not points:
            errors.append(f"{path}:{section_id}: points must not be empty")
            points = []
        point_ids: set[str] = set()
        for point in points:
            if not isinstance(point, dict):
                errors.append(f"{path}:{section_id}: every point must be a mapping")
                continue
            point_id = text(point.get("id"))
            if not point_id:
                errors.append(f"{path}:{section_id}: point.id is required")
                continue
            if point_id in point_owners:
                errors.append(f"{path}:{point_id}: point id duplicates {point_owners[point_id]}")
            point_owners[point_id] = section_id
            point_ids.add(point_id)
            if len(compact(point.get("text"))) < 4:
                errors.append(f"{path}:{point_id}: point.text must be concrete")
            if text(point.get("importance")) not in POINT_IMPORTANCE:
                errors.append(f"{path}:{point_id}: importance must be one of {sorted(POINT_IMPORTANCE)}")

        covered_points: set[str] = set()
        for slide_id in slide_ids:
            slide = slides[slide_id]
            source_ids = [text(value) for value in slide.get("source_section_ids") or [] if text(value)]
            if source_ids != [section_id]:
                errors.append(f"{path}:{slide_id}: source_section_ids must contain only {section_id}")
            expected_scope = "reference" if mode == "reference" else ("appendix" if mode == "appendix" else None)
            if expected_scope and text(slide.get("delivery_scope")) != expected_scope:
                errors.append(f"{path}:{slide_id}: delivery_scope must be {expected_scope} for {mode} coverage")

            track = slide.get("talk_track")
            if not isinstance(track, dict):
                errors.append(f"{path}:{slide_id}: talk_track is required")
                continue
            if text(track.get("source_section_id")) != section_id:
                errors.append(f"{path}:{slide_id}: talk_track.source_section_id must be {section_id}")
            beats = track.get("beats")
            if not isinstance(beats, list) or not beats:
                errors.append(f"{path}:{slide_id}: talk_track.beats must not be empty")
                continue
            script = text((slide.get("speaker_cue") or {}).get("script"))
            note_content = note_talking_content(slide.get("spoken_note"))
            visible = compact(" ".join(story_visible_strings(slide)))
            visible_count = 0
            for beat_index, beat in enumerate(beats, 1):
                if not isinstance(beat, dict):
                    errors.append(f"{path}:{slide_id}:beats[{beat_index}] must be a mapping")
                    continue
                point_id = text(beat.get("point_id"))
                spoken_text = text(beat.get("spoken_text"))
                visible_text = text(beat.get("visible_text"))
                if point_id not in point_ids:
                    errors.append(f"{path}:{slide_id}:beats[{beat_index}].point_id is not declared by {section_id}")
                else:
                    covered_points.add(point_id)
                if len(compact(spoken_text)) < 8:
                    errors.append(f"{path}:{slide_id}:beats[{beat_index}].spoken_text must be concrete")
                elif compact(spoken_text) not in compact(script):
                    errors.append(f"{path}:{slide_id}:beats[{beat_index}].spoken_text is missing from speaker_cue.script")
                elif compact(spoken_text) not in compact(note_content):
                    errors.append(f"{path}:{slide_id}:beats[{beat_index}].spoken_text is missing from spoken_note 話す内容")
                if visible_text:
                    visible_count += 1
                    if compact(visible_text) not in visible:
                        errors.append(f"{path}:{slide_id}:beats[{beat_index}].visible_text is not visible in Story: {visible_text}")
            if text(slide.get("role")) not in EXEMPT_SYNTHETIC_ROLES and visible_count == 0:
                errors.append(f"{path}:{slide_id}: at least one talk_track beat requires visible_text")
        missing_points = sorted(point_ids - covered_points)
        if missing_points:
            errors.append(f"{path}:{section_id}: points are missing from talk_track beats: {missing_points}")

    unknown_coverage = sorted(set(coverage) - set(expected_ids))
    if unknown_coverage:
        errors.append(f"{path}: section_coverage references out-of-scope sections: {unknown_coverage}")

    ordered_positions = [position for _, position in first_positions]
    if ordered_positions != sorted(ordered_positions):
        errors.append(f"{path}: source section slide order must match the manifest order")

    coverage_slide_ids = {
        text(slide_id)
        for item in coverage.values()
        for slide_id in item.get("slide_ids") or []
        if text(slide_id)
    }
    for slide_id, slide in slides.items():
        source_ids = [text(value) for value in slide.get("source_section_ids") or [] if text(value)]
        if len(source_ids) > 1:
            errors.append(f"{path}:{slide_id}: a slide cannot merge multiple source sections")
        if source_ids and slide_id not in coverage_slide_ids:
            errors.append(f"{path}:{slide_id}: source_section_ids is not declared by section_coverage")
    return errors


def validate_blueprint(path: Path, blueprint: dict[str, Any], story: dict[str, Any]) -> list[str]:
    if text((story.get("project") or {}).get("authoring_mode")) != AUTHORING_MODE:
        return []
    errors: list[str] = []
    story_slides = slide_map(story)
    blueprint_slides = slide_map(blueprint)
    for slide_id, source in story_slides.items():
        source_ids = [text(value) for value in source.get("source_section_ids") or [] if text(value)]
        if not source_ids:
            continue
        rendered = blueprint_slides.get(slide_id)
        if not rendered:
            errors.append(f"{path}:{slide_id}: Blueprint slide is missing")
            continue
        if rendered.get("source_section_ids") != source.get("source_section_ids"):
            errors.append(f"{path}:{slide_id}: source_section_ids must be copied unchanged")
        if rendered.get("talk_track") != source.get("talk_track"):
            errors.append(f"{path}:{slide_id}: talk_track must be copied unchanged")
        visible = compact(" ".join(blueprint_visible_strings(rendered)))
        for beat in (source.get("talk_track") or {}).get("beats") or []:
            visible_text = text(beat.get("visible_text")) if isinstance(beat, dict) else ""
            if visible_text and compact(visible_text) not in visible:
                errors.append(f"{path}:{slide_id}: talk_track visible_text is not rendered by Blueprint: {visible_text}")
    return errors


class SlideHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.slides: dict[str, dict[str, Any]] = {}
        self.current_id: str | None = None
        self.depth = 0
        self.skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "section" and "slide" in values.get("class", "").split() and self.current_id is None:
            self.current_id = values.get("data-slide-id") or ""
            self.depth = 1
            self.skip = 0
            self.parts = []
            self.slides[self.current_id] = {
                "source_section_ids": values.get("data-source-section-ids", "").split(),
                "text": "",
            }
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
            self.slides[self.current_id]["text"] = " ".join(self.parts)
            self.current_id = None
            self.parts = []

    def handle_data(self, data: str) -> None:
        if self.current_id is not None and not self.skip and data.strip():
            self.parts.append(data.strip())


def validate_html(path: Path, html: str, story: dict[str, Any]) -> list[str]:
    if text((story.get("project") or {}).get("authoring_mode")) != AUTHORING_MODE:
        return []
    parser = SlideHTMLParser()
    parser.feed(html)
    errors: list[str] = []
    for slide_id, source in slide_map(story).items():
        source_ids = [text(value) for value in source.get("source_section_ids") or [] if text(value)]
        if not source_ids:
            continue
        rendered = parser.slides.get(slide_id)
        if not rendered:
            errors.append(f"{path}:{slide_id}: HTML slide is missing")
            continue
        if rendered["source_section_ids"] != source_ids:
            errors.append(f"{path}:{slide_id}: data-source-section-ids must match Story")
        visible = compact(rendered["text"])
        for beat in (source.get("talk_track") or {}).get("beats") or []:
            visible_text = text(beat.get("visible_text")) if isinstance(beat, dict) else ""
            if visible_text and compact(visible_text) not in visible:
                errors.append(f"{path}:{slide_id}: talk_track visible_text is missing from HTML: {visible_text}")
    return errors


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def main() -> int:
    parser = argparse.ArgumentParser(description="記事セクション、Spoken Note、可視スライドの一対一対応を検証する")
    parser.add_argument("--source", action="append", type=Path, default=[])
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--manifest-out", type=Path)
    parser.add_argument("--story", type=Path)
    parser.add_argument("--blueprint", type=Path)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()

    try:
        if args.manifest:
            manifest = load(args.manifest.resolve())
        elif args.source:
            manifest = build_manifest([source.resolve() for source in args.source], Path.cwd())
        else:
            parser.error("--source or --manifest is required")
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        print(f"ERROR: source section manifestを読めません: {exc}")
        return 1

    if args.manifest_out:
        args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
        args.manifest_out.write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False, width=120),
            encoding="utf-8",
        )

    errors: list[str] = []
    if args.story:
        try:
            story = load(args.story.resolve())
            if story.get("kind") == "lt-slide-series":
                if args.blueprint or args.html:
                    errors.append("series manifest cannot be combined with --blueprint or --html; validate each part")
                assigned: list[str] = []
                for part in story.get("parts") or []:
                    if not isinstance(part, dict) or not text(part.get("story_file")):
                        errors.append(f"{args.story}: every series part requires story_file")
                        continue
                    child_path = (args.story.resolve().parent / text(part.get("story_file"))).resolve()
                    child = load(child_path)
                    if text((child.get("project") or {}).get("authoring_mode")) != AUTHORING_MODE:
                        errors.append(f"{child_path}: series part must use {AUTHORING_MODE}")
                        continue
                    scope = [text(value) for value in child.get("section_scope") or [] if text(value)]
                    if not scope:
                        errors.append(f"{child_path}: series part requires non-empty section_scope")
                    assigned.extend(scope)
                    errors.extend(validate_story(child_path, manifest, child))
                duplicates = sorted({value for value in assigned if assigned.count(value) > 1})
                if duplicates:
                    errors.append(f"{args.story}: section_scope overlaps across parts: {duplicates}")
                all_sections = [text(item.get("id")) for item in manifest.get("sections") or [] if text(item.get("id"))]
                omitted = set(omission_map(story))
                missing = sorted(set(all_sections) - set(assigned) - omitted)
                if missing:
                    errors.append(f"{args.story}: source sections are not assigned to any part: {missing}")
            else:
                errors.extend(validate_story(args.story.resolve(), manifest, story))
                if args.blueprint:
                    errors.extend(validate_blueprint(args.blueprint.resolve(), load(args.blueprint.resolve()), story))
                if args.html:
                    errors.extend(validate_html(args.html.resolve(), args.html.read_text(encoding="utf-8"), story))
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            errors.append(f"Story/Blueprint/HTMLを読めません: {exc}")
    elif args.blueprint or args.html:
        errors.append("--blueprint and --html require --story")

    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print(f"OK: {len(manifest.get('sections') or [])} source sections inventoried and validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
