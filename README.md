# cognitive-agent-core

> A modular, production-ready AI cognitive agent runtime built in Python — featuring priority-based orchestration, TTL-aware memory, sandboxed execution, structured telemetry, and a pluggable recon pipeline.

![CI](https://github.com/AkshatRaj00/cognitive-agent-core/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🧠 Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                    cognitive-agent-core                    │
├───────────────────────────────────────────────────────────────┤
│  MasterOrchestrator → RuntimeExecutor → SandboxActuator    │
│         ↓                    ↓                  ↓          │
│   AgentEngine       CognitiveBrain      MemoryStore (TTL)  │
│         ↓                    ↓                             │
│    CyberScout            Telemetry                         │
└───────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

| Module | What it does |
|---|---|
| `MasterOrchestrator` | Priority-based task queue with FIFO tie-breaking and lifecycle hooks |
| `RuntimeExecutor` | Retry logic with configurable exponential backoff |
| `SandboxActuator` | Wall-clock timeout + POSIX memory-limit enforcement |
| `MemoryStore` | Thread-safe key-value store with per-entry TTL and background pruning |
| `CognitiveBrain` | LLM reasoning layer (Gemini-backed) |
| `AgentEngine` | Main entry point wiring all modules together |
| `CyberScout` | Pluggable recon pipeline with TTL result caching |
| `Telemetry` | Structured event tracing with ring-buffer and summary stats |
| `AgentConfig` | Env-aware config dataclass with field validation |

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/AkshatRaj00/cognitive-agent-core.git
cd cognitive-agent-core
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
```

### 2. Set your API key

```bash
export GEMINI_API_KEY="your-key-here"
```

### 3. Run the agent

```bash
python agent_engine.py
```

---

## 🧪 Run Tests

```bash
pytest -v --cov=. --cov-report=term-missing
```

---

## 📍 Usage Examples

### MemoryStore with TTL

```python
from memory_store import MemoryStore

store = MemoryStore(default_ttl=3600)  # 1-hour default
store.set("session:abc", {"user": "akshat"}, ttl=300)  # 5-min override
print(store.get("session:abc"))  # {'user': 'akshat'}
```

### Priority Task Scheduling

```python
from master_orchestrator import MasterOrchestrator

orch = MasterOrchestrator(
    on_task_success=lambda name, result: print(f"{name} done: {result}")
)
orch.enqueue("fetch_data", lambda: "data", priority=1)   # highest
orch.enqueue("log_event", lambda: "logged", priority=10)  # lowest
orch.run_all()  # fetch_data runs first
```

### Retry with Backoff

```python
from runtime_executor import RuntimeExecutor

executor = RuntimeExecutor(max_retries=3, backoff_base=2.0)
result = executor.execute(my_api_call, task_name="gemini.generate")
```

---

## 🛠️ Configuration

All settings are configurable via environment variables (prefix: `AGENT_`) or programmatically:

```bash
export AGENT_MODEL_NAME=gemini-1.5-flash
export AGENT_TEMPERATURE=0.5
export AGENT_MAX_RETRIES=5
export AGENT_DEBUG=true
```

---

## 📄 License

MIT © [Akshat Raj](https://github.com/AkshatRaj00)
