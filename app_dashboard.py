import time
import streamlit as st

from config import APP_TITLE, DEFAULT_FEEDS
from master_orchestrator import MasterOrchestrator

st.set_page_config(page_title=APP_TITLE, page_icon="🧠", layout="wide")

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = MasterOrchestrator()
    st.session_state.logs = []
    st.session_state.last_result = None
    st.session_state.auto_refresh = False
    st.session_state.refresh_interval = 15
    st.session_state.selected_feed = DEFAULT_FEEDS[0] if DEFAULT_FEEDS else ""
    st.session_state.last_cycle_ts = 0.0

st.title(APP_TITLE)
st.subheader("Autonomous Defensive Intelligence Control Plane")
st.markdown("---")

with st.sidebar:
    st.header("Core Controls")
    st.session_state.selected_feed = st.text_input("Target feed URL", value=st.session_state.selected_feed)
    st.session_state.auto_refresh = st.checkbox("Activate Framework Loop", value=st.session_state.auto_refresh)
    st.session_state.refresh_interval = st.slider("Refresh Interval (seconds)", 10, 120, st.session_state.refresh_interval)
    run_once = st.button("Run Single Cycle", use_container_width=True)
    clear_logs = st.button("Clear Logs", use_container_width=True)

    if clear_logs:
        st.session_state.logs = []
        st.session_state.last_result = None

def summarize_log(result: dict) -> str:
    decision = result.get("decision", {})
    enrich = decision.get("llm_enrichment") or {}
    summary = enrich.get("summary") or decision.get("reasoning_topology", "")
    summary = " ".join(summary.split())
    return summary[:160] + ("..." if len(summary) > 160 else "")

def execute_cycle():
    url = st.session_state.selected_feed.strip()
    if not url:
        return
    result = st.session_state.orchestrator.run_single_cycle(url)
    st.session_state.last_result = result
    st.session_state.logs.insert(
        0,
        f"[{result['timestamp']}] {result['decision']['autonomous_action']} | {result['decision']['priority']} | {summarize_log(result)}"
    )
    st.session_state.logs = st.session_state.logs[:20]

if run_once:
    execute_cycle()
    st.session_state.last_cycle_ts = time.time()

now = time.time()
if st.session_state.auto_refresh and now - st.session_state.last_cycle_ts >= st.session_state.refresh_interval:
    execute_cycle()
    st.session_state.last_cycle_ts = now

left, right = st.columns([1, 2])

with left:
    st.header("Live Decision State")
    result = st.session_state.last_result

    if result:
        decision = result["decision"]
        ingestion = result["ingestion"]
        st.metric("Risk Level", decision.get("risk_level", "UNKNOWN"))
        st.metric("Action", decision.get("autonomous_action", "UNKNOWN"))
        st.metric("Priority", decision.get("priority", "UNKNOWN"))
        st.metric("Source Status", ingestion.get("status", "UNKNOWN"))

        if decision.get("risk_level") == "HIGH":
            st.warning("High-risk signal detected")
        elif decision.get("risk_level") == "MEDIUM":
            st.info("Monitored signal detected")
        else:
            st.success("Low-risk monitored state")
    else:
        st.info("Run a cycle to initialize Mythos.")

with right:
    st.header("Sovereign Brain Output")
    result = st.session_state.last_result
    if result:
        st.text_area("Reasoning Topology", value=result["decision"].get("reasoning_topology", ""), height=100)

        enrichment = result["decision"].get("llm_enrichment")
        if enrichment:
            st.text_area(
                "LLM Enrichment",
                value=(
                    f"Summary: {enrichment.get('summary', '')}\n\n"
                    f"Recommended Next Step: {enrichment.get('recommended_next_step', '')}\n\n"
                    f"Confidence Note: {enrichment.get('confidence_note', '')}"
                ),
                height=180,
            )

        st.json(result)
    else:
        st.info("No result yet.")

st.markdown("### Operational Action Packets")
st.text_area("Recent Logs", value="\n".join(st.session_state.logs), height=220)

st.markdown("### Recent Memory")
for item in st.session_state.orchestrator.recent_runs(limit=5):
    with st.expander(f"{item['created_at']} | {item['verdict']} | {item['priority']}"):
        st.json(item["payload"])

if st.session_state.auto_refresh:
    time.sleep(1)
    st.rerun()
