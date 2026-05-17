# Mythos Core

A modular, defensive AI operations engine built for autonomous telemetry analysis, structured decision-making, and controlled runtime actions.

## Overview

Mythos Core is designed as a multi-layer agent framework that combines system telemetry, deterministic reasoning, optional LLM augmentation, persistent memory, and controlled execution workflows. The architecture is intentionally split into focused modules so the system remains explainable, debuggable, and extensible as it grows.

The current build is best understood as a real autonomous monitoring and decision framework, not a magical all-powerful AGI. It can ingest runtime data, score operational risk, generate action recommendations, store execution history, and surface decisions through a Streamlit control plane. Local or provider-backed LLMs can be attached for summarization and structured reasoning overlays.

## Core Architecture

```text
cognitive-agent-core/
├── app_dashboard.py         # Streamlit command center
├── core_telemetry.py        # Runtime system telemetry capture
├── cognitive_brain.py       # Deterministic + LLM-assisted decision engine
├── runtime_executor.py      # Safe execution / self-healing layer
├── agent_engine.py          # Orchestration helpers and lifecycle glue
├── config.py                # Runtime configuration and feature flags
├── memory_store.py          # Persistent local memory / execution history
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation
```

## Design Goals

- Build a real agent framework, not a fake demo shell.
- Keep the decision path explainable through deterministic scoring.
- Add LLM capability as augmentation, not blind control.
- Preserve a modular structure so each subsystem can evolve independently.
- Support local-first operation where possible.
- Make the dashboard feel like an operator console, not a toy UI.

## What Mythos Can Do

### 1. Telemetry Awareness
Mythos can capture live runtime vectors such as CPU load, memory usage, disk pressure, and process counts through a telemetry layer. Those metrics become the base signal for every downstream decision.

### 2. Deterministic Risk Scoring
The brain module can evaluate telemetry against threshold logic and convert noisy machine-state data into a structured verdict like:

- `MAINTAIN_STEADY_STATE`
- `REVIEW_AND_MONITOR`
- `TRIGGER_SELF_HEALING`

This makes the system predictable and inspectable.

### 3. Optional LLM Augmentation
A local or provider-backed LLM can enrich decisions with summaries, operational interpretation, and next-step guidance. The LLM does not need to own the final verdict; it can work as a reasoning amplifier on top of the deterministic engine.

### 4. Persistent Memory
Mythos can store run history, verdicts, and operational notes in a local persistence layer such as SQLite. This provides the foundation for trend analysis, false-positive suppression, and future self-correction logic.

### 5. Streamlit Control Plane
The dashboard can expose:

- current system state
- latest verdict
- execution history
- reasoning output
- auto-refresh loops
- manual or guarded action controls

## What Mythos Is Not

Mythos is **not** currently:

- a full AGI
- a self-improving unrestricted cyber-operator
- an always-correct autonomous intelligence
- a replacement for proper infrastructure monitoring stacks
- a magical model that outperforms all frontier AI systems by default

That distinction matters. A strong engineering system grows from reliable parts, not exaggerated labels.

## Execution Model

Mythos uses a layered reasoning pattern:

1. **Observe** — capture system telemetry or fetch operational input.
2. **Evaluate** — run deterministic scoring and anomaly classification.
3. **Augment** — optionally ask an LLM for a structured summary.
4. **Decide** — create a verdict with priority and reasoning.
5. **Act** — pass that verdict to a controlled executor.
6. **Remember** — store the run for future analysis.

This separation is what makes the project maintainable.

## Example Decision Payload

```json
{
  "verdict": "REVIEW_AND_MONITOR",
  "execution_priority": "HIGH",
  "confidence": "MEDIUM",
  "anomaly_score": 4,
  "anomalies": [
    "cpu_elevated",
    "memory_elevated"
  ],
  "reasoning_topology": "CPU elevated at 81.2%. Memory elevated at 84.7%.",
  "used_llm": true,
  "llm_analysis": {
    "summary": "The system is under elevated resource pressure but does not yet indicate catastrophic failure.",
    "recommended_next_step": "Monitor for sustained spikes and inspect heavy processes.",
    "operational_risk": "MODERATE",
    "notable_metric": "memory_usage_percentage"
  }
}
```

## Why This Architecture Matters

A lot of so-called agent projects are only wrappers around a chat completion API plus dramatic variable names. Mythos is meant to move in a better direction:

- deterministic core first
- telemetry-backed decision logic
- structured outputs
- modular action layer
- persistent memory
- optional local-model compatibility

That means the project can mature into something genuinely useful instead of collapsing under hype.

## Recommended Module Roles

### `core_telemetry.py`
Responsible for collecting runtime metrics and normalizing them into a stable machine-readable schema.

### `cognitive_brain.py`
Responsible for scoring, verdict generation, anomaly labeling, confidence estimation, and optional LLM augmentation.

### `runtime_executor.py`
Responsible for safe actions only. This is where controlled self-healing, restart hooks, isolation logic, or audit events should live.

### `agent_engine.py`
Responsible for orchestration, pipeline lifecycle, and module coordination.

### `app_dashboard.py`
Responsible for the operator interface, decision visibility, live status, and memory introspection.

## Realistic Capability Level

Current Mythos should be described as:

> **A real, modular, defensive AI operations prototype with deterministic reasoning and optional LLM augmentation.**

That is already meaningful.

It is stronger than a fake demo, but weaker than a true autonomous general intelligence system. The strength of the project is not raw fantasy power — it is the fact that it can be engineered into something reliable.

## Local-First Strategy

If API costs are a concern, Mythos can be adapted toward a local-first architecture using local LLM runtimes and local memory. In that setup:

- telemetry stays local
- decisions stay local
- memory stays local
- dashboard stays local
- only optional online signals are fetched from the internet

This is a strong direction for privacy, cost control, and long-term independence.

## Roadmap

### Phase 1 — Stable Core
- Clean telemetry collection
- Deterministic verdict engine
- Basic Streamlit dashboard
- Local memory persistence
- Structured result payloads

### Phase 2 — Better Intelligence
- Historical baselines
- False-positive suppression
- Confidence calibration
- Better anomaly clustering
- Provider-agnostic LLM layer

### Phase 3 — Real Agent Behavior
- Multi-step planning
- Tool routing
- Task queues
- Action policies
- Recovery workflows
- Rich audit trails

### Phase 4 — Production Hardening
- Deployment profiles
- Authentication
- Role-based control
- Alert integrations
- Real scheduler separation from UI
- Dedicated backend worker architecture

## Installation

```bash
git clone https://github.com/AkshatRaj00/cognitive-agent-core.git
cd cognitive-agent-core
pip install -r requirements.txt
streamlit run app_dashboard.py
```

## Environment Variables

```env
AI_AGENT_API_KEY=your_provider_key
AI_AGENT_MODEL=llama-3.1-8b-instant
AI_AGENT_BASE_URL=https://api.groq.com/openai/v1
```

If a provider key is not configured, Mythos should still operate in deterministic mode.

## Engineering Principles

- Never let branding outrun implementation.
- Deterministic reasoning should remain visible.
- LLMs should assist, not blindly dominate.
- Store execution history.
- Prefer explainability over hype.
- Build capability in layers.

## Final Note

Mythos Core is at its best when treated like an evolving systems-engineering project: one that combines telemetry, reasoning, memory, and controlled actions into a serious operator-grade framework.

The right goal is not to pretend it is already a god-tier intelligence.
The right goal is to make it powerful through iteration, structure, honesty, and disciplined engineering.
