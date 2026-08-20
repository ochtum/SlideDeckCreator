#!/usr/bin/env python3
"""Validate the durable slide-style profile used by the LT skill pipeline."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_HEADINGS = (
    "Metadata",
    "Presenter Stance",
    "Narrative Patterns",
    "Heading And Voice",
    "Emotional Beats",
    "Failure And Success",
    "Evidence And Specificity",
    "Visual Composition",
    "Speaker Notes",
    "Reusable Patterns",
    "Application Limits",
    "Evidence Sources",
)
ALLOWED_STRENGTHS = {"MUST", "SHOULD", "MAY", "MUST NOT"}
ABSOLUTE_SLIDE_COUNT_FIELDS = (
    "target_slide_count",
    "minimum_slide_count",
    "minimum_body_slides",
    "min_body_slides",
    "slide_count_floor",
)


def section(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$([\s\S]*?)(?=^## |\Z)", text, re.MULTILINE
    )
    return match.group(1) if match else ""


def field_values(text: str, field: str) -> list[str]:
    return re.findall(rf"^\s*(?:-\s+)?{re.escape(field)}:\s*(.+?)\s*$", text, re.MULTILINE)


def absolute_slide_count_rules(limits: str) -> list[str]:
    """Return total/body slide-count rules that do not belong in a style profile."""
    findings: list[str] = []
    field_pattern = "|".join(re.escape(field) for field in ABSOLUTE_SLIDE_COUNT_FIELDS)
    if re.search(rf"^\s*(?:-\s+)?(?:{field_pattern})\s*:", limits, re.MULTILINE | re.IGNORECASE):
        findings.append("absolute slide-count field")
    prose_patterns = (
        r"(?:本文|本編|各回|各パート|デッキ全体|スライド総数|総ページ数)[^\n]{0,40}\d+\s*枚\s*(?:以上|以下|を下限|を上限|を目標|に固定)",
        r"\d+\s*枚\s*(?:以上|以下|を下限|を上限|を目標|に固定)[^\n]{0,40}(?:本文|本編|各回|各パート|デッキ全体|スライド総数|総ページ数)",
    )
    if any(re.search(pattern, limits) for pattern in prose_patterns):
        findings.append("absolute total/body slide-count prose")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", type=Path)
    args = parser.parse_args()
    errors: list[str] = []

    if not args.profile.is_file():
        print(f"ERROR: profile not found: {args.profile}")
        return 1

    text = args.profile.read_text(encoding="utf-8")
    if not re.search(r"^# LT Slide Style Profile\s*$", text, re.MULTILINE):
        errors.append("missing H1 '# LT Slide Style Profile'")
    for heading in REQUIRED_HEADINGS:
        if not re.search(rf"^## {re.escape(heading)}\s*$", text, re.MULTILINE):
            errors.append(f"missing required section: {heading}")

    metadata = section(text, "Metadata")
    for key in ("profile_version", "updated_at", "evidence_count", "status"):
        if not re.search(rf"^\s*-?\s*{key}:\s*\S+", metadata, re.MULTILINE):
            errors.append(f"Metadata is missing '{key}'")

    evidence_count_match = re.search(r"^\s*-?\s*evidence_count:\s*(\d+)\s*$", metadata, re.MULTILINE)
    status_match = re.search(r"^\s*-?\s*status:\s*(\S+)\s*$", metadata, re.MULTILINE)
    source_ids = re.findall(r"^\s*-\s+id:\s*([^\s#]+)", section(text, "Evidence Sources"), re.MULTILINE)
    if len(set(source_ids)) < 3:
        errors.append("Evidence Sources must contain at least three distinct '- id:' entries")
    if evidence_count_match and int(evidence_count_match.group(1)) != len(set(source_ids)):
        errors.append("Metadata evidence_count does not match distinct Evidence Sources IDs")
    if status_match and status_match.group(1) not in {"confirmed", "draft"}:
        errors.append("Metadata status must be 'confirmed' or 'draft'")
    if status_match and status_match.group(1) == "confirmed" and len(set(source_ids)) < 3:
        errors.append("confirmed profiles require at least three evidence sources")

    patterns = section(text, "Reusable Patterns")
    ids = field_values(patterns, "id")
    if len(ids) < 3:
        errors.append("Reusable Patterns must contain at least three 'id:' rules")
    if len(ids) != len(set(ids)):
        errors.append("Reusable Patterns contain duplicate rule IDs")
    strengths = field_values(patterns, "strength")
    if not strengths:
        errors.append("Reusable Patterns contain no strength fields")
    for strength in strengths:
        if strength not in ALLOWED_STRENGTHS:
            errors.append(f"unsupported strength: {strength}")
    for required_field in ("role", "applies_when", "guidance", "limits", "evidence"):
        if not field_values(patterns, required_field):
            errors.append(f"Reusable Patterns are missing '{required_field}:'")
    if "MUST NOT" not in strengths:
        errors.append("include at least one MUST NOT rule to prevent over-application")
    if "MUST" in strengths and len(set(source_ids)) < 3:
        errors.append("MUST rules require at least three evidence sources")

    limits = section(text, "Application Limits")
    if not re.search(r"(連続|上限|最大|頻度)", limits) or not re.search(r"(捏造|作らない|追加しない)", limits):
        errors.append("Application Limits must state frequency and fact-invention limits")
    if not re.search(r"^duration_evidence:\s*$", limits, re.MULTILINE):
        errors.append("Application Limits must include duration_evidence")
    if not re.search(r"^\s+long_form_density_source:\s*(quality-default|observed-long-form)\s*$", limits, re.MULTILINE):
        errors.append("duration_evidence must declare long_form_density_source")
    if absolute_slide_count_rules(limits):
        errors.append(
            "Application Limits must not set an absolute total/body slide-count floor, target, or fixed value; "
            "record observed counts in Evidence Sources and let 01 derive target_slide_count from content"
        )

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: {args.profile} ({len(set(source_ids))} evidence sources, {len(ids)} reusable rules)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
