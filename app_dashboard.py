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
    st.session_state.refresh_interval = 10
    st.session_state.selected_feed = DEFAULT_FEEDS[0] if DEFAULT_FEEDS else ""

st.title(APP_TITLE)
st.subheader("Autonomous Defensive Intelligence Control Plane")
st.markdown("---")

with st.sidebar:
    st.header("Core Controls")
    st.session_state.selected_feed = st.text_input("Target feed URL", value=st.session_state.selected_feed)
    st.session_state.auto_refresh = st.checkbox("Activate Framework Loop", value=st.session_state.auto_refresh)
    st.session_state.refresh_interval = st.slider("Refresh Interval (seconds)", 5, 60, st.session_state.refresh_interval)
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
    return summary[:140] + ("..." if len(summary) > 140 else "")

def execute_cycle():
    if not st.session_state.selected_feed.strip():
        return
    result = st.session_state.orchestrator.run_single_cycle(st.session_state.selected_feed.strip())
    st.session_state.last_result = result
    st.session_state.logs.insert(
        0,
        f"[{result['timestamp']}] {result['decision']['autonomous_action']} | {result['decision']['priority']} | {summarize_log(result)}"
    )
    st.session_state.logs = st.session_state.logs[:20]

if run_once:
    execute_cycle()

if st.session_state.auto_refresh:
    execute_cycle()

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

        if decision.get("risk_level") == "CRITICAL":
            st.error("Critical risk detected")
        elif decision.get("risk_level") == "HIGH":
            st.warning("High risk detected")
        else:
            st.success("System in monitored state")
    else:
        st.info("Run a cycle to initialize Mythos.")

with right:
    st.header("Sovereign Brain Output")
    result = st.session_state.last_result

    if result:
        st.text_area(
            "Reasoning Topology",
            value=result["decision"].get("reasoning_topology", ""),
            height=120,
        )

        enrichment = result["decision"].get("llm_enrichment")
        if enrichment:
            st.text_area(
                "LLM Enrichment",
                value=f"Summary: {enrichment.get('summary', '')}\n\nNext Step: {enrichment.get('recommended_next_step', '')}",
                height=140,
            )

        st.json(result)
    else:
        st.info("No result yet.")

st.markdown("### Operational Action Packets")
st.text_area("Recent Logs", value="\n".join(st.session_state.logs), height=220)

st.markdown("### Recent Memory")
recent_runs = st.session_state.orchestrator.recent_runs(limit=5)
for item in recent_runs:
    with st.expander(f"{item['created_at']} | {item['verdict']} | {item['priority']}"):
        st.json(item["payload"])

if st.session_state.auto_refresh:
    time.sleep(st.session_state.refresh_interval)
    st.rerun()
