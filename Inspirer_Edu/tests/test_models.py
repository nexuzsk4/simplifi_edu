import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from preset_inspirer_agent.models import LearningContext, ValidationError


class LearningContextTests(unittest.TestCase):
    def test_accepts_all_fields_including_career_context(self):
        context = LearningContext.from_mapping(
            {
                "education_level": "Bachelor",
                "year": "Year 1",
                "faculty": "Science",
                "department": "Mathematics",
                "course": "Calculus 1",
                "topic": "Limits of functions",
                "career_context": "engineering, finance, data science",
                "output_language": "English",
            }
        )
        self.assertEqual(context.topic, "Limits of functions")
        self.assertEqual(context.career_context, "engineering, finance, data science")
        self.assertEqual(context.output_language, "English")

    def test_missing_career_context_becomes_no_data(self):
        context = LearningContext.from_mapping({"course": "Physics", "topic": "Linear motion"})
        self.assertEqual(context.career_context, "ไม่มีข้อมูล")
        self.assertEqual(context.output_language, "Thai")

    def test_accepts_aliases(self):
        context = LearningContext.from_mapping(
            {
                "course": "Physics",
                "careercontext": "robotics",
                "outputlanguage": "English",
            }
        )
        self.assertEqual(context.career_context, "robotics")
        self.assertEqual(context.output_language, "English")

    def test_rejects_extra_fields(self):
        with self.assertRaises(ValidationError):
            LearningContext.from_mapping({"course": "Physics", "topic": "Forces", "school": "extra"})

    def test_rejects_all_context_fields_missing_even_with_career_context(self):
        with self.assertRaises(ValidationError):
            LearningContext.from_mapping({"career_context": "medicine"})

    def test_rejects_non_string_career_context(self):
        with self.assertRaises(ValidationError):
            LearningContext.from_mapping({"course": "Physics", "career_context": ["engineering"]})


if __name__ == "__main__":
    unittest.main()
