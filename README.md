# 🧠 Cognitive AI Agent Core

An advanced autonomous **Multi-Agent Control Loop** framework engineered to monitor low-level operating system telemetry, process environmental drift using a cognitive reasoning engine, and trigger real-time autonomous self-healing sequences.

## 🏗️ System Architecture & Dhancha

The framework operates on a continuous feedback loop decoupled into three core components:

[System Telemetry (Sensors)] ➔ [Cognitive Engine (Brain/LLM)] ➔ [Runtime Actuator (Executor)]
▲                                                                │
└─────────────────── [Self-Healing Action Feedback] ─────────────┘


1. **`core_telemetry.py` (Sensors):** Extracts metrics including CPU footprints, thread allocation thresholds, and memory drift.
2. **`cognitive_brain.py` (Brain):** Implements dynamic algorithmic weights and LLM interfaces to evaluate anomalous states.
3. **`runtime_executor.py` (Actuators):** Performs localized system corrections and context garbage collection without human intervention.
4. **`app_dashboard.py` (Front Page):** A live data-streaming developer dashboard visualizing telemetry vectors and agent logs.

## 🚀 Deployment Instructions

### 1. Initialize the Live Dashboard UI
```bash
pip install streamlit psutil openai
streamlit run app_dashboard.py
