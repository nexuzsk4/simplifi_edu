import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from preset_question_agent.cli import build_cost_summary, build_run_record, sanitize_filename_part, write_run_record


class CliOutputTests(unittest.TestCase):
    def test_build_cost_summary_calculated(self):
        summary = build_cost_summary(
            output_payload={"model": "gemini-2.5-flash-lite"},
            usage_payload={"input_tokens": 1200, "output_tokens": 700, "cached_input_tokens": 0},
        )
        self.assertEqual(summary["status"], "calculated_from_usage")
        self.assertEqual(summary["model"], "gemini-2.5-flash-lite")
        self.assertAlmostEqual(summary["total_cost_usd"], 0.0004)
        self.assertAlmostEqual(summary["total_cost_thb"], 0.0132)
        self.assertEqual(summary["thb_rate"], 33.0)

    def test_write_run_record_to_output_dir(self):
        run_record = build_run_record(
            input_payload={"course": "Physics", "topic": "Linear motion"},
            output_payload={"model": "gemini-2.5-flash-lite", "usage": {"input_tokens": 1, "output_tokens": 1}},
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = write_run_record(run_record=run_record, output_dir=tmp_dir)
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertIn("started_at_utc", payload)
            self.assertIn("completed_at_utc", payload)
            self.assertIn("processing_time_seconds", payload)
            self.assertIsInstance(payload["processing_time_seconds"], (float, int))
            self.assertIn("input", payload)
            self.assertIn("output", payload)
            self.assertIn("cost_usd", payload)
            self.assertIn("usage", payload["output"])
            self.assertEqual(output_path.name, "output_1_Linear motion.json")

    def test_write_run_record_increments_output_sequence(self):
        first_record = build_run_record(
            input_payload={"course": "Physics", "topic": "Linear motion"},
            output_payload={"model": "gemini-2.5-flash-lite", "usage": {"input_tokens": 1, "output_tokens": 1}},
        )
        second_record = build_run_record(
            input_payload={"course": "Math", "topic": "แคลคูลัสเบื้องต้น"},
            output_payload={"model": "gemini-2.5-flash-lite", "usage": {"input_tokens": 1, "output_tokens": 1}},
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            first_path = write_run_record(run_record=first_record, output_dir=tmp_dir)
            second_path = write_run_record(run_record=second_record, output_dir=tmp_dir)

            self.assertEqual(first_path.name, "output_1_Linear motion.json")
            self.assertEqual(second_path.name, "output_2_แคลคูลัสเบื้องต้น.json")

    def test_sanitize_filename_part_removes_invalid_characters(self):
        self.assertEqual(sanitize_filename_part('A/B:C*D?"E'), "A-B-C-D-E")


if __name__ == "__main__":
    unittest.main()
