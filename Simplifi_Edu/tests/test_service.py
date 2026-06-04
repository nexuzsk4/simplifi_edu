import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from preset_question_agent.models import ValidationError
from preset_question_agent.service import normalize_categories, parse_json_payload


class ServiceTests(unittest.TestCase):
    def test_parse_json_payload_accepts_object(self):
        payload = parse_json_payload('{"categories": []}')
        self.assertIn("categories", payload)

    def test_parse_json_payload_accepts_fenced_json(self):
        payload = parse_json_payload('```json\n{"categories": []}\n```')
        self.assertIn("categories", payload)

    def test_parse_json_payload_extracts_json_from_extra_text(self):
        payload = parse_json_payload('Here is the JSON:\n{"categories": []}\nDone.')
        self.assertIn("categories", payload)

    def test_parse_json_payload_extracts_json_with_trailing_text(self):
        payload = parse_json_payload('{"categories": []}\nDone.')
        self.assertIn("categories", payload)

    def test_parse_json_payload_repairs_trailing_commas(self):
        payload = parse_json_payload('{"categories": [],}')
        self.assertIn("categories", payload)

    def test_parse_json_payload_error_includes_preview(self):
        with self.assertRaisesRegex(ValidationError, "Error context"):
            parse_json_payload("not json")

    def test_normalize_categories_enforces_required_ids(self):
        payload = {
            "categories": [
                {"id": "foundations", "title": "F", "questions": ["Q5"]},
                {"id": "common_questions", "title": "C", "questions": ["Q3", "Q4"]},
                {"id": "misconceptions", "title": "M", "questions": ["Q1", "Q2"]},
            ]
        }
        categories = normalize_categories(payload, max_count=20)
        self.assertEqual(len(categories), 3)
        self.assertEqual(categories[0].id, "misconceptions")
        self.assertEqual(categories[1].id, "common_questions")
        self.assertEqual(categories[2].id, "foundations")
        self.assertEqual(categories[0].questions[0].id, "misconceptions_01")

    def test_normalize_categories_deduplicates_questions(self):
        payload = {
            "categories": [
                {"id": "misconceptions", "title": "M", "questions": ["Q1", "Q1"]},
                {"id": "common_questions", "title": "C", "questions": ["Q2"]},
                {"id": "foundations", "title": "F", "questions": ["Q3"]},
            ]
        }
        categories = normalize_categories(payload, max_count=20)
        flat = [q.text for c in categories for q in c.questions]
        self.assertEqual(flat.count("Q1"), 1)
        self.assertEqual(flat.count("Q2"), 1)

    def test_normalize_categories_rejects_unsupported_category_id(self):
        payload = {
            "categories": [
                {"id": "misconceptions", "title": "M", "questions": ["Q1"]},
                {"id": "common_questions", "title": "C", "questions": ["Q2"]},
                {"id": "foundations", "title": "F", "questions": ["Q3"]},
                {"id": "extra", "title": "E", "questions": ["Q5"]},
            ]
        }
        with self.assertRaises(ValidationError):
            normalize_categories(payload, max_count=20)

    def test_normalize_categories_limits_fixed_distribution_counts(self):
        payload = {
            "categories": [
                {"id": "misconceptions", "title": "M", "questions": [f"M{i}" for i in range(12)]},
                {"id": "common_questions", "title": "C", "questions": [f"C{i}" for i in range(12)]},
                {"id": "foundations", "title": "F", "questions": [f"F{i}" for i in range(12)]},
            ]
        }
        categories = normalize_categories(payload, max_count=30)
        self.assertEqual([len(category.questions) for category in categories], [10, 10, 10])


if __name__ == "__main__":
    unittest.main()
