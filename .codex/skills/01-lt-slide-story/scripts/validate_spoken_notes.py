from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re

import yaml


LABELS = ("橋渡し", "読み方", "次の判断")
FORBIDDEN = ("具体例と次の判断を補う", "ノートなし", "todo", "tbd", "後で書く")


class SlideParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.notes: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "section":
            data = dict(attrs)
            if data.get("data-slide-id"):
                self.notes[data["data-slide-id"]] = data.get("data-spoken-note") or ""


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value).lower()


def sections(note: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in note.splitlines():
        match = re.match(r"^\s*(橋渡し|読み方|次の判断)\s*[:：]\s*(.+?)\s*$", line)
        if match:
            result[match.group(1)] = match.group(2)
    return result


def validate_slides(slides: list[dict]) -> tuple[list[str], dict[str, str]]:
    errors: list[str] = []
    notes: dict[str, str] = {}
    seen: dict[str, str] = {}
    for index, slide in enumerate(slides, start=1):
        slide_id = str(slide.get("id") or f"slide-{index}")
        title = str(slide.get("title") or "")
        note = slide.get("spoken_note")
        if not isinstance(note, str) or not note.strip():
            errors.append(f"{slide_id}: spoken_note が空です")
            continue
        notes[slide_id] = note
        normalized = compact(note)
        if any(compact(phrase) in normalized for phrase in FORBIDDEN):
            errors.append(f"{slide_id}: 仮ノートまたはプレースホルダーを使えません")
        if normalized in seen:
            errors.append(f"{slide_id}: spoken_note が {seen[normalized]} と完全一致しています")
        else:
            seen[normalized] = slide_id

        parts = sections(note)
        missing = [label for label in LABELS if not parts.get(label)]
        if missing:
            errors.append(f"{slide_id}: {', '.join(missing)} の各行を含めてください")
            continue
        if any(len(compact(parts[label])) < 8 for label in LABELS):
            errors.append(f"{slide_id}: 橋渡し・読み方・次の判断はそれぞれ具体的に8文字以上で書いてください")
        if title and compact(title) not in compact(parts["読み方"]):
            errors.append(f"{slide_id}: 読み方にはスライド固有のタイトル「{title}」を含めてください")
    return errors, notes


def validate_html(html_path: Path, expected: dict[str, str]) -> list[str]:
    parser = SlideParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for slide_id, note in expected.items():
        actual = parser.notes.get(slide_id)
        if actual is None:
            errors.append(f"{html_path}: {slide_id} の data-slide-id がありません")
        elif actual != note:
            errors.append(f"{html_path}: {slide_id} の data-spoken-note がストーリーと一致しません")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="ページ固有で構造化されたスピーカーノートを検証する")
    parser.add_argument("--story", required=True, type=Path)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()
    try:
        story = yaml.safe_load(args.story.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: story を読めません: {exc}")
        return 1
    slides = story.get("slides") if isinstance(story, dict) else None
    if not isinstance(slides, list):
        print("ERROR: --story には slides を持つパートの01-story.yamlを指定してください")
        return 1

    errors, notes = validate_slides(slides)
    if args.html:
        if not args.html.is_file():
            errors.append(f"HTMLがありません: {args.html}")
        else:
            errors.extend(validate_html(args.html, notes))
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    scope = " とHTML" if args.html else ""
    print(f"OK: {len(notes)}枚のスピーカーノート{scope}を検証しました")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
