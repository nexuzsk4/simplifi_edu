import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from preset_question_agent.models import LearningContext
from preset_question_agent.prompt import MAX_QUESTION_COUNT, MIN_QUESTION_COUNT, TARGET_QUESTION_COUNT, build_prompt


class PromptTests(unittest.TestCase):
    def test_prompt_contains_context_and_language_instruction(self):
        context = LearningContext.from_mapping(
            {
                "education_level": "Bachelor",
                "year": "Year 1",
                "faculty": "Science",
                "department": "Mathematics",
                "course": "Calculus 1",
                "topic": "Limits of functions",
                "output_language": "English",
            }
        )
        prompt = build_prompt(context).as_single_prompt()

        self.assertIn("education_level: Bachelor", prompt)
        self.assertIn("year: Year 1", prompt)
        self.assertIn("faculty: Science", prompt)
        self.assertIn("department: Mathematics", prompt)
        self.assertIn("course: Calculus 1", prompt)
        self.assertIn("topic: Limits of functions", prompt)
        self.assertIn("output_language: English", prompt)
        self.assertIn("All category titles and questions must be in this output language: English", prompt)
        self.assertNotIn("course_data", prompt)

    def test_prompt_uses_fixed_category_contract(self):
        context = LearningContext.from_mapping({"course": "Physics", "topic": "Linear motion"})
        prompt = build_prompt(context).as_single_prompt()

        self.assertEqual(TARGET_QUESTION_COUNT, 30)
        self.assertEqual(MIN_QUESTION_COUNT, 30)
        self.assertEqual(MAX_QUESTION_COUNT, 30)
        self.assertIn("Generate exactly 30 preset questions", prompt)
        self.assertIn("Hard max 30", prompt)
        self.assertIn("exact order", prompt)
        self.assertIn("`misconceptions`: 10 questions", prompt)
        self.assertIn("`common_questions`: 10 questions", prompt)
        self.assertIn("`foundations`: 10 questions", prompt)
        self.assertIn('"id": "misconceptions"', prompt)
        self.assertIn('"id": "common_questions"', prompt)
        self.assertIn('"id": "foundations"', prompt)
        self.assertNotIn("`applications`", prompt)

    def test_prompt_uses_universal_lesson_detail_anchor_method(self):
        context = LearningContext.from_mapping(
            {
                "education_level": "Master",
                "faculty": "Pharmacy",
                "department": "Clinical Pharmacy",
                "course": "Advanced Pharmacotherapy 1",
                "topic": "Medication use in pregnancy and breastfeeding",
            }
        )
        prompt = build_prompt(context).as_single_prompt()

        self.assertIn("Infer 8-12 lesson-detail anchors", prompt)
        self.assertIn("specific sub-detail taught inside the topic", prompt)
        self.assertIn("property, relationship, quantity, representation", prompt)
        self.assertIn("condition, operation, method, model", prompt)
        self.assertIn("edge case, boundary, exception", prompt)
        self.assertIn("reasoning pattern", prompt)
        self.assertIn("Do not output the anchor list", prompt)

    def test_prompt_rejects_broad_anchors_and_topic_stuffing(self):
        context = LearningContext.from_mapping({"course": "Social Studies", "topic": "Welfare policy"})
        prompt = build_prompt(context).as_single_prompt()

        self.assertIn("Reject broad anchors", prompt)
        self.assertIn("exact topic name", prompt)
        self.assertIn("course name", prompt)
        self.assertIn("parent field", prompt)
        self.assertIn('generic words like "concept", "system", "data"', prompt)
        self.assertIn("real life", prompt)
        self.assertIn("topic stuffing", prompt)
        self.assertIn("If removing the anchor would make the question fit many unrelated topics", prompt)

    def test_prompt_controls_depth_without_old_level_taxonomy(self):
        context = LearningContext.from_mapping(
            {
                "education_level": "Bachelor",
                "year": "Year 1",
                "course": "Calculus 1",
                "topic": "Limits and continuity",
            }
        )
        prompt = build_prompt(context).as_single_prompt()

        self.assertIn("one level below the topic", prompt)
        self.assertIn("Adapt depth to the learner level", prompt)
        self.assertIn("go deeper within the learner's level", prompt)
        self.assertIn("do not add advanced or graduate framing unless the input explicitly implies it", prompt)
        self.assertNotIn("Depth By Level", prompt)
        self.assertNotIn("Doctoral: critique", prompt)

    def test_prompt_frames_categories_as_deep_academic_inquiry(self):
        context = LearningContext.from_mapping(
            {
                "course": "Microbial Proteomics",
                "topic": "Proteomics and microbial protein analysis",
            }
        )
        prompt = build_prompt(context).as_single_prompt()

        self.assertIn("`misconceptions`: questions that reveal mistaken assumptions", prompt)
        self.assertIn("boundary confusion", prompt)
        self.assertIn("overgeneralization", prompt)
        self.assertIn("`common_questions`: natural questions a learner might ask", prompt)
        self.assertIn("specific sub-detail", prompt)
        self.assertIn("`foundations`: deep foundation questions", prompt)
        self.assertIn("Direct definition questions are allowed only when framed through relation", prompt)
        self.assertIn("boundary, condition, representation, or why-it-matters", prompt)

    def test_prompt_forbids_quiz_exercise_and_case_solving_style(self):
        context = LearningContext.from_mapping(
            {
                "education_level": "Bachelor",
                "faculty": "Science",
                "department": "Mathematics",
                "course": "Calculus 1",
                "topic": "Limits and continuity",
            }
        )
        prompt = build_prompt(context).as_single_prompt()

        self.assertIn("not exercises", prompt)
        self.assertIn("homework tasks", prompt)
        self.assertIn("quizzes", prompt)
        self.assertIn("exams", prompt)
        self.assertIn("Do not write quiz, exam, homework, exercise", prompt)
        self.assertIn("formula-recall", prompt)
        self.assertIn("calculation", prompt)
        self.assertIn("proof", prompt)
        self.assertIn("solve", prompt)
        self.assertIn("calculate", prompt)
        self.assertIn("find the value", prompt)
        self.assertIn("Do not invent specific values, functions, statutes", prompt)
        self.assertIn("case facts, patient data, datasets, passages, or scenarios", prompt)

    def test_prompt_removes_old_bloated_prompt_sections(self):
        context = LearningContext.from_mapping({"course": "Economics", "topic": "Elasticity"})
        prompt = build_prompt(context).as_single_prompt()

        self.assertNotIn("Discipline Anchors", prompt)
        self.assertNotIn("Quantitative / math / physics / engineering", prompt)
        self.assertNotIn("Law: doctrines, elements/tests", prompt)
        self.assertNotIn("Medicine / health / pharmacy", prompt)
        self.assertNotIn("Social science", prompt)
        self.assertNotIn("Humanities / language / arts", prompt)
        self.assertNotIn("Business / economics", prompt)
        self.assertNotIn("8-12 central sub-concepts", prompt)
        self.assertNotIn("applications", prompt)


if __name__ == "__main__":
    unittest.main()
