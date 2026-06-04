from __future__ import annotations

import json
import re
from typing import Any, Mapping

from .models import (
    REQUIRED_CATEGORY_IDS,
    Category,
    InspirerQuestionResult,
    LearningContext,
    Question,
    ValidationError,
)
from .pricing import estimate_cost
from .prompt import MAX_QUESTION_COUNT, MIN_QUESTION_COUNT, TARGET_QUESTION_COUNT, build_prompt
from .providers import LLMProvider


CATEGORY_QUESTION_COUNTS = {
    "everyday_use_cases": 10,
    "professional_use_cases": 10,
    "future_ideas": 10,
}


class PresetInspirerGenerator:
    def __init__(
        self,
        provider: LLMProvider,
        target_count: int = TARGET_QUESTION_COUNT,
        min_count: int = MIN_QUESTION_COUNT,
        max_count: int = MAX_QUESTION_COUNT,
    ) -> None:
        self.provider = provider
        self.target_count = target_count
        self.min_count = min_count
        self.max_count = max_count

    def build_prompt(self, data: Mapping[str, Any]):
        context = LearningContext.from_mapping(data)
        return build_prompt(context, target_count=self.target_count, max_count=self.max_count)

    def generate(self, data: Mapping[str, Any]) -> InspirerQuestionResult:
        context = LearningContext.from_mapping(data)
        prompt = build_prompt(context, target_count=self.target_count, max_count=self.max_count)
        response = self.provider.generate(prompt)
        payload = parse_json_payload(response.text)
        recommended_career_domains = normalize_recommended_career_domains(payload)
        categories = normalize_categories(payload, max_count=self.max_count)
        total_questions = sum(len(category.questions) for category in categories)
        if total_questions < self.min_count:
            raise ValidationError(f"Generated only {total_questions} questions; expected at least {self.min_count}")

        estimated_cost = None
        try:
            estimated_cost = estimate_cost(response.model, response.usage).total_cost_usd
        except ValidationError:
            estimated_cost = None

        return InspirerQuestionResult(
            version="1.0",
            language=context.output_language,
            context=context,
            recommended_career_domains=recommended_career_domains,
            provider=response.provider,
            model=response.model,
            total_questions=total_questions,
            categories=categories,
            usage=response.usage,
            estimated_cost_usd=estimated_cost,
        )


def parse_json_payload(text: str) -> dict[str, Any]:
    cleaned = text.strip().lstrip("\ufeff").strip()
    cleaned = _strip_code_fence(cleaned)
    cleaned = _extract_json_object(cleaned)
    payload = _load_json_object(cleaned)
    if not isinstance(payload, dict):
        raise ValidationError("Provider response must be a JSON object")
    return payload


def _load_json_object(text: str) -> Any:
    attempts = (text, _repair_common_json_issues(text))
    last_error: json.JSONDecodeError | None = None
    for candidate in attempts:
        try:
            return json.loads(candidate, strict=False)
        except json.JSONDecodeError as exc:
            last_error = exc

    if last_error is None:
        raise ValidationError("Provider response is not valid JSON")
    raise ValidationError(_format_json_error(last_error, text)) from last_error


def _repair_common_json_issues(text: str) -> str:
    # Most malformed structured-output responses we see are valid JSON except
    # for a trailing comma before a closing object/array.
    return re.sub(r",\s*([}\]])", r"\1", text)


def _format_json_error(error: json.JSONDecodeError, text: str) -> str:
    preview = text[:500].replace("\n", "\\n").replace("\r", "\\r")
    context_start = max(0, error.pos - 250)
    context_end = min(len(text), error.pos + 250)
    error_context = text[context_start:context_end].replace("\n", "\\n").replace("\r", "\\r")
    return (
        "Provider response is not valid JSON "
        f"(line {error.lineno}, column {error.colno}). Raw preview: {preview}. "
        f"Error context: {error_context}"
    )


def _strip_code_fence(text: str) -> str:
    cleaned = text.strip()
    if not cleaned.startswith("```"):
        return cleaned

    lines = cleaned.splitlines()
    if len(lines) >= 2 and lines[0].strip().startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return cleaned.strip("`").strip()


def _extract_json_object(text: str) -> str:
    start = text.find("{")
    if start == -1:
        return text

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1].strip()

    return text[start:].strip()


def normalize_recommended_career_domains(payload: Mapping[str, Any], max_domains: int = 8) -> tuple[str, ...]:
    raw_domains = payload.get("recommended_career_domains")
    if not isinstance(raw_domains, list):
        raise ValidationError("Provider response must contain recommended_career_domains as a list")

    domains: list[str] = []
    seen_domains: set[str] = set()
    for raw_domain in raw_domains:
        if len(domains) >= max_domains:
            break
        if not isinstance(raw_domain, str):
            raise ValidationError("recommended_career_domains must contain strings only")
        domain = " ".join(raw_domain.strip().split())
        if not domain or domain in seen_domains:
            continue
        seen_domains.add(domain)
        domains.append(domain)

    if not domains:
        raise ValidationError("recommended_career_domains must contain at least one non-empty value")
    return tuple(domains)


def normalize_categories(payload: Mapping[str, Any], max_count: int = MAX_QUESTION_COUNT) -> tuple[Category, ...]:
    raw_categories = payload.get("categories")
    if not isinstance(raw_categories, list):
        raise ValidationError("Provider response must contain categories as a list")

    categories_by_id: dict[str, Category] = {}
    seen_questions: set[str] = set()

    for raw_category in raw_categories:
        if not isinstance(raw_category, Mapping):
            raise ValidationError("Each category must be an object")
        category_id = _read_string(raw_category, "id")
        if category_id not in REQUIRED_CATEGORY_IDS:
            raise ValidationError(f"Unsupported category id: {category_id}")
        title = _read_string(raw_category, "title")
        raw_questions = raw_category.get("questions")
        if not isinstance(raw_questions, list):
            raise ValidationError(f"{category_id}.questions must be a list")

        existing = categories_by_id.get(category_id)
        questions = list(existing.questions) if existing else []
        category_limit = CATEGORY_QUESTION_COUNTS[category_id]
        for raw_question in raw_questions:
            if len(questions) >= category_limit:
                break
            if not isinstance(raw_question, str):
                raise ValidationError(f"{category_id}.questions must contain strings only")
            question_text = " ".join(raw_question.strip().split())
            if not question_text or question_text in seen_questions:
                continue
            seen_questions.add(question_text)
            question_number = len(questions) + 1
            questions.append(
                Question(
                    id=f"{category_id}_{question_number:02d}",
                    text=question_text,
                )
            )

        if questions:
            categories_by_id[category_id] = Category(id=category_id, title=title, questions=tuple(questions))

    category_ids = set(categories_by_id)
    missing_required = [category_id for category_id in REQUIRED_CATEGORY_IDS if category_id not in category_ids]
    if missing_required:
        raise ValidationError("Missing required categories: " + ", ".join(missing_required))

    categories = tuple(categories_by_id[category_id] for category_id in REQUIRED_CATEGORY_IDS)
    total = sum(len(category.questions) for category in categories)
    if total > max_count:
        raise ValidationError(f"Generated {total} questions; expected at most {max_count}")
    return tuple(categories)


def _read_string(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{key} must be a non-empty string")
    return value.strip()
