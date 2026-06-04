import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from preset_question_agent.models import LearningContext, ValidationError


class LearningContextTests(unittest.TestCase):
    def test_accepts_all_six_fields(self):
        context = LearningContext.from_mapping(
            {
                "education_level": "มัธยม",
                "year": "ม.4",
                "faculty": "-",
                "department": "-",
                "course": "ฟิสิกส์",
                "topic": "การเคลื่อนที่แนวเส้นตรง",
            }
        )
        self.assertEqual(context.course, "ฟิสิกส์")
        self.assertEqual(context.output_language, "Thai")

    def test_rejects_extra_fields(self):
        with self.assertRaises(ValidationError):
            LearningContext.from_mapping(
                {
                    "education_level": "มัธยม",
                    "year": "ม.4",
                    "faculty": "-",
                    "department": "-",
                    "course": "ฟิสิกส์",
                    "topic": "การเคลื่อนที่แนวเส้นตรง",
                    "school": "extra",
                }
            )

    def test_missing_or_empty_fields_become_no_data(self):
        context = LearningContext.from_mapping({"course": "ฟิสิกส์", "topic": ""})
        self.assertEqual(context.course, "ฟิสิกส์")
        self.assertEqual(context.topic, "ไม่มีข้อมูล")
        self.assertEqual(context.faculty, "ไม่มีข้อมูล")

    def test_dash_placeholder_becomes_no_data(self):
        context = LearningContext.from_mapping({"course": "ฟิสิกส์", "faculty": "-", "department": "N/A"})
        self.assertEqual(context.faculty, "ไม่มีข้อมูล")
        self.assertEqual(context.department, "ไม่มีข้อมูล")

    def test_accepts_outputlanguage_alias(self):
        context = LearningContext.from_mapping({"course": "Physics", "outputlanguage": "English"})
        self.assertEqual(context.output_language, "English")

    def test_rejects_conflicting_output_language_aliases(self):
        with self.assertRaises(ValidationError):
            LearningContext.from_mapping(
                {
                    "course": "Physics",
                    "output_language": "Thai",
                    "outputlanguage": "English",
                }
            )

    def test_rejects_all_fields_missing(self):
        with self.assertRaises(ValidationError):
            LearningContext.from_mapping({})


if __name__ == "__main__":
    unittest.main()
