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


SYSTEM_INSTRUCTION = """You are an Education Inspiration Designer.
Create open-ended application prompts that help learners feel why a lesson topic is worth learning.
Lead with visible use cases, real situations, useful problems, and meaningful decisions; connect each prompt back to the lesson through a concrete sub-detail.
These are inspiration prompts, not quizzes, exercises, exam items, homework, textbook checks, or career advice.
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
career_context: {context.career_context}
output_language: {context.output_language}

# Intent
Create prompts for learners who feel bored or wonder why they need this topic.
Each question should make a use case visible and help the learner feel: "This lesson is one of the roots of that real situation."
Focus on open-ended application thinking, not finding the correct answer from the lesson.

# Output Contract
Generate exactly {target_count} questions. Hard max {max_count}.
Also generate 3-6 recommended career or life domains that fit the topic and course.
All category titles, recommended domains, and questions must be in this output language: {context.output_language}.
Use these category IDs in this exact order with fixed counts:
- `everyday_use_cases`: 10 questions. Title should mean "เรื่องใกล้ตัวที่ไม่เคยสังเกต".
- `professional_use_cases`: 10 questions. Title should mean "งานที่ใช้ความรู้นี้จริง".
- `future_ideas`: 10 questions. Title should mean "ไอเดียที่อยากลองสร้าง".

# Silent Method
1. Infer 8-12 lesson-detail anchors from the actual input topic. An anchor must be a specific sub-detail taught inside the topic: a property, relationship, quantity, representation, condition, operation, method, model, edge case, boundary, exception, or reasoning pattern.
2. Reject broad anchors: the exact topic name, course name, parent field, or generic words like "shape", "system", "data", "technology", "real life", "science", or "math" are not enough.
3. Map those anchors to visible situations, useful problems, tools, products, daily-life systems, work decisions, research questions, or design ideas that fit the discipline and learner level.
4. Write each question so it includes all three pieces: a concrete use case, a specific lesson-detail anchor, and why that anchor matters in the situation.
5. In `everyday_use_cases`, still include the anchor naturally; do not make the question only a daily-life observation.
6. If removing the anchor would make the question fit many unrelated topics, rewrite it with a more specific anchor.
7. Use career_context when it has data; otherwise infer suitable domains from the topic and course.
8. Do not output the anchor list.

# Quality Rules
- Write natural open-ended prompts that can start discussion. Several answers may be reasonable.
- Do not write quiz, exam, definition, formula, theorem-recall, calculation, proof, or homework-style questions.
- Do not use the exact topic phrase as the lesson-detail anchor. Prefer a narrower sub-detail; the exact topic phrase should appear only when it makes the question clearer.
- Do not make the use case so detached that a learner cannot see why it belongs to this topic.
- Avoid bot templates like "How is [topic] applied in [field]?" or "How does [profession] use [topic]?".
- Avoid vague bridges such as only saying "เกี่ยวข้องกับ", "นำไปใช้", "ใช้แนวคิด", or "ประยุกต์ใช้" without a specific lesson detail.
- Avoid parent-field bridges such as only saying "รูปทรงเรขาคณิต", "การคำนวณ", "ข้อมูล", "ระบบ", or "เทคโนโลยี" when a topic-specific anchor is needed.
- Vary sentence openings and application frames across the 30 questions.

# Output JSON Schema
Use this shape. Include all three categories in the exact order shown.
{{
  "recommended_career_domains": ["career domain in output_language", "career domain in output_language"],
  "categories": [
    {{
      "id": "everyday_use_cases",
      "title": "category title in output_language",
      "questions": ["question in output_language", "question in output_language"]
    }},
    {{
      "id": "professional_use_cases",
      "title": "category title in output_language",
      "questions": ["question in output_language", "question in output_language"]
    }},
    {{
      "id": "future_ideas",
      "title": "category title in output_language",
      "questions": ["question in output_language", "question in output_language"]
    }}
  ]
}}
"""
    return PromptBundle(system=SYSTEM_INSTRUCTION, user=user)
