# Simplifi Engine

Monorepo for two separate preset-question agents that share the same overall engine style, provider configuration, and local environment file.

## Projects

- `Simplifi_Edu`: academic preset question agent for misconception, common question, and foundation prompts.
- `Inspirer_Edu`: inspiration-first use-case question agent for everyday, professional, and future application prompts.

Each project keeps its own package, CLI, Streamlit playground, tests, and README. The shared `.env` and `.env.example` live at this root folder so both agents use the same provider keys and default model settings.

## Repository Layout

```text
Simplifi_Engine/
  .env
  .env.example
  .gitignore
  README.md
  Simplifi_Edu/
  Inspirer_Edu/
```

## Environment Files

Create one root `.env` for both agents:

```powershell
copy .env.example .env
```

Shared settings used by both agents:

- `LLM_PROVIDER`
- `LLM_MODEL`
- `LLM_TEMPERATURE`
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`

Optional per-agent overrides are still supported when needed:

- Simplifi: `PRESET_LLM_PROVIDER`, `PRESET_LLM_MODEL`, `PRESET_LLM_TEMPERATURE`, `PRESET_GEMINI_API_KEY`, `PRESET_OPENAI_API_KEY`
- Inspirer: `INSPIRER_LLM_PROVIDER`, `INSPIRER_LLM_MODEL`, `INSPIRER_LLM_TEMPERATURE`, `INSPIRER_GEMINI_API_KEY`, `INSPIRER_OPENAI_API_KEY`

The real root `.env` is ignored by Git. Commit only `.env.example`.

## Install Dependencies

Install dependencies for both agents from the root convenience file:

```powershell
pip install -r requirements.txt
```

The subproject `requirements.txt` files are kept because each agent can still be installed, tested, or deployed independently.

## Run Tests

Run each agent from its own folder:

```powershell
cd Simplifi_Edu
python -m unittest discover -s tests

cd ..\Inspirer_Edu
python -m unittest discover -s tests
```

## Run Playgrounds

Both playgrounds read the root `.env` automatically when running inside this monorepo.

```powershell
cd Simplifi_Edu
streamlit run playground/app.py

cd ..\Inspirer_Edu
streamlit run playground/app.py
```

## Git Notes

Use this root folder as the only Git repository. Subproject folders should not contain their own `.git` directories.

Generated outputs, virtual environments, caches, and real `.env` files are ignored at the root level.