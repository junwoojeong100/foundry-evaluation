import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_actions_video import guide_order, intervals, presentation_order, srt_time
from media_server import byte_range


class MediaTimelineTests(unittest.TestCase):
    def test_video_is_ordered_by_the_guide_not_capture_time(self):
        actions = [{"guide": value} for value in ["G · Monitor", "A · IQ", "00 · 준비", "마무리 · 정리", "C · 평가"]]
        self.assertEqual([a["guide"] for a in sorted(actions, key=guide_order)],
                         ["00 · 준비", "A · IQ", "C · 평가", "G · Monitor", "마무리 · 정리"])

    def test_trace_review_precedes_feedback_and_report_precedes_comparison(self):
        actions = [{"guide": "D · 실패", "id": name} for name in ["D04-feedback", "D-P03-trace-detail", "D02-monitor", "D03-review"]]
        self.assertEqual([a["id"] for a in sorted(actions, key=presentation_order)],
                         ["D02-monitor", "D-P03-trace-detail", "D03-review", "D04-feedback"])
        self.assertLess(presentation_order({"guide": "E · 개선", "id": "E-P04-improved-report"}),
                        presentation_order({"guide": "E · 개선", "id": "E07-compare"}))

    def test_short_action_is_kept_whole(self):
        self.assertEqual(intervals({"id": "x", "started": 11000, "ended": 17000}, {"started": 1000}),
                         [(10, 16)])

    def test_long_wait_does_not_remove_action_or_result(self):
        result = intervals({"id": "x", "started": 11000, "result_at": 310000, "ended": 318000}, {"started": 1000})
        self.assertEqual(result, [(10, 14), (308, 317)])
        self.assertLess(result[0][1], result[1][0])

    def test_invalid_clocks_are_rejected(self):
        with self.assertRaises(ValueError):
            intervals({"id": "x", "started": 10, "ended": 20}, {"started": 1000})

    def test_caption_time(self):
        self.assertEqual(srt_time(3661.25), "01:01:01,250")

    def test_video_byte_ranges_support_chapter_seeking(self):
        self.assertEqual(byte_range("bytes=100-199", 1000), (100, 199))
        self.assertEqual(byte_range("bytes=100-", 1000), (100, 999))
        self.assertEqual(byte_range("bytes=-100", 1000), (900, 999))
        for value in ("bytes=1000-", "bytes=5-4", "bytes=-0", "bytes=1-2,3-4"):
            with self.assertRaises(ValueError):
                byte_range(value, 1000)


if __name__ == "__main__":
    unittest.main()
