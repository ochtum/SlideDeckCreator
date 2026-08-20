#!/usr/bin/env python3
"""Validate that required visual plans resolve into a blueprint implementation."""
import argparse
from pathlib import Path
import yaml

HTML_IMPLEMENTATIONS = {"inline-svg", "html-table", "html-code"}
ASSET_IMPLEMENTATIONS = {"provided-image", "generated-image"}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--story", required=True, type=Path)
    parser.add_argument("--blueprint", required=True, type=Path)
    args = parser.parse_args()
    story = yaml.safe_load(args.story.read_text(encoding="utf-8")) or {}
    blueprint = yaml.safe_load(args.blueprint.read_text(encoding="utf-8")) or {}
    plans = story.get("visual_plan", [])
    slides = {slide.get("id"): slide for slide in blueprint.get("slides", [])}
    assets = blueprint.get("visual_assets", [])
    errors = []
    for plan in plans:
        if plan.get("need") != "required":
            continue
        slide = slides.get(plan.get("slide_id"))
        if not slide:
            errors.append(f"{plan.get('plan_id')}: missing target slide")
            continue
        visual = slide.get("visual", {})
        if visual.get("visual_plan_id") != plan.get("plan_id"):
            errors.append(f"{plan.get('plan_id')}: blueprint visual_plan_id is missing")
            continue
        implementation = plan.get("implementation")
        if implementation in HTML_IMPLEMENTATIONS:
            if not slide.get("content_model") and visual.get("kind") != "inline-svg":
                errors.append(f"{plan.get('plan_id')}: missing HTML/SVG implementation")
        elif implementation in ASSET_IMPLEMENTATIONS:
            asset_id = visual.get("asset_id")
            if not asset_id or not any(asset.get("asset_id") == asset_id for asset in assets):
                errors.append(f"{plan.get('plan_id')}: missing visual_assets entry")
        elif implementation != "none":
            errors.append(f"{plan.get('plan_id')}: unknown implementation {implementation}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("OK: required visual plans resolve in blueprint")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
