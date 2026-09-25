"""Version 3 notes: concise cues, optional script, and explicit reading time.

Keep this serialization shared by validation and editor import. The HTML note is
self-describing, so older decks need no migration or extra runtime attributes.
"""
from __future__ import annotations

import re

MODES = {"cue", "script", "hybrid"}
LABELS = {"形式", "要点", "話す内容", "指差し", "橋渡し", "次の一言", "次のスライド", "話さない理由"}


def render_note(slide: dict) -> str:
    cue = slide.get("speaker_cue") or {}
    lines = [f"形式: {cue.get('mode', 'cue')}"]
    for item in cue.get("cues") or []:
        lines.append(f"要点: {item}")
    for label, value in (
        ("話す内容", cue.get("script")),
        ("指差し", " / ".join(cue.get("point_at") or [])),
        ("橋渡し", (slide.get("connection_from_previous") or {}).get("bridge")),
        ("次の一言", cue.get("transition")),
        ("次のスライド", cue.get("next_slide_id")),
        ("話さない理由", cue.get("silence_reason")),
    ):
        if value:
            lines.append(f"{label}: {value}")
    return "\n".join(lines)


def parse_note(note: str) -> tuple[dict, str]:
    """Reject ambiguous/lossy edits instead of silently discarding their text."""
    parts: dict[str, str] = {}
    cues: list[str] = []
    for line in note.splitlines():
        if not line.strip():
            continue
        match = re.match(r"^\s*([^:：]+)\s*[:：]\s*(\S.*?)\s*$", line)
        if not match or match[1].strip() not in LABELS:
            raise ValueError(f"未対応のノート行: {line}")
        label, value = match[1].strip(), match[2]
        if label == "要点":
            cues.append(value)
        elif label in parts:
            raise ValueError(f"{label} が重複しています")
        else:
            parts[label] = value
    mode = parts.get("形式")
    if mode not in MODES:
        raise ValueError("形式は cue / script / hybrid のいずれかです")
    script = parts.get("話す内容", "")
    silence = parts.get("話さない理由", "")
    if silence:
        if mode != "cue" or cues or script or parts.get("橋渡し") or parts.get("次の一言"):
            raise ValueError("話さないページは cue 形式にし、発話する行を併記しません")
        if not parts.get("指差し") or parts["指差し"] == "none":
            raise ValueError("話さないページには見る対象を指差しに指定してください")
    else:
        if mode in {"cue", "hybrid"} and not cues:
            raise ValueError("cue / hybrid には要点が必要です")
        if mode in {"script", "hybrid"} and not script:
            raise ValueError("script / hybrid には話す内容が必要です")
        if mode == "cue" and script or mode == "script" and cues:
            raise ValueError("要点と話す内容の両方を使う場合は hybrid にしてください")
    if bool(parts.get("次の一言")) != bool(parts.get("次のスライド")):
        raise ValueError("次の一言と次のスライドIDを一緒に指定してください")
    cue = {
        "mode": mode, "cues": cues, "script": script,
        "point_at": parts.get("指差し", "").split(" / ") if parts.get("指差し") else [],
        "transition": parts.get("次の一言", ""),
        "next_slide_id": parts.get("次のスライド", ""),
        "silence_reason": silence,
    }
    return cue, parts.get("橋渡し", "")


def validate_note(slide: dict, next_id: str = "") -> list[str]:
    cue = slide.get("speaker_cue")
    connection = slide.get("connection_from_previous") or {}
    if not isinstance(cue, dict) or not isinstance(connection, dict):
        return ["speaker_cue / connection_from_previous はmappingで指定してください"]
    for field in ("cues", "point_at"):
        values = cue.get(field, [])
        if not isinstance(values, list) or any(not isinstance(item, str) or not item.strip() or "\n" in item or "\r" in item for item in values):
            return [f"speaker_cue.{field} は空でない1行文字列の配列で指定してください"]
    for value in [connection.get("bridge", "")] + [cue.get(field, "") for field in ("mode", "script", "transition", "next_slide_id", "silence_reason")]:
        if not isinstance(value, str) or "\n" in value or "\r" in value:
            return ["ノートの値は1項目1行の文字列で指定してください"]
    note = slide.get("spoken_note") or ""
    try:
        parsed, _ = parse_note(note)
    except (ValueError, TypeError) as exc:
        return [str(exc)]
    if note != render_note(slide):
        return ["spoken_note が speaker_cue / connection_from_previous と一致しません（render_note で生成）"]
    if parsed["next_slide_id"] and parsed["next_slide_id"] != next_id:
        return [f"次のスライドは実際の次ページ {next_id or 'なし'} と一致させてください"]
    return []
