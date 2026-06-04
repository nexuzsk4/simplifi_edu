from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import TokenUsage, ValidationError
from .prompt import PromptBundle


OPENAI_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "recommended_career_domains": {
            "type": "array",
            "minItems": 1,
            "maxItems": 8,
            "items": {"type": "string"},
        },
        "categories": {
            "type": "array",
            "minItems": 3,
            "maxItems": 3,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "questions": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 10,
                        "items": {"type": "string"},
                    },
                },
                "required": ["id", "title", "questions"],
            },
        },
    },
    "required": ["recommended_career_domains", "categories"],
}


@dataclass(frozen=True)
class LLMResponse:
    text: str
    usage: TokenUsage
    provider: str
    model: str


class LLMProvider(Protocol):
    provider: str
    model: str

    def generate(self, prompt: PromptBundle) -> LLMResponse:
        ...


class GeminiProvider:
    provider = "gemini"

    def __init__(self, model: str, api_key: str, temperature: float = 0.3) -> None:
        if not api_key:
            raise ValidationError("INSPIRER_GEMINI_API_KEY or GEMINI_API_KEY is required for GeminiProvider")
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("Install Gemini support with: pip install -e .[gemini]") from exc

        self.model = model
        self.temperature = temperature
        self._client = genai.Client(api_key=api_key)
        self._types = types

    def generate(self, prompt: PromptBundle) -> LLMResponse:
        response = self._client.models.generate_content(
            model=self.model,
            contents=prompt.as_single_prompt(),
            config=self._types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=self._build_response_schema(),
                max_output_tokens=4096,
                temperature=self.temperature,
            ),
        )
        usage_metadata = getattr(response, "usage_metadata", None)
        usage = TokenUsage(
            input_tokens=int(getattr(usage_metadata, "prompt_token_count", 0) or 0),
            output_tokens=int(getattr(usage_metadata, "candidates_token_count", 0) or 0),
        )
        return LLMResponse(
            text=response.text,
            usage=usage,
            provider=self.provider,
            model=self.model,
        )

    def _build_response_schema(self):
        string_schema = self._types.Schema(type=self._types.Type.STRING)
        category_schema = self._types.Schema(
            type=self._types.Type.OBJECT,
            required=["id", "title", "questions"],
            property_ordering=["id", "title", "questions"],
            properties={
                "id": self._types.Schema(type=self._types.Type.STRING),
                "title": self._types.Schema(type=self._types.Type.STRING),
                "questions": self._types.Schema(
                    type=self._types.Type.ARRAY,
                    min_items=1,
                    max_items=10,
                    items=string_schema,
                ),
            },
        )
        return self._types.Schema(
            type=self._types.Type.OBJECT,
            required=["recommended_career_domains", "categories"],
            property_ordering=["recommended_career_domains", "categories"],
            properties={
                "recommended_career_domains": self._types.Schema(
                    type=self._types.Type.ARRAY,
                    min_items=1,
                    max_items=8,
                    items=string_schema,
                ),
                "categories": self._types.Schema(
                    type=self._types.Type.ARRAY,
                    min_items=3,
                    max_items=3,
                    items=category_schema,
                ),
            },
        )


class OpenAIProvider:
    provider = "openai"

    def __init__(self, model: str, api_key: str, temperature: float = 0.3) -> None:
        if not api_key:
            raise ValidationError("INSPIRER_OPENAI_API_KEY or OPENAI_API_KEY is required for OpenAIProvider")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install OpenAI support with: pip install -e .[openai]") from exc

        self.model = model
        self.temperature = temperature
        self._client = OpenAI(api_key=api_key)

    def generate(self, prompt: PromptBundle) -> LLMResponse:
        response = self._client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": prompt.system},
                {"role": "user", "content": prompt.user},
            ],
            temperature=self.temperature,
            max_output_tokens=4096,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "preset_inspirer_questions",
                    "schema": OPENAI_RESPONSE_SCHEMA,
                    "strict": True,
                }
            },
        )
        usage_metadata = getattr(response, "usage", None)
        usage = TokenUsage(
            input_tokens=int(getattr(usage_metadata, "input_tokens", 0) or 0),
            output_tokens=int(getattr(usage_metadata, "output_tokens", 0) or 0),
        )
        return LLMResponse(
            text=response.output_text,
            usage=usage,
            provider=self.provider,
            model=self.model,
        )


def make_provider(provider: str, model: str, api_key: str | None, temperature: float = 0.3) -> LLMProvider:
    if provider == "gemini":
        return GeminiProvider(model=model, api_key=api_key or "", temperature=temperature)
    if provider == "openai":
        return OpenAIProvider(model=model, api_key=api_key or "", temperature=temperature)
    raise ValidationError(f"Unsupported provider: {provider}")
