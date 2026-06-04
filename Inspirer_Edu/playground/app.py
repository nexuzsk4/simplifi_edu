from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from concurrent.futures import ThreadPoolExecutor
import importlib
import math
import time
import json
import sys

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from preset_inspirer_agent.cli import build_run_record, write_run_record
from preset_inspirer_agent.config import load_settings
from preset_inspirer_agent.models import ValidationError
from preset_inspirer_agent.providers import make_provider
from preset_inspirer_agent.service import PresetInspirerGenerator


DEFAULT_OUTPUT_DIR = "run_outputs"
WORKSPACE_ROOT = ROOT.parent
DEFAULT_ENV_FILE = str(
    WORKSPACE_ROOT / ".env"
    if (WORKSPACE_ROOT / "Simplifi_Edu").is_dir() and (WORKSPACE_ROOT / "Inspirer_Edu").is_dir()
    else ROOT / ".env"
)


def main() -> None:
    st.set_page_config(page_title="Preset Inspirer Playground", layout="wide")
    st.title("Preset Inspirer Playground")
    st.caption("Interactive live playground for open-ended inspirational use-case questions.")

    st.subheader("Input")
    education_level = st.text_input("education_level", value="", placeholder="เช่น มัธยมศึกษา, ปริญญาตรี")
    year = st.text_input("year", value="", placeholder="เช่น ม.4, ปี 1")
    faculty = st.text_input("faculty", value="", placeholder="เช่น วิทยาศาสตร์")
    department = st.text_input("department", value="", placeholder="เช่น คณิตศาสตร์")
    course = st.text_input("course", value="", placeholder="เช่น คณิตศาสตร์, แคลคูลัส 1")
    topic = st.text_input("topic", value="", placeholder="เช่น ภาคตัดกรวย, อินทิกรัลตามผิว")
    career_context = st.text_area(
        "career_context (Optional)",
        value="",
        placeholder="ถ้ามีศาสตร์หรืออาชีพที่อยากเชื่อมโยง ใส่เพิ่มได้ เช่น วิศวกรรม, แพทย์, เกม, การเงิน",
        help="เว้นว่างได้ ถ้าไม่กรอก ระบบจะให้โมเดล infer ศาสตร์หรืออาชีพที่เหมาะกับหัวข้อเอง",
        height=80,
    )
    output_language = st.selectbox("output_language", options=["Thai", "English"], index=0)

    payload = {
        "education_level": education_level,
        "year": year,
        "faculty": faculty,
        "department": department,
        "course": course,
        "topic": topic,
        "career_context": career_context,
        "output_language": output_language,
    }

    if st.button("Generate", type="primary", use_container_width=True):
        try:
            reload_agent_logic()
            settings = load_settings(env_file=DEFAULT_ENV_FILE)
            llm_provider = make_provider(
                provider=settings.provider,
                model=settings.model,
                api_key=settings.api_key,
                temperature=settings.temperature,
            )

            generator = PresetInspirerGenerator(provider=llm_provider)
            started_at_utc = datetime.now(timezone.utc)
            result, processing_time_seconds = run_with_live_progress(generator=generator, payload=payload)
            completed_at_utc = datetime.now(timezone.utc)

            output_payload = result.to_dict()
            run_record = build_run_record(
                input_payload=payload,
                output_payload=output_payload,
                started_at_utc=started_at_utc,
                completed_at_utc=completed_at_utc,
                processing_time_seconds=processing_time_seconds,
            )
            write_run_record(run_record=run_record, output_dir=DEFAULT_OUTPUT_DIR)

            st.session_state["latest_run_record"] = run_record
            st.session_state["latest_success_message"] = f"Done in {processing_time_seconds} sec."
        except (ValidationError, RuntimeError, ValueError) as exc:
            st.error(str(exc))
        except Exception as exc:  # noqa: BLE001
            st.exception(exc)

    latest_run_record = st.session_state.get("latest_run_record")
    if latest_run_record:
        latest_success_message = st.session_state.get("latest_success_message")
        if latest_success_message:
            st.success(latest_success_message)
        show_summary(run_record=latest_run_record)


def show_summary(run_record: dict) -> None:
    output = run_record["output"]
    cost = run_record["cost_usd"]
    total_cost_thb = cost.get("total_cost_thb")
    total_cost_usd = cost.get("total_cost_usd")
    cost_thb_display = "-"
    if isinstance(total_cost_thb, (float, int)):
        cost_thb_display = f"{total_cost_thb:.6f} THB"

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Provider", output.get("provider", "-"))
    m2.metric("Model", output.get("model", "-"))
    m3.metric("Questions", output.get("total_questions", 0))
    m4.metric("Processing (s)", run_record.get("processing_time_seconds", 0.0))
    m5.metric("Total Cost (THB)", cost_thb_display)
    if isinstance(total_cost_usd, (float, int)):
        st.caption(f"Total cost (USD): {total_cost_usd:.9f}")

    domains = output.get("recommended_career_domains", [])
    if domains:
        st.subheader("Recommended Career Domains")
        st.write(", ".join(domains))

    st.subheader("Categories")
    for category in output.get("categories", []):
        with st.expander(f"{category.get('title', '-')}: {category.get('id', '-')}", expanded=True):
            for item in category.get("questions", []):
                st.write(f"- {item.get('text', '')}")

    with st.expander("Saved Run Record JSON", expanded=False):
        st.code(json.dumps(run_record, ensure_ascii=False, indent=2), language="json")


def run_with_live_progress(generator: PresetInspirerGenerator, payload: dict) -> tuple:
    start_counter = perf_counter()
    progress_bar = st.progress(0, text="Running model...")
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(generator.generate, payload)
        while not future.done():
            elapsed = perf_counter() - start_counter
            progress = min(95, int((1.0 - math.exp(-elapsed / 1.5)) * 100))
            progress_bar.progress(progress, text=f"Running model... {progress}%")
            time.sleep(0.05)
        result = future.result()
    processing_time_seconds = round(perf_counter() - start_counter, 6)
    progress_bar.progress(100, text="Running model... 100%")
    time.sleep(0.05)
    progress_bar.empty()
    return result, processing_time_seconds


def reload_agent_logic() -> None:
    """Reload local agent code so playground runs recent source edits."""
    import preset_inspirer_agent.cli as cli_module
    import preset_inspirer_agent.config as config_module
    import preset_inspirer_agent.models as models_module
    import preset_inspirer_agent.pricing as pricing_module
    import preset_inspirer_agent.prompt as prompt_module
    import preset_inspirer_agent.providers as providers_module
    import preset_inspirer_agent.service as service_module

    global build_run_record, load_settings, make_provider, PresetInspirerGenerator, ValidationError, write_run_record

    importlib.reload(models_module)
    importlib.reload(prompt_module)
    importlib.reload(pricing_module)
    importlib.reload(config_module)
    importlib.reload(providers_module)
    importlib.reload(service_module)
    importlib.reload(cli_module)

    build_run_record = cli_module.build_run_record
    load_settings = config_module.load_settings
    make_provider = providers_module.make_provider
    PresetInspirerGenerator = service_module.PresetInspirerGenerator
    ValidationError = models_module.ValidationError
    write_run_record = cli_module.write_run_record


if __name__ == "__main__":
    main()
