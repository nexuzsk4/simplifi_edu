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


SYSTEM_INSTRUCTION = """You are an Academic Curriculum & Pedagogy Expert.
Generate grouped preset questions that help learners fill understanding gaps and study a specific topic more deeply.
These are learning inquiry presets, not exercises, homework tasks, quizzes, or exam items.
Use only the provided fields; treat empty/no-data fields as missing; prioritize `topic` then `course`; adapt depth to `education_level` and `year`.
Do not invent institution-specific syllabus, exam facts, or curriculum details.
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

# Task
Generate exactly {target_count} preset questions. Hard max {max_count}.
All category titles and questions must be in this output language: {context.output_language}.

# Silent Planning (do not output)
1. Classify the discipline from faculty, department, course, and topic.
2. Infer 8-12 central sub-concepts inside this topic at the given education level.
3. For each sub-concept, choose concrete anchors and blind spots: formula, symbol, graph, doctrine, legal test, method, model, metric, mechanism, criterion, exception, case/fact pattern, evidence type, patient factor, text feature, scenario variable, or other discipline-specific term.
4. Write questions one level below the topic. If a question would still work after replacing this topic with another topic in the same course, it is too broad; rewrite it.

# Discipline Anchors (use only matching lines)
- Quantitative / math / physics / engineering: formulas, derivations, graphs, units, assumptions, edge cases, calculation mistakes.
- Law: doctrines, elements/tests, exceptions, statutory interpretation, case reasoning, burden of proof, policy tensions, fact patterns.
- Medicine / health / pharmacy: mechanisms, criteria, differential reasoning, contraindications, PK/PD, dose adjustment, monitoring, patient-specific risk, safety/ethics.
- Social science: theories, constructs, causal claims, evidence, research design, measurement, competing explanations.
- Humanities / language / arts: interpretation, context, form, rhetoric, schools of thought, textual evidence, critique.
- Business / economics: models, assumptions, metrics, tradeoffs, incentives, constraints, scenario analysis.

# Depth By Level
Use the closest matching level only; do not add graduate research framing to lower-level contexts unless the input explicitly asks for it.
- Primary / early secondary: concrete language, simple examples, minimal core concepts.
- Upper secondary: rules/formulas/terms, standard problem patterns, graph/text interpretation, common mistakes.
- Bachelor: concept-method links, procedures, assumptions, boundary cases, cross-topic links.
- Master: methodology, model/theory comparison, limitations, evidence quality, advanced exceptions.
- Doctoral: critique, methodological choices, assumptions, scholarly debates, research gaps, competing frameworks.

# Categories
Use these IDs in this exact order with fixed counts: `misconceptions` 10 questions, `common_questions` 10 questions, `foundations` 10 questions.
- misconceptions: learner questions that check mistaken assumptions, boundary confusion, overgeneralization, or misuse of a rule/method. Title should mean "misconception check questions". Do not write statements or headings. Good patterns: "Does X always imply Y", "Can X be used interchangeably with Y", "Why does X not necessarily mean Y".
- common_questions: natural lesson questions about specific sub-concepts, boundaries, mechanisms, conditions, comparisons, or explanations. Do not write exercises, computational prompts, exact case-solving prompts, or subtopic labels such as "meaning of X", "role of Y", or "application of Z".
- foundations: core definitions, formulas, doctrines, theories, methods, representations, or conditions inside this topic only.

# Item Rules
- Every item must be a learner-facing question or clear learner intent, never a bare topic label, noun phrase, lecture topic, or table-of-contents heading.
- A question mark is optional, but question intent is required.
- Avoid plain yes/no questions except misconception checks that invite explanation.
- Avoid duplicates and near-duplicates.
- Avoid broad inventory questions like "what factors affect this" or "what are the types" unless bounded by a concrete anchor, condition, exception, or scenario.
- Do not ask only "what is it", "why is it important", or "how is it used" unless a specific anchor is named.
- Avoid task-command wording such as "solve", "calculate", "prove", "find the value", "determine", "consider this exact case", "จง", "คำนวณ", "หา", or "พิสูจน์". Rephrase as "how to reason through", "what condition to check", "why this method works", or equivalent in the output language.
- Do not ask the learner to solve a specific invented problem.
- In `common_questions`, do not invent specific values, functions, statutes, case facts, patient data, datasets, passages, or scenarios for the learner to evaluate. Ask about the concept, condition, comparison, or reasoning pattern instead.
- Bad common question: "What is the limit of f(x)=(x^2-4)/(x-2) as x approaches 2". Good: "Why does factoring reveal a removable discontinuity when direct substitution gives 0/0".
- Bad common question: "Is this specific case lawful under doctrine X". Good: "Which elements of doctrine X decide whether a fact pattern is lawful".
- Bad common question: "How should this patient's dose be adjusted from creatinine clearance 35 mL/min". Good: "Which renal function and monitoring factors guide dose adjustment".
- At least 80% of questions must contain a concrete topic anchor.
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
