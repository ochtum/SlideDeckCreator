#!/usr/bin/env python3
"""Inventory Markdown learning units and validate full-equivalence traceability."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
import re
from typing import Any

import yaml


STRUCTURED_KINDS = {"table", "code", "config", "mermaid", "image", "checklist"}
STRUCTURE_PRESERVATION = {"structure-preserved", "exact", "reconstructed"}
SECTION_PRESERVATION = STRUCTURE_PRESERVATION | {"explain", "example-preserved"}


@dataclass
class Unit:
    id: str
    source: str
    kind: str
    line_start: int
    line_end: int
    title: str
    summary_seed: str


def compact(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return result or "source"


def relpath(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def block_end(lines: list[str], start: int, predicate) -> int:
    index = start
    while index + 1 < len(lines) and predicate(lines[index + 1]):
        index += 1
    return index


def inventory_source(path: Path, root: Path) -> list[Unit]:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    source = relpath(path, root)
    prefix = f"{slug(path.stem)[:30]}-{sha256(source.encode('utf-8')).hexdigest()[:6]}"
    counters: Counter[str] = Counter()
    units: list[Unit] = []

    def add(kind: str, start: int, end: int, title: str, seed: str) -> None:
        counters[kind] += 1
        units.append(Unit(
            id=f"{prefix}-{kind}-{counters[kind]:03d}",
            source=source,
            kind=kind,
            line_start=start + 1,
            line_end=end + 1,
            title=compact(title)[:160],
            summary_seed=compact(seed)[:360],
        ))

    index = 0
    while index < len(lines):
        line = lines[index]
        fence = re.match(r"^\s*```\s*([\w.+-]*)", line)
        if fence:
            end = index + 1
            while end < len(lines) and not re.match(r"^\s*```\s*$", lines[end]):
                end += 1
            end = min(end, len(lines) - 1)
            language = fence.group(1).casefold()
            kind = "mermaid" if language == "mermaid" else ("config" if language in {"yaml", "yml", "json", "toml", "ini", "xml", "env"} else "code")
            body = " ".join(lines[index + 1:end])
            add(kind, index, end, language or kind, body)
            index = end + 1
            continue

        heading = re.match(r"^(#{2,4})\s+(.+?)\s*$", line)
        if heading:
            level = len(heading.group(1))
            end = index
            seed_lines: list[str] = []
            cursor = index + 1
            while cursor < len(lines):
                next_heading = re.match(r"^(#{1,4})\s+", lines[cursor])
                if next_heading and len(next_heading.group(1)) <= level:
                    break
                candidate = compact(lines[cursor])
                if candidate and not candidate.startswith(("```", "|", "![")):
                    seed_lines.append(candidate)
                end = cursor
                cursor += 1
            add("section", index, end, heading.group(2), " ".join(seed_lines[:4]))
            index += 1
            continue

        if re.match(r"^\s*\|.*\|\s*$", line) and index + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{3,}", lines[index + 1]):
            end = block_end(lines, index, lambda value: bool(re.match(r"^\s*\|.*\|\s*$", value)))
            add("table", index, end, "Markdown table", " ".join(lines[index:end + 1]))
            index = end + 1
            continue

        image = re.search(r"!\[([^\]]*)\]\(([^)]+)\)", line)
        if image:
            add("image", index, index, image.group(1) or "image", image.group(2))
            index += 1
            continue

        if re.match(r"^\s*[-*]\s+\[[ xX]\]\s+", line):
            end = block_end(lines, index, lambda value: bool(re.match(r"^\s*[-*]\s+\[[ xX]\]\s+", value)))
            add("checklist", index, end, "Checklist", " ".join(lines[index:end + 1]))
            index = end + 1
            continue
        index += 1
    return units


def build_inventory(sources: list[Path], root: Path) -> dict[str, Any]:
    units = [unit for source in sources for unit in inventory_source(source, root)]
    counts = Counter(unit.kind for unit in units)
    return {
        "schema_version": 1,
        "kind": "lt-source-inventory",
        "sources": [
            {
                "path": relpath(path, root),
                "sha256": sha256(path.read_bytes()).hexdigest(),
            }
            for path in sources
        ],
        "counts": dict(sorted(counts.items())),
        "units": [asdict(unit) for unit in units],
    }


class SlideHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.source_units: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "section":
            return
        values = {key: value or "" for key, value in attrs}
        if "slide" not in values.get("class", "").split():
            return
        self.source_units.update(values.get("data-source-unit-ids", "").split())


def load_html_units(paths: list[Path]) -> set[str]:
    result: set[str] = set()
    for path in paths:
        parser = SlideHTMLParser()
        parser.feed(path.read_text(encoding="utf-8"))
        result.update(parser.source_units)
    return result


def validate(inventory: dict[str, Any], story: dict[str, Any], html_paths: list[Path], require_full: bool) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    fidelity = compact((story.get("project") or {}).get("content_fidelity"))
    if require_full and fidelity != "full-equivalence":
        errors.append("project.content_fidelity must be full-equivalence for an all-content request")
    if fidelity != "full-equivalence" and not require_full:
        return errors, {"fidelity": fidelity or "unspecified", "checked_units": 0, "missing_units": []}

    units = {unit["id"]: unit for unit in inventory.get("units") or []}
    matrix = story.get("coverage_matrix")
    if not isinstance(matrix, list):
        matrix = []
        errors.append("coverage_matrix must be a list")
    by_id = {compact(item.get("unit_id")): item for item in matrix if isinstance(item, dict)}
    omissions = {compact(item.get("unit_id")) for item in (story.get("approved_omissions") or []) if isinstance(item, dict)}
    html_units = load_html_units(html_paths) if html_paths else set()
    missing: list[str] = []

    for unit_id, unit in units.items():
        item = by_id.get(unit_id)
        if unit_id in omissions:
            continue
        if not item:
            errors.append(f"{unit_id}: coverage is missing")
            missing.append(unit_id)
            continue
        if compact(item.get("status")) != "covered":
            errors.append(f"{unit_id}: status must be covered")
        if not item.get("parts") or not item.get("slide_ids"):
            errors.append(f"{unit_id}: parts and slide_ids are required")
        preservation = compact(item.get("preservation"))
        allowed = STRUCTURE_PRESERVATION if unit.get("kind") in STRUCTURED_KINDS else SECTION_PRESERVATION
        if preservation not in allowed:
            errors.append(f"{unit_id}: preservation '{preservation}' does not preserve {unit.get('kind')}")
        if unit.get("kind") in STRUCTURED_KINDS and not item.get("artifact_ids"):
            errors.append(f"{unit_id}: structured source requires artifact_ids")
        if html_paths and unit_id not in html_units:
            errors.append(f"{unit_id}: not traceable from HTML data-source-unit-ids")

    unknown = sorted(set(by_id) - set(units))
    for unit_id in unknown:
        errors.append(f"{unit_id}: coverage references an unknown inventory unit")
    return errors, {
        "fidelity": fidelity or "unspecified",
        "checked_units": len(units),
        "covered_units": len(units) - len(missing),
        "missing_units": missing,
        "html_traced_units": len(html_units & set(units)),
    }


def write_report(path: Path, inventory: dict[str, Any], result: dict[str, Any], errors: list[str]) -> None:
    lines = [
        "# 入力内容同等性レポート",
        "",
        f"- 判定: {'不合格' if errors else '合格'}",
        f"- content fidelity: {result.get('fidelity')}",
        f"- 入力unit数: {len(inventory.get('units') or [])}",
        f"- coverage済み: {result.get('covered_units', 0)}",
        f"- HTMLから逆引き可能: {result.get('html_traced_units', 0)}",
        "- 種別: " + ", ".join(f"{key}={value}" for key, value in (inventory.get("counts") or {}).items()),
        "",
        "## Findings",
        "",
    ]
    lines.extend([f"- {error}" for error in errors] or ["- なし"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="入力資料の学習単位台帳とfull-equivalence追跡を検証する")
    parser.add_argument("--source", action="append", type=Path, default=[])
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--inventory-out", type=Path)
    parser.add_argument("--story", type=Path)
    parser.add_argument("--html", action="append", type=Path, default=[])
    parser.add_argument("--report", type=Path)
    parser.add_argument("--require-full-equivalence", action="store_true")
    args = parser.parse_args()

    root = Path.cwd()
    if args.inventory:
        inventory = yaml.safe_load(args.inventory.read_text(encoding="utf-8")) or {}
    elif args.source:
        inventory = build_inventory([path.resolve() for path in args.source], root)
    else:
        parser.error("--source or --inventory is required")

    if args.inventory_out:
        args.inventory_out.parent.mkdir(parents=True, exist_ok=True)
        args.inventory_out.write_text(yaml.safe_dump(inventory, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")

    errors: list[str] = []
    result = {"fidelity": "inventory-only", "covered_units": 0, "html_traced_units": 0}
    if args.story:
        story = yaml.safe_load(args.story.read_text(encoding="utf-8")) or {}
        result_errors, result = validate(inventory, story, [path.resolve() for path in args.html], args.require_full_equivalence)
        errors.extend(result_errors)
    if args.report:
        write_report(args.report, inventory, result, errors)
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print(f"OK: {len(inventory.get('units') or [])} source units inventoried; fidelity={result.get('fidelity')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
