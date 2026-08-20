from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from validate_talkability import validate_blueprint, validate_story


def long_script(slide_id: str, focus: str, minimum: int) -> str:
    sentences = [
        f"{slide_id}の例では、家庭の電力使用量を時間帯別に記録し、{focus}が変わる位置を一緒に見ます。",
        f"数字を並べるだけでは原因を判断できないため、前日の値と気温を同じ条件で比較します。",
        f"ここで重要なのは最大値ではなく、生活行動を変えた直後に増えた区間と、その前後の差です。",
        f"この差を手掛かりにすると、節電策を思いつきで選ばず、次に試す操作を一つへ絞れます。",
    ]
    value = "".join(sentences)
    while len(value.replace(" ", "")) < minimum:
        value += f"さらに{slide_id}の記録を残すと、次回も同じ条件で結果を比べられます。"
    return value


def make_slide(slide_id: str, role: str, phase: str, seconds: int | None, anchor: str) -> dict:
    bridge = f"直前の結果だけでは判断できないため、{slide_id}の観点へ進みます。"
    transition = f"{slide_id}で得た答えを使い、次に残った疑問へ進みます。"
    minimum = min(240, max(50, int((seconds or 25) * 1.5)))
    script = long_script(slide_id, anchor, minimum)
    point_at = [anchor] if seconds is not None and role != "goal" else ["none"]
    cue = {
        "purpose": f"{slide_id}で聴衆の判断材料を一つ増やす",
        "audience_state_before": f"{slide_id}の判断根拠がまだ分からない",
        "audience_state_after": f"{slide_id}の判断根拠を具体例で説明できる",
        "script": script,
        "point_at": point_at,
        "transition": transition,
    }
    slide = {
        "id": slide_id,
        "role": role,
        "flow_phase": phase,
        "title": f"{slide_id} 電力記録の読み方",
        "connection_from_previous": {"prior_state": "直前の説明を理解している", "bridge": bridge},
        "speaker_cue": cue,
        "spoken_note": "\n".join([
            f"橋渡し: {bridge}",
            f"話す内容: {script}",
            f"指差し: {' / '.join(point_at)}",
            f"次の一言: {transition}",
        ]),
    }
    if seconds is not None:
        slide["delivery"] = {
            "mode": "demo" if phase == "demo" else "explain",
            "estimated_seconds": seconds,
            "talking_points": [f"{slide_id}の比較条件", f"{slide_id}の判断基準"],
            "visible_anchors": [anchor, f"{anchor}の前日差"],
        }
    return slide


