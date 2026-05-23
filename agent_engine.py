import sys
import time
import json
import traceback
import numpy as np
from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass, field

# Max consecutive self-healing retries before aborting loop
MAX_SELF_HEAL_RETRIES = 3


@dataclass
class ExecutionNode:
    timestamp: float
    action: str
    feedback: Any
    entropy: float
    thought: str


class CognitiveState:
    """Manages the internal multi-dimensional vector log and execution state."""

    def __init__(self):
        self.entropy_history: List[float] = [0.0]
        self.knowledge_base: Dict[str, Any] = {}
        self.execution_graph: List[ExecutionNode] = []

    @property
    def current_entropy(self) -> float:
        return self.entropy_history[-1]

    def update_state(self, action: str, thought: str, feedback: Any, variance: float):
        # BUG FIX: original code did list + list concat incorrectly inside np.mean
        # Correct approach: slice last 3 items then append variance as separate arg
        recent = self.entropy_history[-3:]
        new_entropy = float(np.mean(recent + [variance]))
        self.entropy_history.append(new_entropy)

        node = ExecutionNode(
            timestamp=time.time(),
            action=action,
            feedback=feedback,
            entropy=new_entropy,
            thought=thought,
        )
        self.execution_graph.append(node)

    def get_summary(self) -> Dict[str, Any]:
        """Returns a clean telemetry snapshot of the current cognitive state."""
        return {
            "total_nodes": len(self.execution_graph),
            "final_entropy": round(self.current_entropy, 4),
            "entropy_trend": [round(e, 4) for e in self.entropy_history[-5:]],
            "last_action": self.execution_graph[-1].action if self.execution_graph else None,
        }


class AutonomousExecutor:
    """
    Enhanced ReAct Agent Engine with Recursive Reflection.
    Includes self-healing retry guard to prevent infinite error loops.
    """

    def __init__(self, state: CognitiveState):
        self.state = state
        self.tool_registry: Dict[str, Callable] = {}
        self._bootstrap_system_tools()

    def _bootstrap_system_tools(self):
        """Registers core operational capabilities."""
        self.register_tool(
            "kernel_telemetry",
            lambda: {
                "sys_path_depth": len(sys.path),
                "memory_usage": "STABLE",
                "threads": 1,
            },
        )
        self.register_tool(
            "entropy_stabilizer",
            lambda: {"adjustment": -0.05, "status": "COOLDOWN"},
        )

    def register_tool(self, name: str, fn: Callable):
        self.tool_registry[name] = fn

    def _reason(self, objective: str) -> Dict[str, Any]:
        """The 'Think' phase of ReAct."""
        complexity_score = len(objective) * 0.012
        current_flux = self.state.current_entropy

        if current_flux > 0.8:
            action = "entropy_stabilizer"
            thought = "System entropy exceeds threshold. Initiating stabilization sequence."
        elif complexity_score > 0.2:
            action = "kernel_telemetry"
            thought = f"Objective complexity ({complexity_score:.2f}) requires system telemetry."
        else:
            action = "terminate"
            thought = "Objective convergence reached. Minimal delta detected."

        return {"thought": thought, "action": action, "score": complexity_score}

    def orchestrate_loop(
        self, primary_objective: str, max_cycles: int = 5
    ) -> Dict[str, Any]:
        print(f"\U0001f680 [Core] Initializing Pipeline: '{primary_objective}'")

        context = primary_objective
        consecutive_errors = 0

        for cycle in range(max_cycles):
            print(f"\n\U0001f300 [Cycle {cycle + 1}]")

            # 1. THINK
            inference = self._reason(context)
            print(f"  \U0001f9e0 [Thought]: {inference['thought']}")

            if inference["action"] == "terminate":
                print("  \u2705 [Convergence] Stability achieved.")
                break

            # 2. ACT
            action_key = inference["action"]
            try:
                if action_key not in self.tool_registry:
                    raise ValueError(f"Tool '{action_key}' not found in registry.")

                print(f"  \U0001f6e0\ufe0f [Action]: Dispatching {action_key}...")
                result = self.tool_registry[action_key]()

                # 3. OBSERVE & REFLECT
                variance = 0.1 * (cycle + 1)
                self.state.update_state(
                    action=action_key,
                    thought=inference["thought"],
                    feedback=result,
                    variance=variance,
                )

                feedback_json = json.dumps(result)
                print(f"  \U0001f441\ufe0f [Observation]: {feedback_json}")
                context = f"Previous result: {feedback_json}. Objective: {primary_objective}"

                # Reset error counter on success
                consecutive_errors = 0

            except Exception as e:
                consecutive_errors += 1
                print(f"  \u26a0\ufe0f [Self-Healing]: Error encountered: {str(e)}")
                self.state.update_state("error_recovery", "Fault detected", str(e), 0.9)

                # Guard: abort if too many consecutive failures
                if consecutive_errors >= MAX_SELF_HEAL_RETRIES:
                    print(
                        f"  \U0001f6ab [Abort] Max self-heal retries ({MAX_SELF_HEAL_RETRIES}) reached. Stopping loop."
                    )
                    break

        return self.state.get_summary()


# --- Execution ---
if __name__ == "__main__":
    brain = CognitiveState()
    agent = AutonomousExecutor(state=brain)

    task = "Monitor memory drift and stabilize high-entropy fluctuations."
    report = agent.orchestrate_loop(primary_objective=task)

    print("\n" + "=" * 50)
    print(f"\U0001f4ca [FINAL TELEMETRY REPORT]")
    print(json.dumps(report, indent=2))
    print("=" * 50)
