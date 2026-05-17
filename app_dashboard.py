import time
import streamlit as st

from core_telemetry import SystemTelemetryMatrix
from cognitive_brain import LLMAgentBrain
from runtime_executor import RuntimeExecutionOrchestrator


st.set_page_config(page_title="Mythos 2.0 - Operational Core", page_icon="🧠", layout="wide")

if "sensor" not in st.session_state:
    st.session_state.sensor = SystemTelemetryMatrix()
    st.session_state.brain = LLMAgentBrain(sensor_node=st.session_state.sensor)
    st.session_state.orchestrator = RuntimeExecutionOrchestrator(brain_node=st.session_state.brain)
    st.session_state.logs = []
    st.session_state.auto_refresh = False
    st.session_state.refresh_interval = 2
    st.session_state.last_result = None

st.title("🧠 Mythos 2.0: Operational AI Core")
st.subheader("Autonomous Multi-Agent Feedback Control Loop")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ Core Controls")
    auto_refresh = st.checkbox("Activate Framework Loop", value=st.session_state.auto_refresh)
    refresh_interval = st.slider("Sensor Refresh Interval (Seconds)", 1, 10, st.session_state.refresh_interval)
    run_once = st.button("Run Single Cycle", use_container_width=True)
    clear_logs = st.button("Clear Logs", use_container_width=True)

    st.session_state.auto_refresh = auto_refresh
    st.session_state.refresh_interval = refresh_interval

    if clear_logs:
        st.session_state.logs = []
        st.session_state.last_result = None

def execute_cycle():
    result = st.session_state.orchestrator.run_autonomous_pipeline(
        "Maintain stable machine operational matrix."
    )
    st.session_state.last_result = result

    log_line = (
        f"[{time.strftime('%H:%M:%S')}] "
        f"{result['verdict']} | "
        f"{result['execution_priority']} | "
        f"{result['reasoning_topology']}"
    )
    st.session_state.logs.insert(0, log_line)
    st.session_state.logs = st.session_state.logs[:20]

if run_once:
    execute_cycle()

if st.session_state.auto_refresh:
    execute_cycle()

col1, col2 = st.columns([1, 2])

with col1:
    st.header("📊 Live System Telemetry")

    result = st.session_state.last_result
    telemetry = result["telemetry"] if result else st.session_state.sensor.capture_runtime_vectors()
    metrics = telemetry.get("metrics", {})

    st.metric("System CPU Footprint", f"{metrics.get('cpu_load_percentage', 0)} %")
    st.metric("Memory Utilization", f"{metrics.get('memory_usage_percentage', 0)} %")
    st.metric("Disk Utilization", f"{metrics.get('disk_usage_percentage', 0)} %")
    st.metric("Process Count", f"{metrics.get('process_count', 0)}")

    verdict = result.get("verdict") if result else "IDLE"
    if verdict == "TRIGGER_SELF_HEALING":
        st.error("🔴 ANOMALY DETECTED")
    elif verdict == "REVIEW_AND_MONITOR":
        st.warning("🟠 REVIEW REQUIRED")
    elif verdict == "MAINTAIN_STEADY_STATE":
        st.success("🟢 SYSTEM OPTIMAL")
    else:
        st.info("ℹ️ Awaiting first cycle")

with col2:
    st.header("🤖 Ultron Core Monologue & Insights")

    if result:
        st.text_area(
            "Reasoning Topology",
            value=result.get("reasoning_topology", ""),
            height=140,
        )

        st.json(
            {
                "verdict": result.get("verdict"),
                "execution_priority": result.get("execution_priority"),
                "used_llm": result.get("used_llm"),
                "maintenance_report": result.get("maintenance_report"),
            }
        )
    else:
        st.info("Run a cycle to initialize strategy output.")

    st.text_area(
        "Operational Action Packets",
        value="\n".join(st.session_state.logs),
        height=240,
    )

if st.session_state.auto_refresh:
    time.sleep(st.session_state.refresh_interval)
    st.rerun()
