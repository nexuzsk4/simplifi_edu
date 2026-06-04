import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from preset_inspirer_agent.models import TokenUsage, ValidationError
from preset_inspirer_agent.providers import LLMResponse
from preset_inspirer_agent.service import (
    PresetInspirerGenerator,
    normalize_categories,
    normalize_recommended_career_domains,
    parse_json_payload,
)


class FakeProvider:
    provider = "fake"
    model = "gemini-2.5-flash-lite"

    def generate(self, prompt):
        payload = {
            "recommended_career_domains": ["Engineering", "Data science", "Product design"],
            "categories": [
                {
                    "id": "everyday_use_cases",
                    "title": "Real",
                    "questions": [f"R{i}" for i in range(10)],
                },
                {
                    "id": "professional_use_cases",
                    "title": "Career",
                    "questions": [f"C{i}" for i in range(10)],
                },
                {
                    "id": "future_ideas",
                    "title": "Create",
                    "questions": [f"P{i}" for i in range(10)],
                },
            ],
        }
        import json

        return LLMResponse(
            text=json.dumps(payload),
            usage=TokenUsage(input_tokens=1200, output_tokens=700),
            provider=self.provider,
            model=self.model,
        )


class ServiceTests(unittest.TestCase):
    def test_parse_json_payload_accepts_object(self):
        payload = parse_json_payload('{"categories": [], "recommended_career_domains": []}')
        self.assertIn("categories", payload)

    def test_parse_json_payload_repairs_trailing_commas(self):
        payload = parse_json_payload('{"categories": [], "recommended_career_domains": [],}')
        self.assertIn("recommended_career_domains", payload)

    def test_parse_json_payload_error_includes_preview(self):
        with self.assertRaisesRegex(ValidationError, "Error context"):
            parse_json_payload("not json")

    def test_normalize_recommended_career_domains_deduplicates_and_limits(self):
        domains = normalize_recommended_career_domains(
            {
                "recommended_career_domains": [
                    " Engineering ",
                    "Engineering",
                    "Data science",
                    "Product design",
                    "Medicine",
                    "Law",
                    "Business",
                    "Robotics",
                    "Architecture",
                    "Extra",
                ]
            }
        )
        self.assertEqual(domains[0], "Engineering")
        self.assertEqual(len(domains), 8)

    def test_normalize_recommended_career_domains_rejects_empty(self):
        with self.assertRaises(ValidationError):
            normalize_recommended_career_domains({"recommended_career_domains": ["", "  "]})

    def test_normalize_categories_enforces_required_ids_and_order(self):
        payload = {
            "categories": [
                {"id": "professional_use_cases", "title": "C", "questions": ["Q2"]},
                {"id": "everyday_use_cases", "title": "R", "questions": ["Q1"]},
                {"id": "future_ideas", "title": "P", "questions": ["Q3"]},
            ]
        }
        categories = normalize_categories(payload, max_count=30)
        self.assertEqual([category.id for category in categories], [
            "everyday_use_cases",
            "professional_use_cases",
            "future_ideas",
        ])
        self.assertEqual(categories[0].questions[0].id, "everyday_use_cases_01")

    def test_normalize_categories_rejects_unsupported_category_id(self):
        payload = {
            "categories": [
                {"id": "everyday_use_cases", "title": "R", "questions": ["Q1"]},
                {"id": "professional_use_cases", "title": "C", "questions": ["Q2"]},
                {"id": "future_ideas", "title": "P", "questions": ["Q3"]},
                {"id": "extra", "title": "E", "questions": ["Q4"]},
            ]
        }
        with self.assertRaises(ValidationError):
            normalize_categories(payload, max_count=30)

    def test_normalize_categories_limits_fixed_distribution_counts(self):
        payload = {
            "categories": [
                {"id": "everyday_use_cases", "title": "R", "questions": [f"R{i}" for i in range(12)]},
                {"id": "professional_use_cases", "title": "C", "questions": [f"C{i}" for i in range(12)]},
                {"id": "future_ideas", "title": "P", "questions": [f"P{i}" for i in range(12)]},
            ]
        }
        categories = normalize_categories(payload, max_count=30)
        self.assertEqual([len(category.questions) for category in categories], [10, 10, 10])

    def test_generator_returns_recommended_career_domains(self):
        generator = PresetInspirerGenerator(provider=FakeProvider())
        result = generator.generate({"course": "Physics", "topic": "Linear motion", "output_language": "English"})

        self.assertEqual(result.total_questions, 30)
        self.assertEqual(result.recommended_career_domains, ("Engineering", "Data science", "Product design"))
        self.assertEqual(result.to_dict()["recommended_career_domains"][0], "Engineering")


if __name__ == "__main__":
    unittest.main()
