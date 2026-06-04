from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


DEFAULT_PROVIDER = "gemini"
DEFAULT_MODEL = "gemini-2.5-flash-lite"
DEFAULT_TEMPERATURE = 0.3


@dataclass(frozen=True)
class Settings:
    provider: str
    model: str
    temperature: float
    api_key: str | None
    env_file: Path


def package_root() -> Path:
    return Path(__file__).resolve().parents[2]


def workspace_root() -> Path:
    root = package_root()
    parent = root.parent
    if (parent / "Simplifi_Edu").is_dir() and (parent / "Inspirer_Edu").is_dir():
        return parent
    return root


def default_env_path() -> Path:
    return workspace_root() / ".env"


def parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def load_settings(
    provider: str | None = None,
    model: str | None = None,
    env_file: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Settings:
    env_path = Path(env_file) if env_file else default_env_path()
    file_values = parse_env_file(env_path)
    process_values = dict(os.environ if environ is None else environ)

    def get_value(key: str, fallback: str | None = None) -> str | None:
        return process_values.get(key) or file_values.get(key) or fallback

    resolved_provider = (
        provider
        or get_value("PRESET_LLM_PROVIDER")
        or get_value("LLM_PROVIDER", DEFAULT_PROVIDER)
        or DEFAULT_PROVIDER
    ).strip()
    resolved_model = (
        model
        or get_value("PRESET_LLM_MODEL")
        or get_value("LLM_MODEL", DEFAULT_MODEL)
        or DEFAULT_MODEL
    ).strip()
    raw_temperature = get_value("PRESET_LLM_TEMPERATURE") or get_value("LLM_TEMPERATURE", str(DEFAULT_TEMPERATURE))
    try:
        resolved_temperature = float(raw_temperature or DEFAULT_TEMPERATURE)
    except ValueError:
        resolved_temperature = DEFAULT_TEMPERATURE

    if resolved_provider == "gemini":
        api_key = get_value("PRESET_GEMINI_API_KEY") or get_value("GEMINI_API_KEY")
    elif resolved_provider == "openai":
        api_key = get_value("PRESET_OPENAI_API_KEY") or get_value("OPENAI_API_KEY")
    else:
        api_key = None

    return Settings(
        provider=resolved_provider,
        model=resolved_model,
        temperature=resolved_temperature,
        api_key=api_key,
        env_file=env_path,
    )
