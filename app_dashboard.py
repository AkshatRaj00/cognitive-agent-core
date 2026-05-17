import streamlit as st
import time
import json
import random
# Interconnecting our core agent modules
from core_telemetry import SystemTelemetryMatrix
from cognitive_brain import CognitiveMatrixEngine

# Page configuration for a premium dark-themed developer UI
st.set_page_config(page_title="Cognitive Agent Core", page_icon="🧠", layout="wide")

st.title("🧠 Cognitive AI Agent Core - Real-Time Control Loop")
st.markdown("---")

# Initializing core subsystems
sensor = SystemTelemetryMatrix()
brain = CognitiveMatrixEngine(sensor_node=sensor)

# UI Layout: Splitting the screen into real-time metrics and AI reasoning
col1, col2 = st.columns([1, 2])

with col1:
    st.header("📊 Live System Telemetry")
    cpu_metric = st.metric(label="CPU Utilization", value="0 %")
    memory_metric = st.metric(label="Memory Drift Coeff", value="0 %")
    status_indicator = st.subheader("System Status: Fetching...")

with col2:
    st.header("🤖 AI Agent Internal Monologue")
    log_area = st.empty()
    action_status = st.info("Agent State: Standing by...")

# Continuous Real-Time Simulation Loop
st.markdown("### 🔄 Active Monitoring Stream")
run_agent = st.checkbox("Start Autonomous Agent Loop", value=True)

if run_agent:
    log_data = []
    while True:
        # 1. Fetch live telemetry vectors
        telemetry = sensor.capture_runtime_vectors()
        metrics = telemetry.get("metrics", {})
        
        # Updating UI metrics live
        cpu_metric.metric(label="CPU Utilization", value=f"{metrics['cpu_load_percentage']} %")
        memory_metric.metric(label="Memory Drift Coeff", value=f"{metrics['memory_drift_coefficient']} %")
        
        # 2. Consult the Cognitive Engine
        strategy = brain.formulate_execution_strategy("Maintain optimal server latency.")
        
        # Update Status based on Agent's Verdict
        if strategy["verdict"] == "TRIGGER_SELF_HEALING":
            status_indicator.error("🔴 ANOMALY DETECTED")
            action_status.error(f"⚡ [Action Executed]: {strategy['reasoning_topology']}")
        else:
            status_indicator.success("🟢 SYSTEM OPTIMAL")
            action_status.success(f"🛡️ [Stable State]: {strategy['reasoning_topology']}")
            
        # Logging thoughts to the UI front page
        log_entry = f"[{time.strftime('%H:%M:%S')}] Verdict: {strategy['verdict']} | {strategy['reasoning_topology']}"
        log_data.insert(0, log_entry)
        log_area.text_area("Agent Execution Logs", value="\n".join(log_data[:10]), height=200)
        
        time.sleep(2) # Refreshing every 2 seconds to match live streams
