# Model Cost Notes

Pricing snapshot date: 2026-05-28.

Always verify prices before production rollout because model pricing and aliases change.

## Default Recommendation

Use `gemini-2.5-flash-lite` as the default for high-volume, disposable frontend suggestions. It is cheap, fast, supports structured output, and is enough for generating exactly 30 Thai academic preset questions.

## Supported Text Models

Prices are USD per 1M tokens.

| Provider | Model | Input | Cached Input | Output | Suggested Use |
| --- | ---: | ---: | ---: | ---: | --- |
| Gemini | `gemini-2.5-flash-lite` | 0.10 | 0.01 | 0.40 | Default high-volume preset generation |
| Gemini | `gemini-2.5-flash` | 0.30 | 0.03 | 2.50 | Better quality fallback |
| Gemini | `gemini-3-flash-preview` | 0.50 | 0.05 | 3.00 | Preview quality test, not default |
| OpenAI | `gpt-5-nano` | 0.05 | 0.005 | 0.40 | Cheapest OpenAI fallback |
| OpenAI | `gpt-4.1-nano` | 0.10 | 0.025 | 0.40 | Legacy nano fallback |
| OpenAI | `gpt-5.4-nano` | 0.20 | 0.02 | 1.25 | Newer nano option |
| OpenAI | `gpt-5-mini` | 0.25 | 0.025 | 2.00 | Stronger low-cost option |
| OpenAI | `gpt-4.1-mini` | 0.40 | 0.10 | 1.60 | Strong instruction-following fallback |
| OpenAI | `gpt-5.4-mini` | 0.75 | 0.075 | 4.50 | Stronger mini option |

## Cost Formula

```text
input_cost = input_tokens / 1_000_000 * input_price
cached_input_cost = cached_input_tokens / 1_000_000 * cached_input_price
output_cost = output_tokens / 1_000_000 * output_price
total_cost = input_cost + cached_input_cost + output_cost
```

The package computes this from provider token usage when available.

## Example Estimate

For a typical small request with 1,200 input tokens and 700 output tokens:

| Model | Estimated Cost |
| --- | ---: |
| `gemini-2.5-flash-lite` | $0.000400 |
| `gpt-5-nano` | $0.000340 |
| `gpt-4.1-mini` | $0.001600 |

## Official Sources

- Google Gemini API pricing: https://ai.google.dev/gemini-api/docs/pricing
- OpenAI pricing: https://developers.openai.com/api/docs/pricing
- OpenAI `gpt-5-nano`: https://developers.openai.com/api/docs/models/gpt-5-nano
- OpenAI `gpt-4.1-mini`: https://developers.openai.com/api/docs/models/gpt-4.1-mini
