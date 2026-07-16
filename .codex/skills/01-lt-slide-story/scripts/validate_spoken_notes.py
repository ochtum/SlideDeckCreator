from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re

import yaml


LEGACY_LABELS = ("橋渡し", "読み方", "次の判断")
TALKABILITY_LABELS = ("橋渡し", "話す内容", "指差し", "次の一言")
FORBIDDEN = (
    "具体例と次の判断を補う",
    "ノートなし",
    "todo",
    "tbd",
    "後で書く",
)
GENERIC_SCRIPT = (
    "このページでは",
    "このスライドでは",
    "タイトルの通り",
    "表示内容を確認",
    "画面を確認します",
    "次の具体的な判断材料",
)


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


def sections(note: str, labels: tuple[str, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in note.splitlines():
        label_pattern = "|".join(re.escape(label) for label in labels)
        match = re.match(rf"^\s*({label_pattern})\s*[:：]\s*(.+?)\s*$", line)
        if match:
            result[match.group(1)] = match.group(2)
    return result


def validate_slides(slides: list[dict], talkability_version: int = 1) -> tuple[list[str], dict[str, str]]:
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

        labels = TALKABILITY_LABELS if talkability_version >= 2 else LEGACY_LABELS
        parts = sections(note, labels)
        missing = [label for label in labels if not parts.get(label)]
        if missing:
            errors.append(f"{slide_id}: {', '.join(missing)} の各行を含めてください")
            continue
        if talkability_version < 2:
            if any(len(compact(parts[label])) < 8 for label in labels):
                errors.append(f"{slide_id}: 橋渡し・読み方・次の判断はそれぞれ具体的に8文字以上で書いてください")
            if title and compact(title) not in compact(parts["読み方"]):
                errors.append(f"{slide_id}: 読み方にはスライド固有のタイトル「{title}」を含めてください")
            continue

        minimums = {"橋渡し": 8, "話す内容": 40, "指差し": 2, "次の一言": 8}
        for label, minimum in minimums.items():
            if len(compact(parts[label])) < minimum:
                errors.append(f"{slide_id}: {label} は具体的に{minimum}文字以上で書いてください")
        if any(compact(phrase) in compact(parts["話す内容"]) for phrase in GENERIC_SCRIPT):
            errors.append(f"{slide_id}: 話す内容がメタ説明のテンプレートです。実際に口にする説明へ直してください")

        cue = slide.get("speaker_cue")
        if not isinstance(cue, dict):
            errors.append(f"{slide_id}: talkability v2 では speaker_cue が必要です")
            continue
        expected = {
            "橋渡し": ((slide.get("connection_from_previous") or {}).get("bridge") or "").strip(),
            "話す内容": str(cue.get("script") or "").strip(),
            "指差し": " / ".join(str(value) for value in (cue.get("point_at") or [])),
            "次の一言": str(cue.get("transition") or "").strip(),
        }
        for label, value in expected.items():
            if value and compact(parts[label]) != compact(value):
                errors.append(f"{slide_id}: {label} が speaker_cue または接続情報と一致しません")
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

    project = story.get("project") or {}
    talkability_version = int(project.get("talkability_version") or 1)
    errors, notes = validate_slides(slides, talkability_version)
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
