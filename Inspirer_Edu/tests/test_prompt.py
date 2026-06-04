import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from preset_inspirer_agent.models import LearningContext
from preset_inspirer_agent.prompt import MAX_QUESTION_COUNT, MIN_QUESTION_COUNT, TARGET_QUESTION_COUNT, build_prompt


class PromptTests(unittest.TestCase):
    def test_prompt_contains_context_and_language_contract(self):
        context = LearningContext.from_mapping(
            {
                "education_level": "Bachelor",
                "year": "Year 1",
                "faculty": "Science",
                "department": "Mathematics",
                "course": "Calculus 1",
                "topic": "Limits of functions",
                "career_context": "engineering and finance",
                "output_language": "English",
            }
        )
        prompt = build_prompt(context).as_single_prompt()

        self.assertIn("education_level: Bachelor", prompt)
        self.assertIn("course: Calculus 1", prompt)
        self.assertIn("topic: Limits of functions", prompt)
        self.assertIn("career_context: engineering and finance", prompt)
        self.assertIn("output_language: English", prompt)
        self.assertIn("All category titles, recommended domains, and questions", prompt)

    def test_prompt_uses_target_counts_and_new_category_contract(self):
        context = LearningContext.from_mapping({"course": "Physics", "topic": "Linear motion"})
        prompt = build_prompt(context).as_single_prompt()

        self.assertEqual(TARGET_QUESTION_COUNT, 30)
        self.assertEqual(MIN_QUESTION_COUNT, 30)
        self.assertEqual(MAX_QUESTION_COUNT, 30)
        self.assertIn("Generate exactly 30", prompt)
        self.assertIn("Hard max 30", prompt)
        self.assertIn("`everyday_use_cases`: 10 questions", prompt)
        self.assertIn("`professional_use_cases`: 10 questions", prompt)
        self.assertIn("`future_ideas`: 10 questions", prompt)
        self.assertIn('"recommended_career_domains"', prompt)

    def test_prompt_is_compact_inspiration_first_single_call(self):
        context = LearningContext.from_mapping({"course": "Biology", "topic": "Cell signaling"})
        prompt = build_prompt(context).as_single_prompt()

        self.assertIn("Education Inspiration Designer", prompt)
        self.assertIn("learners who feel bored", prompt)
        self.assertIn("This lesson is one of the roots of that real situation", prompt)
        self.assertIn("open-ended application thinking", prompt)
        self.assertIn("Silent Method", prompt)
        self.assertIn("Do not output the anchor list", prompt)

    def test_prompt_requires_visible_use_case_and_lesson_detail_relation(self):
        context = LearningContext.from_mapping({"course": "Vector Calculus", "topic": "Surface integrals"})
        prompt = build_prompt(context).as_single_prompt()

        self.assertIn("Infer 8-12 lesson-detail anchors", prompt)
        self.assertIn("property, relationship, quantity, representation", prompt)
        self.assertIn("operation, method, model, edge case", prompt)
        self.assertIn("concrete use case", prompt)
        self.assertIn("specific lesson-detail anchor", prompt)
        self.assertIn("why that anchor matters", prompt)
        self.assertIn("everyday_use_cases", prompt)
        self.assertIn("do not make the question only a daily-life observation", prompt)

    def test_prompt_rejects_topic_name_and_parent_field_as_anchor(self):
        context = LearningContext.from_mapping({"course": "Mathematics", "topic": "Conic sections"})
        prompt = build_prompt(context).as_single_prompt()

        self.assertIn("Reject broad anchors", prompt)
        self.assertIn("exact topic name", prompt)
        self.assertIn("course name", prompt)
        self.assertIn("parent field", prompt)
        self.assertIn("shape", prompt)
        self.assertIn("system", prompt)
        self.assertIn("data", prompt)
        self.assertIn("If removing the anchor would make the question fit many unrelated topics", prompt)

    def test_prompt_rejects_quiz_bot_and_vague_application_styles(self):
        context = LearningContext.from_mapping({"course": "Mathematics", "topic": "Conic sections"})
        prompt = build_prompt(context).as_single_prompt()

        self.assertIn("Do not write quiz, exam, definition, formula", prompt)
        self.assertIn("Do not use the exact topic phrase as the lesson-detail anchor", prompt)
        self.assertIn("How is [topic] applied in [field]", prompt)
        self.assertIn("How does [profession] use [topic]", prompt)
        self.assertIn("เกี่ยวข้องกับ", prompt)
        self.assertIn("นำไปใช้", prompt)
        self.assertIn("ประยุกต์ใช้", prompt)
        self.assertIn("รูปทรงเรขาคณิต", prompt)
        self.assertIn("การคำนวณ", prompt)
        self.assertIn("parent-field bridges", prompt)
        self.assertIn("Vary sentence openings", prompt)

    def test_prompt_omits_old_bloated_sections_and_old_category_ids(self):
        context = LearningContext.from_mapping({"course": "Calculus 1", "topic": "Limits and continuity"})
        prompt = build_prompt(context).as_single_prompt()

        self.assertNotIn("Lesson-Detail Bridge", prompt)
        self.assertNotIn("Topic Anchor Coverage", prompt)
        self.assertNotIn("Grounding Standard", prompt)
        self.assertNotIn("real_world_applications", prompt)
        self.assertNotIn("career_connections", prompt)
        self.assertNotIn("creative_problem_framing", prompt)


if __name__ == "__main__":
    unittest.main()
