#!/usr/bin/env python3
"""Export conflict-checked Story/Blueprint candidates from saved editor notes.

Never overwrite the source files. Review candidates, run all applicable pipeline
validators, then adopt both files together and rebuild HTML (clears edit baseline).
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from html.parser import HTMLParser
import json
from pathlib import Path
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "01-lt-slide-story" / "scripts"))
from speaker_notes import parse_note, render_note
from validate_spoken_notes import sections, TALKABILITY_LABELS, validate_slides
from validate_talkability import validate_story


class Notes(HTMLParser):
    def __init__(self):
        super().__init__()
        self.slides = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag != "section" or "slide" not in (attrs.get("class") or "").split():
            return
        sid = attrs.get("data-slide-id")
        if not sid or sid in self.slides:
            raise ValueError(f"HTMLのスライドIDが空または重複: {sid}")
        self.slides[sid] = attrs


def propose(story: dict, blueprint: dict, html: str) -> tuple[dict, dict, list[str]]:
    parser = Notes()
    parser.feed(html)
    result, plan = deepcopy(story), deepcopy(blueprint)
    source_ids = [slide["id"] for slide in result["slides"]]
    plan_ids = [slide["id"] for slide in plan["slides"]]
    if len(set(source_ids)) != len(source_ids) or plan_ids != source_ids or list(parser.slides) != source_ids:
        raise ValueError("スライドの追加・削除・並べ替えがあります。先にStory/Blueprintの構成を更新してください")
    version = int((story.get("project") or {}).get("talkability_version") or 1)
    if version not in {2, 3}:
        raise ValueError("ノート取り込みは talkability_version 2 / 3 に対応しています")
    changed = []
    for slide, target in zip(result["slides"], plan["slides"]):
        sid = slide["id"]
        if target.get("spoken_note") != slide.get("spoken_note") or target.get("speaker_cue") != slide.get("speaker_cue"):
            raise ValueError(f"{sid}: StoryとBlueprintが既に不一致です。先に差分を確認してください")
        attrs = parser.slides[sid]
        note = attrs.get("data-spoken-note") or ""
        if note == slide.get("spoken_note"):
            continue
        if attrs.get("data-original-spoken-note") != slide.get("spoken_note"):
            raise ValueError(f"{sid}: 編集開始時のノートがStoryと異なります。変更の競合を確認してください")
        cue = slide.setdefault("speaker_cue", {})
        if version == 3:
            parsed, bridge = parse_note(note)
            cue.update(parsed)
        else:
            parts = sections(note, TALKABILITY_LABELS)
            if len(parts) != 4 or len([line for line in note.splitlines() if line.strip()]) != 4:
                raise ValueError(f"{sid}: 旧ノートは4行形式で入力してください")
            cue.update(script=parts["話す内容"], point_at=parts["指差し"].split(" / "), transition=parts["次の一言"])
            bridge = parts["橋渡し"]
        slide.setdefault("connection_from_previous", {})["bridge"] = bridge
        slide["spoken_note"] = render_note(slide) if version == 3 else note
        target["speaker_cue"] = deepcopy(cue)
        target["spoken_note"] = slide["spoken_note"]
        target.setdefault("narrative_continuity", {})["bridge"] = bridge
        # Some builders also retain Story's connection object in Blueprint.
        if "connection_from_previous" in target:
            target["connection_from_previous"]["bridge"] = bridge
        changed.append(sid)
    return result, plan, changed


def main() -> int:
    parser = argparse.ArgumentParser(description="保存済みHTMLのノート修正をStory/Blueprintの候補ファイルへ反映する")
    parser.add_argument("--story", type=Path, required=True)
    parser.add_argument("--blueprint", type=Path, required=True)
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="未使用の候補出力ディレクトリ")
    args = parser.parse_args()
    try:
        story, blueprint, changed = propose(
            yaml.safe_load(args.story.read_text(encoding="utf-8")),
            yaml.safe_load(args.blueprint.read_text(encoding="utf-8")),
            args.html.read_text(encoding="utf-8"),
        )
        if not changed:
            print("OK: 取り込むノート変更はありません")
            return 0
        note_errors, _ = validate_slides(story["slides"], int(story["project"]["talkability_version"]))
        errors = note_errors + validate_story(args.story, story)
        # Candidate directory must be new: source files and earlier reviews survive.
        args.out.mkdir(parents=True, exist_ok=False)
        for name, data in (("01-story.yaml", story), ("02-blueprint.yaml", blueprint)):
            (args.out / name).write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        report = {"changed_slides": changed, "note_errors": errors,
                  "remaining_checks": ["section fidelity / knowledge / semantic / timing / visible anchors", "slide and cue rehearsal"],
                  "user_rehearsal": "not_performed", "sources_overwritten": False}
        (args.out / "note-revisions.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"候補を出力: {args.out}（{len(changed)}ページ）。対応する全validatorと意味レビュー後に2ファイルを同時採用しHTMLを再構築してください。")
        if errors:
            print("\n".join(f"ERROR: {error}" for error in errors))
            return 1
        return 0
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
