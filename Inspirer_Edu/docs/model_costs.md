# Model Cost Notes

The package estimates cost only for models listed in `src/preset_inspirer_agent/pricing.py`.

Configured defaults:

- Provider: `gemini`
- Model: `gemini-2.5-flash-lite`
- Temperature: `0.3`
- THB conversion in run records: `33.0` THB per USD

If a live response uses an unknown model, generation still succeeds but cost status becomes `unavailable`.

Provider/model/temperature can be configured with shared root `.env` names (`LLM_PROVIDER`, `LLM_MODEL`, `LLM_TEMPERATURE`). Provider keys use shared names (`GEMINI_API_KEY`, `OPENAI_API_KEY`) or Inspirer-specific names (`INSPIRER_GEMINI_API_KEY`, `INSPIRER_OPENAI_API_KEY`). Inspirer-specific keys take priority when present.
