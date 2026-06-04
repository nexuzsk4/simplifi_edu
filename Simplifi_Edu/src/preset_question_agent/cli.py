from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import re
from time import perf_counter
import sys
from pathlib import Path
from uuid import uuid4
from typing import Any

from .config import load_settings
from .models import LearningContext, TokenUsage, ValidationError
from .pricing import estimate_cost
from .prompt import build_prompt
from .providers import make_provider
from .service import PresetQuestionGenerator

THB_PER_USD = 33.0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    context_data = load_context_data(args)

    if args.dry_run:
        context = LearningContext.from_mapping(context_data)
        prompt = build_prompt(context)
        print(json.dumps({"system": prompt.system, "user": prompt.user}, ensure_ascii=False, indent=2))
        return 0

    settings = load_settings(provider=args.provider, model=args.model, env_file=args.env_file)
    provider = make_provider(
        provider=settings.provider,
        model=settings.model,
        api_key=settings.api_key,
        temperature=args.temperature if args.temperature is not None else settings.temperature,
    )

    generator = PresetQuestionGenerator(provider=provider)
    started_at_utc = datetime.now(timezone.utc)
    start_counter = perf_counter()
    result = generator.generate(context_data)
    processing_time_seconds = round(perf_counter() - start_counter, 6)
    completed_at_utc = datetime.now(timezone.utc)
    result_payload = result.to_dict()
    print(json.dumps(result_payload, ensure_ascii=False, indent=2))
    print(f"\nLLM processing_time_seconds: {processing_time_seconds}")

    if not args.no_save:
        run_record = build_run_record(
            input_payload=context_data,
            output_payload=result_payload,
            started_at_utc=started_at_utc,
            completed_at_utc=completed_at_utc,
            processing_time_seconds=processing_time_seconds,
        )
        output_path = write_run_record(run_record=run_record, output_dir=args.output_dir)
        print(f"\nSaved run output: {output_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate grouped academic preset questions.")
    parser.add_argument("--input-json", type=str, help="Path to JSON file containing any context fields plus output_language.")
    parser.add_argument("--education-level", type=str)
    parser.add_argument("--year", type=str)
    parser.add_argument("--faculty", type=str)
    parser.add_argument("--department", type=str)
    parser.add_argument("--course", type=str)
    parser.add_argument("--topic", type=str)
    parser.add_argument("--output-language", "--outputlanguage", dest="output_language", type=str)
    parser.add_argument("--provider", choices=["gemini", "openai"], help="Live provider override.")
    parser.add_argument("--model", type=str, help="Live model override.")
    parser.add_argument("--env-file", type=str, help="Path to shared .env file.")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Print the generated prompt only.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="run_outputs",
        help="Directory for saved JSON run outputs (default: run_outputs).",
    )
    parser.add_argument("--no-save", action="store_true", help="Do not save output JSON to disk.")
    return parser


def load_context_data(args: argparse.Namespace) -> dict[str, Any]:
    if args.input_json:
        path = Path(args.input_json)
        return json.loads(path.read_text(encoding="utf-8"))

    values = {
        "education_level": args.education_level,
        "year": args.year,
        "faculty": args.faculty,
        "department": args.department,
        "course": args.course,
        "topic": args.topic,
        "output_language": args.output_language,
    }
    context_values = {key: values[key] for key in ("education_level", "year", "faculty", "department", "course", "topic")}
    if all(value is None for value in context_values.values()):
        raise SystemExit("Provide --input-json or at least one of the 6 context flags.")
    return values


def build_run_record(
    input_payload: dict[str, Any],
    output_payload: dict[str, Any],
    started_at_utc: datetime | None = None,
    completed_at_utc: datetime | None = None,
    processing_time_seconds: float | None = None,
) -> dict[str, Any]:
    if started_at_utc is None:
        started_at_utc = datetime.now(timezone.utc)
    if completed_at_utc is None:
        completed_at_utc = datetime.now(timezone.utc)
    if processing_time_seconds is None:
        processing_time_seconds = 0.0

    usage = output_payload.get("usage", {})
    cost_usd = build_cost_summary(output_payload=output_payload, usage_payload=usage)
    return {
        "run_id": str(uuid4()),
        "created_at_utc": completed_at_utc.isoformat(),
        "started_at_utc": started_at_utc.isoformat(),
        "completed_at_utc": completed_at_utc.isoformat(),
        "processing_time_seconds": processing_time_seconds,
        "input": input_payload,
        "output": output_payload,
        "cost_usd": cost_usd,
    }


def build_cost_summary(output_payload: dict[str, Any], usage_payload: dict[str, Any]) -> dict[str, Any]:
    model = output_payload.get("model")
    try:
        usage_input = int(usage_payload.get("input_tokens", 0) or 0)
        usage_output = int(usage_payload.get("output_tokens", 0) or 0)
        usage_cached = int(usage_payload.get("cached_input_tokens", 0) or 0)
    except (TypeError, ValueError):
        usage_input, usage_output, usage_cached = 0, 0, 0

    if model:
        try:
            estimate = estimate_cost(
                model=model,
                usage=TokenUsage(
                    input_tokens=usage_input,
                    output_tokens=usage_output,
                    cached_input_tokens=usage_cached,
                ),
            )
            return {
                "status": "calculated_from_usage",
                "model": model,
                "input_cost_usd": estimate.input_cost_usd,
                "cached_input_cost_usd": estimate.cached_input_cost_usd,
                "output_cost_usd": estimate.output_cost_usd,
                "total_cost_usd": estimate.total_cost_usd,
                "total_cost_thb": round(estimate.total_cost_usd * THB_PER_USD, 9),
                "thb_rate": THB_PER_USD,
            }
        except ValidationError:
            pass

    fallback_total_usd = output_payload.get("estimated_cost_usd")
    fallback_total_thb = None
    if isinstance(fallback_total_usd, (float, int)):
        fallback_total_thb = round(float(fallback_total_usd) * THB_PER_USD, 9)

    return {
        "status": "unavailable",
        "model": model,
        "input_cost_usd": None,
        "cached_input_cost_usd": None,
        "output_cost_usd": None,
        "total_cost_usd": fallback_total_usd,
        "total_cost_thb": fallback_total_thb,
        "thb_rate": THB_PER_USD,
    }


def write_run_record(run_record: dict[str, Any], output_dir: str) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    sequence_number = next_output_sequence(output_path)
    topic_name = build_output_topic_name(run_record)
    filename = f"output_{sequence_number}_{topic_name}.json"
    full_path = output_path / filename
    full_path.write_text(json.dumps(run_record, ensure_ascii=False, indent=2), encoding="utf-8")
    return full_path.resolve()


def next_output_sequence(output_path: Path) -> int:
    max_sequence = 0
    for path in output_path.glob("output_*_*.json"):
        match = re.match(r"output_(\d+)_", path.name)
        if match:
            max_sequence = max(max_sequence, int(match.group(1)))
    return max_sequence + 1


def build_output_topic_name(run_record: dict[str, Any]) -> str:
    input_payload = run_record.get("input", {})
    topic = input_payload.get("topic") or input_payload.get("course") or "untitled"
    return sanitize_filename_part(str(topic))


def sanitize_filename_part(value: str, max_length: int = 80) -> str:
    cleaned = " ".join(value.strip().split())
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    cleaned = cleaned.strip(" .-_")
    if not cleaned:
        cleaned = "untitled"
    return cleaned[:max_length].strip(" .-_") or "untitled"


if __name__ == "__main__":
    sys.exit(main())
