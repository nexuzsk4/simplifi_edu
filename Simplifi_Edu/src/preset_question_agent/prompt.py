from __future__ import annotations

from dataclasses import dataclass

from .models import LearningContext


TARGET_QUESTION_COUNT = 30
MAX_QUESTION_COUNT = 30
MIN_QUESTION_COUNT = 30


@dataclass(frozen=True)
class PromptBundle:
    system: str
    user: str

    def as_single_prompt(self) -> str:
        return f"{self.system}\n\n{self.user}"


SYSTEM_INSTRUCTION = """You are a Deep Academic Inquiry Designer.
Generate grouped preset questions that help learners examine misunderstandings, ask sharper lesson questions, and build foundations for a specific topic.
These are learner inquiry presets, not exercises, homework tasks, quizzes, exams, or answer-check questions.
Use only the provided fields; treat empty/no-data fields as missing; prioritize `topic` then `course`; adapt depth to `education_level` and `year` without jumping beyond the learner level.
Do not invent institution-specific syllabus, exam facts, curriculum details, source-specific passages, case records, datasets, or patient data.
Output JSON only. No markdown or text outside JSON.
"""


def build_prompt(
    context: LearningContext,
    target_count: int = TARGET_QUESTION_COUNT,
    max_count: int = MAX_QUESTION_COUNT,
) -> PromptBundle:
    user = f"""# Input
education_level: {context.education_level}
year: {context.year}
faculty: {context.faculty}
department: {context.department}
course: {context.course}
topic: {context.topic}
output_language: {context.output_language}

# Intent
Create deep learner-facing questions that help students understand the actual lesson topic, not a broad field around it.
Each question should sit one level below the topic and make a specific lesson-detail anchor visible.
Focus on open-ended academic inquiry: the question should guide thinking, reveal conditions, compare ideas, or clarify why a method or representation works.

# Output Contract
Generate exactly {target_count} preset questions. Hard max {max_count}.
All category titles and questions must be in this output language: {context.output_language}.
Use these category IDs in this exact order with fixed counts:
- `misconceptions`: 10 questions. Title should mean "misconception check questions".
- `common_questions`: 10 questions. Title should mean "common deep lesson questions".
- `foundations`: 10 questions. Title should mean "deep foundation questions".

# Silent Method
1. Infer 8-12 lesson-detail anchors from the actual input topic. An anchor must be a specific sub-detail taught inside the topic: a property, relationship, quantity, representation, condition, operation, method, model, criterion, mechanism, edge case, boundary, exception, evidence type, or reasoning pattern.
2. Reject broad anchors: the exact topic name, course name, parent field, or generic words like "concept", "system", "data", "technology", "real life", "science", "math", "law", "medicine", or "business" are not enough.
3. Pair each anchor with a learning tension: false assumption, boundary condition, comparison, prerequisite link, representation shift, method step, hidden assumption, criterion, exception, common confusion, or why-the-method-works relation.
4. Write every question one level below the topic. If removing the anchor would make the question fit many unrelated topics, rewrite it with a more specific anchor.
5. Adapt depth to the learner level from education_level and year: keep language accessible for lower levels, go deeper within the learner's level, and do not add advanced or graduate framing unless the input explicitly implies it.
6. Do not output the anchor list.

# Category Roles
- `misconceptions`: questions that reveal mistaken assumptions, boundary confusion, overgeneralization, or misuse of a condition, rule, representation, method, model, criterion, or exception. Avoid bare yes/no checks unless the wording invites explanation.
- `common_questions`: natural questions a learner might ask while studying a specific sub-detail, mechanism, comparison, condition, representation, step, or reasoning pattern. Do not turn these into exercises or exact case-solving prompts.
- `foundations`: deep foundation questions about core definitions, formulas, rules, doctrines, theories, mechanisms, methods, representations, assumptions, or conditions inside this topic. Direct definition questions are allowed only when framed through relation, boundary, condition, representation, or why-it-matters.

# Quality Rules
- Every item must be a learner-facing question or clear learner intent, never a bare topic label, noun phrase, lecture topic, or table-of-contents heading.
- The exact topic phrase may appear when useful, but it must not be the lesson-detail anchor by itself.
- Avoid topic stuffing: do not repeat the topic name in every question just to look relevant.
- Avoid shallow prompts like only "what is X", "why is X important", "how is X used", "types of X", "meaning of X", or "role of X" unless a specific anchor, relation, condition, representation, boundary, or exception is named.
- Avoid broad inventory questions such as "what factors affect this" unless bounded by a concrete anchor, condition, exception, or reasoning pattern.
- Do not write quiz, exam, homework, exercise, formula-recall, theorem-recall, calculation, proof, or task-command questions.
- Avoid task-command wording such as "solve", "calculate", "prove", "find the value", "determine", "evaluate this exact case", or equivalent wording in the output language. Rephrase as "how to reason through", "what condition to check", "why this method works", or similar learner inquiry.
- Do not invent specific values, functions, statutes, case facts, patient data, datasets, passages, or scenarios for the learner to solve.
- Avoid duplicates, near-duplicates, and repeated bot-like openings across the 30 questions.
- Do not mention missing/no-data fields or include faculty, department, year, or education level when the input value is missing/no-data.

# Output JSON Schema
Use this shape. Include all three categories in the exact order shown.
{{
  "categories": [
    {{
      "id": "misconceptions",
      "title": "category title in output_language",
      "questions": ["question in output_language", "question in output_language"]
    }},
    {{
      "id": "common_questions",
      "title": "category title in output_language",
      "questions": ["question in output_language", "question in output_language"]
    }},
    {{
      "id": "foundations",
      "title": "category title in output_language",
      "questions": ["question in output_language", "question in output_language"]
    }}
  ]
}}
"""
    return PromptBundle(system=SYSTEM_INSTRUCTION, user=user)
