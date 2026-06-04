from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


CONTEXT_FIELDS = (
    "education_level",
    "year",
    "faculty",
    "department",
    "course",
    "topic",
)
CAREER_CONTEXT_FIELD = "career_context"
OUTPUT_LANGUAGE_FIELD = "output_language"
INPUT_FIELDS = CONTEXT_FIELDS + (CAREER_CONTEXT_FIELD, OUTPUT_LANGUAGE_FIELD)
INPUT_ALIASES = {"outputlanguage": OUTPUT_LANGUAGE_FIELD, "careercontext": CAREER_CONTEXT_FIELD}
DEFAULT_OUTPUT_LANGUAGE = "Thai"
NO_DATA = "ไม่มีข้อมูล"
NO_DATA_MARKERS = {"", "-", "n/a", "na", "none", "null", "no data", "ไม่มีข้อมูล", "ไม่มี"}

REQUIRED_CATEGORY_IDS = ("everyday_use_cases", "professional_use_cases", "future_ideas")


class ValidationError(ValueError):
    """Raised when an input or generated response does not match the contract."""


@dataclass(frozen=True)
class LearningContext:
    education_level: str
    year: str
    faculty: str
    department: str
    course: str
    topic: str
    career_context: str
    output_language: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "LearningContext":
        data = _normalize_aliases(data)
        keys = set(data.keys())
        allowed = set(INPUT_FIELDS)
        extra = sorted(keys - allowed)
        if extra:
            raise ValidationError("LearningContext contains unsupported fields: " + ", ".join(extra))

        normalized: dict[str, str] = {}
        has_any_context = False
        for field_name in CONTEXT_FIELDS:
            value = data.get(field_name)
            if field_name == "year" and isinstance(value, (int, float)) and not isinstance(value, bool):
                value = str(value)
            normalized_value = _normalize_optional_text(value, field_name)
            normalized[field_name] = normalized_value
            if normalized_value != NO_DATA:
                has_any_context = True

        if not has_any_context:
            raise ValidationError("At least one of the 6 input fields must contain data")

        normalized[CAREER_CONTEXT_FIELD] = _normalize_optional_text(data.get(CAREER_CONTEXT_FIELD), CAREER_CONTEXT_FIELD)
        normalized[OUTPUT_LANGUAGE_FIELD] = _normalize_output_language(data.get(OUTPUT_LANGUAGE_FIELD))

        return cls(**normalized)

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def _normalize_aliases(data: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(data)
    for alias, canonical in INPUT_ALIASES.items():
        if alias in normalized:
            if canonical in normalized and normalized[canonical] != normalized[alias]:
                raise ValidationError(f"Provide only one of {canonical} or {alias}")
            normalized[canonical] = normalized.pop(alias)
    return normalized


def _normalize_optional_text(value: Any, field_name: str) -> str:
    if value is None:
        return NO_DATA
    if isinstance(value, bool) or not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string, number, empty, or null")
    value = value.strip()
    if value.lower() in NO_DATA_MARKERS:
        return NO_DATA
    return value


def _normalize_output_language(value: Any) -> str:
    if value is None:
        return DEFAULT_OUTPUT_LANGUAGE
    if isinstance(value, bool) or not isinstance(value, str):
        raise ValidationError("output_language must be a non-empty string")
    value = value.strip()
    if value.lower() in NO_DATA_MARKERS:
        return DEFAULT_OUTPUT_LANGUAGE
    return value


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0

    def __post_init__(self) -> None:
        for name, value in (
            ("input_tokens", self.input_tokens),
            ("output_tokens", self.output_tokens),
            ("cached_input_tokens", self.cached_input_tokens),
        ):
            if value < 0:
                raise ValidationError(f"{name} must be >= 0")

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class Question:
    id: str
    text: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class Category:
    id: str
    title: str
    questions: tuple[Question, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "questions": [question.to_dict() for question in self.questions],
        }


@dataclass(frozen=True)
class InspirerQuestionResult:
    version: str
    language: str
    context: LearningContext
    recommended_career_domains: tuple[str, ...]
    provider: str
    model: str
    total_questions: int
    categories: tuple[Category, ...]
    usage: TokenUsage | None = None
    estimated_cost_usd: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "version": self.version,
            "language": self.language,
            "context": self.context.to_dict(),
            "recommended_career_domains": list(self.recommended_career_domains),
            "provider": self.provider,
            "model": self.model,
            "total_questions": self.total_questions,
            "categories": [category.to_dict() for category in self.categories],
        }
        if self.usage is not None:
            result["usage"] = self.usage.to_dict()
        if self.estimated_cost_usd is not None:
            result["estimated_cost_usd"] = self.estimated_cost_usd
        return result