def good_story() -> dict:
    slides = [
        make_slide("cover", "cover", "", None, "表紙"),
        make_slide("profile", "profile", "", None, "自己紹介"),
        make_slide("goal", "goal", "", 120, "none"),
        make_slide("why-1", "problem", "why", 120, "夜20時の使用量"),
        make_slide("why-2", "evidence", "why", 120, "前日差+1.2kWh"),
        make_slide("what-1", "comparison", "what", 150, "時間帯別ログ"),
        make_slide("what-2", "flow", "what", 150, "行動メモ"),
        make_slide("how-1", "action", "how", 160, "計測開始時刻"),
        make_slide("how-2", "action", "how", 160, "比較条件"),
        make_slide("how-3", "action", "how", 160, "完了条件"),
        make_slide("demo-1", "demo", "demo", 180, "スマートメーター値"),
        make_slide("demo-2", "demo", "demo", 180, "差分グラフ"),
        make_slide("recap", "recap", "takeaway", 180, "15分の記録メモ"),
        make_slide("thanks", "thanks", "", None, "終了"),
    ]
    return {
        "project": {
            "title": "家庭の電力ログから最初の節電策を選ぶ",
            "duration_minutes": 30,
            "talkability_version": 2,
            "target_slide_count": 11,
            "time_budget": {
                "content_seconds": 1260,
                "demo_seconds": 300,
                "interaction_seconds": 120,
                "buffer_seconds": 120,
            },
        },
        "narrative": {
            "central_example": "ある家庭の一週間分の時間帯別電力ログ",
            "opening_problem": "請求額だけを見ても、どの生活行動を変えるべきか判断できない",
            "final_change": "十五分の記録から翌日に試す節電策を一つ選べる",
            "framing_seconds": 120,
            "omitted_phases": [],
            "question_spine": [
                {"phase": "why", "audience_question": "請求額だけではなぜ行動を選べないのか？", "answer": "時間帯と行動の対応がないため原因を絞れない", "transition_to_next": "原因を絞るために、まず記録の単位を定義します。", "time_seconds": 240, "source_items": ["fact-meter"]},
                {"phase": "what", "audience_question": "判断に使える電力ログとは何なのか？", "answer": "時間帯別の値と行動メモを同じ時刻で結んだ記録である", "transition_to_next": "記録の形が分かったので、作り方を三手順にします。", "time_seconds": 300, "source_items": ["claim-log"]},
                {"phase": "how", "audience_question": "比較可能なログをどう作るのか？", "answer": "開始時刻、比較条件、完了条件を先に固定して記録する", "transition_to_next": "三つの条件が本当に使えるか、同じ家庭の値で動かします。", "time_seconds": 480, "source_items": ["step-record"]},
                {"phase": "demo", "audience_question": "実際の値から何が見えるのか？", "answer": "夜二十時の増加と調理開始が重なる様子を差分で観測できる", "transition_to_next": "見えた差を、明日十五分で残せる成果物へ縮めます。", "time_seconds": 360, "source_items": ["demo-meter"]},
                {"phase": "takeaway", "audience_question": "明日最初に何を記録すればよいのか？", "answer": "十五分で一時間帯の値と行動を一枚のメモに残す", "transition_to_next": "まず今夜の一時間帯だけを記録してください。", "time_seconds": 180, "source_items": ["action-note"]},
            ],
        },
        "demo_runbook": {
            "starting_state": "スマートメーターの時間帯別一覧と空の行動メモを左右に開いている",
            "steps": [
                {"action": "夜二十時の使用量を選択する", "visible_result": "選択行に2.8kWhと表示される", "talk_line": "まず増えた時刻を一つだけ選びます。"},
                {"action": "前日の同時刻との差分を表示する", "visible_result": "+1.2kWhの差分バーが青色で現れる", "talk_line": "絶対値ではなく同じ条件との差を見ます。"},
                {"action": "行動メモの調理開始時刻を重ねる", "visible_result": "二十時のバーと調理開始マーカーが同じ位置に並ぶ", "talk_line": "ここで初めて次に試す行動を候補にできます。"},
            ],
            "end_state": "増加時刻、前日差、行動マーカーを一画面で説明できる",
            "fallback": "同じ三状態を保存した連続スクリーンショットを表示する",
            "source_items": ["demo-meter"],
        },
        "tomorrow_action": {
            "timebox": "15分",
            "action": "今夜の一時間帯の使用量と行動を記録する",
            "artifact": "時刻、使用量、行動、比較条件を持つ一枚のメモ",
            "done_when": "翌日に同時刻の値を並べて差を説明できる",
            "first_step": "電力会社の時間帯別使用量画面を開く",
        },
        "slides": slides,
    }


class TalkabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.path = Path("energy-story.yaml")

    def test_unrelated_topic_passes(self) -> None:
        self.assertEqual([], validate_story(self.path, good_story()))

    def test_meta_template_script_fails(self) -> None:
        story = good_story()
        slide = story["slides"][3]
        slide["speaker_cue"]["script"] = "このページでは表示内容を確認します。" * 10
        slide["spoken_note"] = slide["spoken_note"].replace(
            slide["spoken_note"].splitlines()[1],
            f"話す内容: {slide['speaker_cue']['script']}",
        )
        errors = validate_story(self.path, story)
        self.assertTrue(any("meta-explanation" in error or "メタ説明" in error for error in errors))

    def test_unobservable_demo_fails(self) -> None:
        story = good_story()
        story["demo_runbook"]["steps"][0]["visible_result"] = "確認する"
        errors = validate_story(self.path, story)
        self.assertTrue(any("not observable" in error for error in errors))

    def test_takeaway_without_artifact_fails(self) -> None:
        story = good_story()
        story["tomorrow_action"]["artifact"] = ""
        errors = validate_story(self.path, story)
        self.assertTrue(any("tomorrow_action.artifact" in error for error in errors))

    def test_uniform_pacing_fails(self) -> None:
        story = good_story()
        counts = {"why": 0, "what": 0, "how": 0, "demo": 0, "takeaway": 0}
        for slide in story["slides"]:
            if "delivery" in slide:
                slide["delivery"]["estimated_seconds"] = 120
                phase = slide.get("flow_phase") or ""
                if phase:
                    counts[phase] += 1
        for item in story["narrative"]["question_spine"]:
            item["time_seconds"] = counts[item["phase"]] * 120
        story["project"]["time_budget"] = {
            "content_seconds": 900,
            "demo_seconds": 240,
            "interaction_seconds": 180,
            "buffer_seconds": 480,
        }
        errors = validate_story(self.path, story)
        self.assertTrue(any("vary pacing" in error for error in errors))

    def test_custom_article_archetype_does_not_require_demo_or_takeaway(self) -> None:
        story = good_story()
        phase_map = {
            "why": "context",
            "what": "evidence",
            "how": "evidence",
            "demo": "decision",
            "takeaway": "decision",
        }
        for slide in story["slides"]:
            phase = slide.get("flow_phase") or ""
            if phase:
                slide["flow_phase"] = phase_map[phase]
            if slide.get("role") == "demo":
                slide["role"] = "evidence"
                slide["delivery"]["mode"] = "explain"
        story["project"]["time_budget"] = {
            "content_seconds": 1560,
            "demo_seconds": 0,
            "interaction_seconds": 120,
            "buffer_seconds": 120,
        }
        story["narrative"]["archetype"] = "constraints-options-tradeoffs"
        story["narrative"]["phase_order"] = ["context", "evidence", "decision"]
        story["narrative"]["question_spine"] = [
            {
                "phase": "context",
                "audience_question": "電力ログを読む前にどの状況をそろえる必要があるか？",
                "answer": "比較する時間帯と生活行動の前提を同じ粒度でそろえる",
                "transition_to_next": "前提がそろったので、観測値と行動記録を結びます。",
                "time_seconds": 240,
                "source_items": ["fact-meter"],
            },
            {
                "phase": "evidence",
                "audience_question": "どの記録なら原因候補を絞る証拠として使えるか？",
                "answer": "開始時刻と比較条件を固定した時間帯別ログを使う",
                "transition_to_next": "証拠がそろったので、次に試す行動を一つ選びます。",
                "time_seconds": 780,
                "source_items": ["claim-log", "step-record"],
            },
            {
                "phase": "decision",
                "audience_question": "観測した差から次に試す節電策をどう選ぶか？",
                "answer": "行動直後に増えた区間を基準に候補を一つへ絞る",
                "transition_to_next": "選んだ候補を一時間帯の記録として残します。",
                "time_seconds": 540,
                "source_items": ["demo-meter", "action-note"],
            },
        ]
        story.pop("demo_runbook")
        story.pop("tomorrow_action")
        self.assertEqual([], validate_story(self.path, story))

    def test_appendix_slide_does_not_consume_live_timing(self) -> None:
        story = good_story()
        appendix = make_slide("appendix-1", "evidence", "", None, "完全な比較条件")
        appendix["delivery_scope"] = "appendix"
        story["slides"].append(appendix)
        self.assertEqual([], validate_story(self.path, story))

    def test_blueprint_must_preserve_cue_and_phase_context(self) -> None:
        story = good_story()
        spine = {item["phase"]: item for item in story["narrative"]["question_spine"]}
        slides = []
        for source in story["slides"]:
            phase = source.get("flow_phase") or ""
            phase_context = {}
            if phase:
                phase_context = {key: spine[phase][key] for key in ("audience_question", "answer", "transition_to_next")}
            slides.append({
                "id": source["id"],
                "speaker_cue": deepcopy(source["speaker_cue"]),
                "spoken_note": source["spoken_note"],
                "phase_context": phase_context,
                "delivery": deepcopy(source.get("delivery") or {}),
                "text": {"details": (source.get("delivery") or {}).get("visible_anchors") or []},
            })
        import tempfile
        import yaml

        with tempfile.TemporaryDirectory() as directory:
            blueprint_path = Path(directory) / "02-blueprint.yaml"
            blueprint_path.write_text(yaml.safe_dump({"slides": slides}, allow_unicode=True), encoding="utf-8")
            self.assertEqual([], validate_blueprint(blueprint_path, story))
            slides[3]["speaker_cue"]["transition"] = "別の台詞"
            blueprint_path.write_text(yaml.safe_dump({"slides": slides}, allow_unicode=True), encoding="utf-8")
            errors = validate_blueprint(blueprint_path, story)
            self.assertTrue(any("speaker_cue was not copied" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
