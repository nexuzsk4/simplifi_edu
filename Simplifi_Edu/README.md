# Preset Question Agent Core

Core Python package for generating grouped academic preset questions from 6 learning-context fields plus one output-language control field:

- `education_level`
- `year`
- `faculty`
- `department`
- `course`
- `topic`
- `output_language` or `outputlanguage`

This package is intentionally separate from `course_data`. It does not read `course_data/.env` or any curriculum files. Inside the monorepo it reads the shared root `../.env` by default; if used standalone, it falls back to `.env` inside this folder.

Each learning-context field is optional at runtime. If a value is missing, empty, or null, the generator treats it as "no data" and builds the prompt from the fields that are available. `output_language` defaults to `Thai` when omitted. Unknown extra fields are rejected.

The LLM prompt is written in English to reduce prompt token cost and improve model consistency, while the generated category titles and questions are forced to match `output_language`.

Default live generation temperature is `0.3` for varied preset suggestions while keeping questions topic-specific.

## Setup

Install package and provider SDK:

```powershell
pip install -e .[gemini]
```

Or for OpenAI:

```powershell
pip install -e .[openai]
```

If you only want to run the Streamlit playground, install from `requirements.txt`:

```powershell
pip install -r requirements.txt
```

## Quick Live Test

```powershell
preset-questions --input-json examples/linear_motion.json
```

## Build Prompt Only

```powershell
preset-questions --dry-run --input-json examples/linear_motion.json
```

## Live API Run

1. From the monorepo root, copy `.env.example` to `.env`.
2. Put your provider key in the root `.env`.
3. Run from `Simplifi_Edu`:

```powershell
preset-questions --input-json examples/linear_motion.json
```

Each successful generation is auto-saved as JSON in `run_outputs/` with:
- `input`
- `output`
- `usage`
- `cost_usd` (includes USD breakdown, `total_cost_thb` using rate 33, and status)

Default live provider/model comes from the shared root `.env` and is `gemini` / `gemini-2.5-flash-lite`. Override it with:

```powershell
preset-questions --provider openai --model gpt-5-nano --input-json examples/linear_motion.json
```

Or pass fields directly:

```powershell
preset-questions --course "Physics" --topic "Linear motion" --output-language English
```

Disable file saving for one run:

```powershell
preset-questions --course "Physics" --topic "Linear motion" --no-save
```

## Unit Tests

```powershell
python -m unittest discover -s tests
```

## Streamlit Playground

Use this if you want a quick UI for live testing in a separate playground.

Run playground:

```powershell
streamlit run playground/app.py
```

The playground uses the same core generator and writes run records to JSON (`run_outputs/`) with:
- input
- output
- cost_usd (including THB conversion)
- processing_time_seconds

## Streamlit Cloud

Use these settings when creating the app:
- Repository: this project repo
- Main file path: `playground/app.py`
- Requirements file: `requirements.txt`

Add secrets in Streamlit Cloud app settings:
- `GEMINI_API_KEY` or `OPENAI_API_KEY`
- `LLM_PROVIDER`
- `LLM_MODEL`
- `LLM_TEMPERATURE`
- optional `PRESET_LLM_PROVIDER`, `PRESET_LLM_MODEL`, `PRESET_LLM_TEMPERATURE` for Simplifi-only overrides
