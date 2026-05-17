import streamlit as st
import time
from core_telemetry import SystemTelemetryMatrix
from cognitive_brain import LLMAgentBrain
from runtime_executor import RuntimeExecutionOrchestrator

# Page configurations for dark telemetry hub theme
st.set_page_config(page_title="Cognitive Agent Core", page_icon="🧠", layout="wide")

st.title("🧠 Cognitive AI Agent Core")
st.subheader("Autonomous Multi-Agent Feedback Control Loop")
st.markdown("---")

# Bootstrap system layers securely
if 'sensor' not in st.session_state:
    st.session_state.sensor = SystemTelemetryMatrix()
    st.session_state.brain = LLMAgentBrain(sensor_node=st.session_state.sensor)
    st.session_state.orchestrator = RuntimeExecutionOrchestrator(brain_node=st.session_state.brain)

col1, col2 = st.columns([1, 2])

with col1:
    st.header("📊 Telemetry Metrics")
    cpu_metric = st.metric(label="System CPU Footprint", value="0 %")
    memory_metric = st.metric(label="Calculated Memory Drift", value="0 %")
    status_box = st.empty()

with col2:
    st.header("🤖 Agent Internal Engine Monologue")
    action_box = st.empty()
    log_stream = st.empty()

st.sidebar.header("⚙️ Core Controls")
run_loop = st.sidebar.checkbox("Activate Framework Loop", value=True)
loop_speed = st.sidebar.slider("Sensor Refresh Interval (Seconds)", 1.0, 5.0, 2.0)

if run_loop:
    logs = []
    while True:
        # 1. Realtime telemetry retrieval
        telemetry = st.session_state.sensor.capture_runtime_vectors()
        metrics = telemetry.get("metrics", {})
        
        # Live dashboard updates
        cpu_metric.metric(label="System CPU Footprint", value=f"{metrics['metrics']['cpu_load_percentage']} %")
        memory_metric.metric(label="Calculated Memory Drift", value=f"{metrics['metrics']['memory_drift_coefficient']} %")
        
        # 2. Execution Pipeline run
        strategy = st.session_state.orchestrator.run_autonomous_pipeline("Optimize cluster infrastructure latency.")
        
        # 3. Dynamic UI updates based on operational decisions
        if strategy["verdict"] == "TRIGGER_SELF_HEALING":
            status_box.error("🔴 ANOMALY BREACH")
            action_box.error(f"⚡ [Action Vector]: {strategy['reasoning_topology']}")
        else:
            status_box.success("🟢 Baseline Secure")
            action_box.success(f"🛡️ [Steady State]: {strategy['reasoning_topology']}")
            
        log_line = f"[{time.strftime('%H:%M:%S')}] {strategy['verdict']} ➔ {strategy['reasoning_topology']}"
        logs.insert(0, log_line)
        log_stream.text_area("Live Log Output (Top 10 Packets)", value="\n".join(logs[:10]), height=250)
        
        time.sleep(loop_speed)
