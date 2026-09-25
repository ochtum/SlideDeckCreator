#!/usr/bin/env python3
"""Heuristics for a slide-and-note rehearsal. Findings require semantic review."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import yaml

AVOID = ("正本", "地図", "道具")
BOILERPLATE = ("原稿の順序を保ち", "を前の判断からつなぎ", "このページでは", "このスライドでは")


def compact(value):
    return re.sub(r"[\s、。！？!?・:：]", "", str(value or ""))


def strings(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in strings(item)]
    if isinstance(value, dict):
        # Preserve code, quotations and source material; review explanatory prose.
        return [text for key, item in value.items() if key not in {"code", "snippet", "quote", "url", "source", "citations"} for text in strings(item)]
    return []


def review(story: dict) -> dict:
    findings, pages, past = [], [], []
    for slide in story.get("slides") or []:
        sid = slide.get("id")
        cue = slide.get("speaker_cue") or {}
        mode = cue.get("mode") or "script"
        phrases = cue.get("cues") if mode in {"cue", "hybrid"} else [cue.get("script") or ""]
        spoken = "。".join(phrases or [])
        visible = " ".join(strings({key: slide.get(key) for key in ("title", "message", "support", "text", "content_model", "information_layers")}))
        note = slide.get("spoken_note") or ""
        exceptions = {item.get("term") for item in slide.get("language_exceptions") or [] if isinstance(item, dict) and item.get("reason")}
        for term in AVOID:
            if term not in exceptions and term in visible + note:
                findings.append({"slide": sid, "type": "wording", "term": term, "message": "指すファイル・図・機能・操作を具体的に書く。引用・正式名称等の場合は理由を記録する"})
        for phrase in BOILERPLATE:
            if phrase in note:
                findings.append({"slide": sid, "type": "template-note", "excerpt": phrase})
        for phrase in re.split(r"[。！？!?\n]", spoken):
            if len(compact(phrase)) > 85:
                findings.append({"slide": sid, "type": "long-utterance", "excerpt": phrase, "message": "一息で話せる単位へ分けるか、表示で伝わる列挙を削る"})
        signature = compact(spoken)
        if signature and len(signature) >= 12 and signature in compact(visible):
            findings.append({"slide": sid, "type": "reads-slide", "message": "画面と発話が同じ。理由や差分の補足だけで足りるか確認する"})
        if len(signature) >= 16:
            grams = {signature[i:i+3] for i in range(len(signature)-2)}
            for old_id, old_grams in past:
                similarity = len(grams & old_grams) / max(1, min(len(grams), len(old_grams)))
                if similarity >= .72:
                    intended = old_id in (cue.get("recap_of") or []) and bool(cue.get("recap_reason"))
                    findings.append({"slide": sid, "other_slide": old_id, "type": "intentional-recap" if intended else "possible-repetition", "similarity": round(similarity, 2)})
            past.append((sid, grams))
        pages.append({"slide": sid, "title": slide.get("title"), "scope": slide.get("delivery_scope", "live"),
                      "purpose": cue.get("purpose"), "spoken": spoken, "point_at": cue.get("point_at", []),
                      "silence_reason": cue.get("silence_reason", ""), "transition": cue.get("transition", ""),
                      "estimated_seconds": (slide.get("delivery") or {}).get("estimated_seconds")})
    return {"automated_check": "completed", "semantic_review": "pending", "user_rehearsal": "not_performed", "findings": findings, "pages": pages}


def main() -> int:
    parser = argparse.ArgumentParser(description="発話・画面・語彙・反復の確認候補を出す。合格や本人確認とは判定しない")
    parser.add_argument("--story", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    story = yaml.safe_load(args.story.read_text(encoding="utf-8"))
    if not isinstance(story, dict) or not isinstance(story.get("slides"), list):
        parser.error("slidesを持つ単一パートのStoryを指定してください")
    report = review(story)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"確認候補 {len(report['findings'])}件: {args.out}（意味レビュー・本人の通し練習は未実施）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
