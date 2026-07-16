#!/usr/bin/env python3
import re
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_deck.py <index.html>")
        return 2

    path = Path(sys.argv[1])
    html = path.read_text(encoding="utf-8")
    errors = []

    required = {
        "1280px slide width": r"\.slide\s*\{[^}]*width:\s*1280px",
        "720px slide height": r"\.slide\s*\{[^}]*height:\s*720px",
        "print styles": r"@media\s+print",
        "16:9 print page": r"@page\s*\{[^}]*size:\s*13\.333333in\s+7\.5in[^}]*margin:\s*0",
        "exact print colors": r"(?:-webkit-)?print-color-adjust:\s*exact",
        "print slide width": r"@media\s+print[\s\S]*?\.slide\s*\{[^}]*width:\s*13\.333333in",
        "print slide height": r"@media\s+print[\s\S]*?\.slide\s*\{[^}]*height:\s*7\.5in",
        "reduced motion": r"prefers-reduced-motion",
        "keyboard next": r"ArrowRight",
        "keyboard previous": r"ArrowLeft",
        "presenter shortcut": r"key\.toLowerCase\(\)\s*===\s*[\"']s[\"']",
        "reveal-all shortcut": r"key\.toLowerCase\(\)\s*===\s*[\"']a[\"']",
        "reveal-all behavior": r"revealAll\s*\(",
        "presenter view": r"presenter-mode|presenter=1",
        "presenter shortcut display": r"presenter-shortcuts|ショートカット",
        "speaker notes": r"data-spoken-note",
        "structured presenter notes": r"renderPresenterNote\s*\(",
        "primary presenter script area": r"presenter-cue-primary",
        "presenter note render cache": r"dataset\.noteKey",
        "timer-only presenter refresh": r"setInterval\s*\(\s*\(\)\s*=>\s*this\.renderPresenterTimer\(\)\s*,\s*1000\s*\)",
        "structured presenter context": r"renderPresenterContext\s*\(",
        "presenter context rows": r"presenter-context-row",
        "phase question presenter context": r"dataset\.phaseQuestion",
        "speaker purpose presenter context": r"dataset\.speakerPurpose",
        "window synchronization": r"BroadcastChannel|postMessage",
        "current preview exact clone": r"renderCurrentPreview\s*\(",
        "next preview final-state renderer": r"renderNextPreview\s*\(",
        "next preview reveal all": r"renderNextPreview[\s\S]*?querySelectorAll\([\"']\[data-anim\][\"']\)[\s\S]*?classList\.add\([\"']shown[\"']\)",
        "audience DOM snapshot": r"slideHTML",
        "scale view": r"scale\(",
        "page numbers": r"page-number|page-num",
        "layout audit": r"audit=1|searchParams\.get\(['\"]audit",
        "viewport gutter token": r"--viewport-gutter\s*:\s*(?:3[2-9]|[4-9]\d)px",
        "viewport gutter fit": r"innerWidth\s*-\s*gutter\s*\*\s*2[\s\S]*innerHeight\s*-\s*gutter\s*\*\s*2",
        "Z-flow animation normalizer": r"applyZFlow\s*\(",
        "Z-flow bucket function": r"zFlowBucket\s*\(",
    }
    for label, pattern in required.items():
        if not re.search(pattern, html, flags=re.I | re.S):
            errors.append(f"missing {label}")

    if re.search(r"https?://", html, flags=re.I):
        errors.append("external URL dependency found")
    if re.search(r"setInterval\s*\(\s*\(\)\s*=>\s*this\.renderPresenter\(\)\s*,\s*1000\s*\)", html):
        errors.append("presenter timer must not rebuild notes every second")

    slide_count = len(re.findall(r"<section\b[^>]*class=[\"'][^\"']*\bslide\b", html, re.I))
    if slide_count < 3:
        errors.append("deck must contain at least 3 slides")

    roles = re.findall(r"<section\b[^>]*data-role=[\"']([^\"']+)", html, re.I)
    if len(roles) < 2 or roles[-2:] != ["recap", "thanks"]:
        errors.append("last two data-role values must be recap and thanks")

    for value in re.findall(r"font-size:\s*(\d+)px", html, re.I):
        size = int(value)
        if size < 18:
            errors.append(f"font-size {size}px is below the absolute floor")
            break

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"OK: {slide_count} slides passed static validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
