import unittest
from review_speaking import review


class SpeakingReviewTests(unittest.TestCase):
    def test_known_problem_patterns_are_reported_without_claiming_rehearsal(self):
        script = "同じ説明を複製すると更新先が分からなくなります。更新先の資料を一つに決めます。"
        story = {"slides": [{"id": sid, "title": "正本と地図", "speaker_cue": {"script": script}, "spoken_note": "橋渡し: 原稿の順序を保ち、次へ進む"} for sid in ("s01", "s02")]}
        result = review(story)
        kinds = {finding["type"] for finding in result["findings"]}
        self.assertTrue({"wording", "template-note", "possible-repetition"} <= kinds)
        self.assertEqual("not_performed", result["user_rehearsal"])

    def test_technical_exception_and_code_are_preserved(self):
        result = review({"slides": [{"id": "s01", "title": "地図API", "language_exceptions": [{"term": "地図", "reason": "地理データを扱うAPIの説明"}], "content_model": {"data": {"code": "正本 = 道具"}}}]})
        self.assertFalse(result["findings"])

    def test_deliberate_recap_is_identified(self):
        cue = {"script": "時刻をそろえて比較してから変更する操作を一つに決めます。"}
        result = review({"slides": [{"id": "s01", "speaker_cue": cue}, {"id": "s02", "speaker_cue": {**cue, "recap_of": ["s01"], "recap_reason": "最後に最初の判断を確認する"}}]})
        self.assertTrue(any(f["type"] == "intentional-recap" for f in result["findings"]))


if __name__ == "__main__":
    unittest.main()
