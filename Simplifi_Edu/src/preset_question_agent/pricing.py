from __future__ import annotations

from dataclasses import asdict, dataclass

from .models import TokenUsage, ValidationError


@dataclass(frozen=True)
class ModelPricing:
    provider: str
    model: str
    input_per_1m_usd: float
    output_per_1m_usd: float
    cached_input_per_1m_usd: float | None = None


@dataclass(frozen=True)
class CostEstimate:
    model: str
    input_cost_usd: float
    cached_input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float

    def to_dict(self) -> dict[str, float | str]:
        return asdict(self)


PRICE_TABLE: dict[str, ModelPricing] = {
    "gemini-2.5-flash-lite": ModelPricing("gemini", "gemini-2.5-flash-lite", 0.10, 0.40, 0.01),
    "gemini-2.5-flash": ModelPricing("gemini", "gemini-2.5-flash", 0.30, 2.50, 0.03),
    "gemini-3-flash-preview": ModelPricing("gemini", "gemini-3-flash-preview", 0.50, 3.00, 0.05),
    "gpt-5-nano": ModelPricing("openai", "gpt-5-nano", 0.05, 0.40, 0.005),
    "gpt-4.1-nano": ModelPricing("openai", "gpt-4.1-nano", 0.10, 0.40, 0.025),
    "gpt-5.4-nano": ModelPricing("openai", "gpt-5.4-nano", 0.20, 1.25, 0.02),
    "gpt-5-mini": ModelPricing("openai", "gpt-5-mini", 0.25, 2.00, 0.025),
    "gpt-4.1-mini": ModelPricing("openai", "gpt-4.1-mini", 0.40, 1.60, 0.10),
    "gpt-5.4-mini": ModelPricing("openai", "gpt-5.4-mini", 0.75, 4.50, 0.075),
}


def estimate_cost(model: str, usage: TokenUsage) -> CostEstimate:
    if model not in PRICE_TABLE:
        raise ValidationError(f"No pricing configured for model: {model}")

    pricing = PRICE_TABLE[model]
    input_tokens = max(usage.input_tokens - usage.cached_input_tokens, 0)
    input_cost = (input_tokens / 1_000_000) * pricing.input_per_1m_usd
    cached_rate = pricing.cached_input_per_1m_usd
    cached_cost = 0.0
    if cached_rate is not None:
        cached_cost = (usage.cached_input_tokens / 1_000_000) * cached_rate
    else:
        cached_cost = (usage.cached_input_tokens / 1_000_000) * pricing.input_per_1m_usd
    output_cost = (usage.output_tokens / 1_000_000) * pricing.output_per_1m_usd
    total = input_cost + cached_cost + output_cost

    return CostEstimate(
        model=model,
        input_cost_usd=round(input_cost, 9),
        cached_input_cost_usd=round(cached_cost, 9),
        output_cost_usd=round(output_cost, 9),
        total_cost_usd=round(total, 9),
    )
