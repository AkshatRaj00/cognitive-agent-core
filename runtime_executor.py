import gc
import json
import os
import platform
import subprocess
import time
from typing import Any, Dict


class RuntimeExecutionOrchestrator:
    """
    Safe executor for local maintenance actions and audit logging.
    """

    def __init__(self, brain_node: Any):
        self.brain = brain_node
        self.audit_log_path = "production_agent_audit.log"

    def execute_environment_check(self) -> str:
        try:
            if platform.system().lower().startswith("win"):
                result = subprocess.run(
                    ["cmd", "/c", "ver"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
            else:
                result = subprocess.run(
                    ["uname", "-a"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
            return (result.stdout or result.stderr).strip()
        except Exception as e:
            return f"Environment check skipped: {str(e)}"

    def deploy_production_patch(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        gc_cycles = 0
        shell_intel = self.execute_environment_check()

        try:
            gc_cycles = gc.collect()
        except Exception:
            gc_cycles = 0

        maintenance_report = {
            "gc_cycles_collected": gc_cycles,
            "environment_check": shell_intel,
            "action_status": "COMPLETED",
        }

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "verdict": strategy.get("verdict"),
            "priority": strategy.get("execution_priority"),
            "reasoning": strategy.get("reasoning_topology"),
            "maintenance_report": maintenance_report,
        }

        try:
            with open(self.audit_log_path, "a", encoding="utf-8") as audit_file:
                audit_file.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass

        return maintenance_report

    def run_autonomous_pipeline(self, target_task: str) -> dict:
        strategy_payload = self.brain.formulate_execution_strategy(target_task)

        maintenance_report = None
        if strategy_payload.get("verdict") == "TRIGGER_SELF_HEALING":
            maintenance_report = self.deploy_production_patch(strategy_payload)

        strategy_payload["maintenance_report"] = maintenance_report
        return strategy_payload
