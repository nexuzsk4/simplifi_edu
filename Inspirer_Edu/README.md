# Preset Inspirer Agent Core

Core Python package for generating open-ended application prompts that help learners see why a lesson matters in real life, real work, and future ideas.

The agent is designed for learners who feel burned out or wonder "why am I learning this?" Each question should make a visible use case concrete, connect it to a specific lesson detail inside the topic, and invite curiosity rather than test recall.

Input fields:

- `education_level`
- `year`
- `faculty`
- `department`
- `course`
- `topic`
- `career_context`
- `output_language` or `outputlanguage`

Each of the 6 learning-context fields is optional at runtime, but at least one of them must contain data. Missing, empty, null, `-`, `no data`, and `ไม่มีข้อมูล` are normalized to `ไม่มีข้อมูล`.

`career_context` is optional. If it is missing, empty, or null, the model infers suitable career or discipline domains from the topic and course. `output_language` defaults to `Thai` when omitted. Unknown extra fields are rejected.

The LLM prompt is written in English to reduce prompt token cost and improve model consistency, while generated category titles, career domains, and questions are forced to match `output_language`.

Default live generation temperature is `0.3` for more varied prompts while keeping applications factual, realistic, and topic-specific. Inside the monorepo it reads the shared root `../.env` by default; if used standalone, it falls back to `.env` inside this folder.

## Output Contract

Each successful generation returns:

- `recommended_career_domains`: 3-6 career or professional domains
- `categories`: exactly 3 categories and 30 questions total

Category IDs and counts:

- `everyday_use_cases`: 10 questions, title meaning "เรื่องใกล้ตัวที่ไม่เคยสังเกต"
- `professional_use_cases`: 10 questions, title meaning "งานที่ใช้ความรู้นี้จริง"
- `future_ideas`: 10 questions, title meaning "ไอเดียที่อยากลองสร้าง"

Question text is the whole product. There are no extra fields such as `lesson_anchor` or `rationale`; each question must carry the real situation, the lesson/sub-detail relation, and the application meaning by itself.

The generator rejects quiz-style framing in the prompt design. Output should not be homework, exercises, formula recall, proofs, or closed questions asking for one exact answer.

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

## Build Prompt Only

```powershell
preset-inspirer --dry-run --course "Calculus 1" --topic "Limits of functions" --output-language English
```

With an explicit career direction:

```powershell
preset-inspirer --dry-run --course "Biology" --topic "Cell signaling" --career-context "medicine, biotechnology, drug discovery"
```

Or pass a partial context. Blank fields are allowed:

```powershell
preset-inspirer --dry-run --topic "อินทิกรัลตามผิว"
```

## Live API Run

1. From the monorepo root, copy `.env.example` to `.env`.
2. Put your provider key in the root `.env`.
3. Run from `Inspirer_Edu`:

```powershell
preset-inspirer --course "Physics" --topic "Linear motion" --output-language English
```

Each successful generation is auto-saved as JSON in `run_outputs/` with:

- `input`
- `output`
- `usage`
- `cost_usd` including USD breakdown, `total_cost_thb` using rate 33, and status
- `processing_time_seconds`

Default live provider/model comes from the shared root `.env` and is `gemini` / `gemini-2.5-flash-lite`. Override it with:

```powershell
preset-inspirer --provider openai --model gpt-5-nano --course "Economics" --topic "Elasticity"
```

Environment variables:

- `LLM_PROVIDER`, `LLM_MODEL`, `LLM_TEMPERATURE` for shared defaults
- `GEMINI_API_KEY` or `OPENAI_API_KEY` for shared provider keys
- optional `INSPIRER_LLM_PROVIDER`, `INSPIRER_LLM_MODEL`, `INSPIRER_LLM_TEMPERATURE` for Inspirer-only overrides
- optional `INSPIRER_GEMINI_API_KEY` or `INSPIRER_OPENAI_API_KEY` for Inspirer-only provider keys

Disable file saving for one run:

```powershell
preset-inspirer --course "Physics" --topic "Linear motion" --no-save
```

## Unit Tests

```powershell
python -m unittest discover -s tests
```

## Streamlit Playground

Use this if you want a quick UI for live testing in a separate playground. Input boxes start empty and show Thai placeholders.

Run playground:

```powershell
streamlit run playground/app.py
```

The playground uses the same core generator and writes run records to JSON (`run_outputs/`) with input, output, cost summary, and processing time.

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
- optional `INSPIRER_LLM_PROVIDER`, `INSPIRER_LLM_MODEL`, `INSPIRER_LLM_TEMPERATURE` for Inspirer-only overrides
