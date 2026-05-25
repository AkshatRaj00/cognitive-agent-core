# API Reference

Complete API documentation for `cognitive-agent-core` public modules.

---

## `core.memory_store`

### `MemoryStore`

```python
class MemoryStore(sweep_interval: float = 60.0)
```

In-memory key-value store with optional TTL-based expiry and lazy eviction.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `set` | `set(key, value, ttl=None)` | Store a value with optional TTL in seconds |
| `get` | `get(key, default=None)` | Get value; returns default if missing or expired |
| `delete` | `delete(key) -> bool` | Remove key, returns True if it existed |
| `exists` | `exists(key) -> bool` | True only if key is present and not expired |
| `ttl_remaining` | `ttl_remaining(key) -> float \| None` | Seconds until expiry; None if no TTL |
| `clear` | `clear()` | Remove all entries |

---

## `core.cognitive_brain`

### `CognitiveBrain`

```python
class CognitiveBrain(config: BrainConfig)
```

Chain-of-thought reasoning engine with confidence scoring.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `think` | `think(input: AgentInput) -> ThoughtResult` | Process input through reasoning chain |
| `stream_think` | `stream_think(input) -> AsyncIterator[str]` | Stream reasoning tokens |
| `reflect` | `reflect(thought: ThoughtResult) -> ReflectionResult` | Self-evaluate a thought |

---

## `core.runtime_executor`

### `RuntimeExecutor`

```python
class RuntimeExecutor(config: ExecutorConfig)
```

Executes agent actions with retry logic and exponential backoff.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `execute` | `execute(action: Action) -> ActionResult` | Run action with retries |
| `execute_many` | `execute_many(actions: list[Action]) -> list[ActionResult]` | Parallel execution |
| `cancel` | `cancel(action_id: str)` | Cancel a running action |

---

## `core.agent_engine`

### `AgentEngine`

```python
class AgentEngine(brain: CognitiveBrain, executor: RuntimeExecutor)
```

Top-level agent orchestrator.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `run` | `run(query: str) -> AgentResponse` | Synchronous agent run |
| `stream` | `stream(query: str) -> AsyncIterator[str]` | Streaming agent run |
| `reset` | `reset()` | Clear conversation context |

---

## `core.vector_store`

### `VectorStore`

```python
class VectorStore(dim: int, metric: Literal["cosine", "dot", "l2"] = "cosine")
```

In-memory vector store with similarity search.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `add` | `add(id: str, vector: np.ndarray, metadata: dict)` | Index a vector |
| `search` | `search(query: np.ndarray, top_k: int = 5) -> list[SearchResult]` | Nearest-neighbour search |
| `delete` | `delete(id: str) -> bool` | Remove a vector |
| `rebuild_index` | `rebuild_index()` | Rebuild FAISS index after bulk updates |

---

## Configuration Objects

### `BrainConfig`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `model` | `str` | `"gemini-1.5-flash"` | LLM model identifier |
| `temperature` | `float` | `0.7` | Sampling temperature |
| `max_tokens` | `int` | `2048` | Max output tokens |
| `chain_of_thought` | `bool` | `True` | Enable CoT reasoning |
| `confidence_threshold` | `float` | `0.6` | Minimum confidence to act |

### `ExecutorConfig`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_retries` | `int` | `3` | Max retry attempts |
| `base_delay` | `float` | `1.0` | Base backoff delay (seconds) |
| `timeout` | `float` | `30.0` | Per-action timeout |
| `parallel_limit` | `int` | `5` | Max concurrent executions |
