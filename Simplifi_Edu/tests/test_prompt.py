import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from preset_question_agent.models import LearningContext
from preset_question_agent.prompt import MAX_QUESTION_COUNT, MIN_QUESTION_COUNT, TARGET_QUESTION_COUNT, build_prompt


class PromptTests(unittest.TestCase):
    def test_prompt_contains_context_and_no_course_data_reference(self):
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

    def test_prompt_uses_target_counts_and_category_contract(self):
        context = LearningContext.from_mapping({"course": "Physics", "topic": "Linear motion"})
        prompt = build_prompt(context).as_single_prompt()

        self.assertEqual(TARGET_QUESTION_COUNT, 30)
        self.assertEqual(MIN_QUESTION_COUNT, 30)
        self.assertEqual(MAX_QUESTION_COUNT, 30)
        self.assertIn("Generate exactly 30", prompt)
        self.assertIn("Hard max 30", prompt)
        self.assertIn("exact order", prompt)
        self.assertIn("`misconceptions` 10 questions", prompt)
        self.assertIn("`common_questions` 10 questions", prompt)
        self.assertIn("`foundations` 10 questions", prompt)
        self.assertNotIn("`applications`", prompt)

    def test_prompt_keeps_discipline_and_depth_coverage(self):
        context = LearningContext.from_mapping(
            {
                "education_level": "Doctoral",
                "faculty": "Law",
                "department": "Public Law",
                "course": "Advanced Jurisprudence",
                "topic": "Constitutional interpretation",
            }
        )
        prompt = build_prompt(context).as_single_prompt()

        self.assertIn("Classify the discipline", prompt)
        self.assertIn("8-12 central sub-concepts", prompt)
        self.assertIn("Discipline Anchors", prompt)
        self.assertIn("Quantitative / math / physics / engineering", prompt)
        self.assertIn("Law: doctrines, elements/tests", prompt)
        self.assertIn("Medicine / health / pharmacy", prompt)
        self.assertIn("Social science", prompt)
        self.assertIn("Humanities / language / arts", prompt)
        self.assertIn("Business / economics", prompt)
        self.assertIn("Depth By Level", prompt)
        self.assertIn("Doctoral: critique", prompt)
        self.assertIn("scholarly debates", prompt)
        self.assertIn("research gaps", prompt)

    def test_prompt_enforces_specific_learner_intent_items(self):
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

        self.assertIn("one level below the topic", prompt)
        self.assertIn("If a question would still work", prompt)
        self.assertIn("too broad", prompt)
        self.assertIn("Every item must be a learner-facing question", prompt)
        self.assertIn("never a bare topic label", prompt)
        self.assertIn("A question mark is optional", prompt)
        self.assertIn("question intent is required", prompt)
        self.assertIn("At least 80% of questions", prompt)
        self.assertIn("concrete topic anchor", prompt)
        self.assertIn("what factors affect this", prompt)

    def test_prompt_frames_misconceptions_and_common_questions(self):
        context = LearningContext.from_mapping(
            {
                "course": "Microbial Proteomics",
                "topic": "Proteomics and microbial protein analysis",
            }
        )
        prompt = build_prompt(context).as_single_prompt()

        self.assertIn("misconceptions: learner questions that check mistaken assumptions", prompt)
        self.assertIn("Title should mean \"misconception check questions\"", prompt)
        self.assertIn("Do not write statements or headings", prompt)
        self.assertIn("Does X always imply Y", prompt)
        self.assertIn("Can X be used interchangeably with Y", prompt)
        self.assertIn("Why does X not necessarily mean Y", prompt)
        self.assertIn("common_questions: natural lesson questions", prompt)
        self.assertIn("or subtopic labels", prompt)
        self.assertIn("meaning of X", prompt)

    def test_prompt_avoids_exercise_style_questions(self):
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

        self.assertIn("learning inquiry presets, not exercises", prompt)
        self.assertIn("homework tasks, quizzes, or exam items", prompt)
        self.assertIn("natural lesson questions", prompt)
        self.assertIn("Do not write exercises", prompt)
        self.assertIn("Do not ask the learner to solve a specific invented problem", prompt)
        self.assertIn("Avoid task-command wording", prompt)
        self.assertIn("calculate", prompt)
        self.assertIn("find the value", prompt)
        self.assertIn("จง", prompt)
        self.assertIn("how to reason through", prompt)
        self.assertIn("what condition to check", prompt)
        self.assertIn("do not invent specific values, functions, statutes, case facts", prompt)
        self.assertIn("datasets, passages, or scenarios", prompt)
        self.assertIn("What is the limit of f(x)=(x^2-4)/(x-2)", prompt)
        self.assertIn("Why does factoring reveal a removable discontinuity", prompt)
        self.assertIn("Which elements of doctrine X", prompt)
        self.assertIn("Which renal function and monitoring factors", prompt)


if __name__ == "__main__":
    unittest.main()
