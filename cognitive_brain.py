import json
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

from core_telemetry import SystemTelemetryMatrix

load_dotenv()


class LLMAgentBrain:
    """
    Deterministic risk engine first.
    Optional LLM summary second.
    """

    def __init__(self, sensor_node: SystemTelemetryMatrix):
        self.sensor = sensor_node
        self.api_key = os.getenv("AI_AGENT_API_KEY", "").strip()
        self.model_name = os.getenv("AI_AGENT_MODEL", "llama-3.1-8b-instant")
        self.base_url = os.getenv("AI_AGENT_BASE_URL", "https://api.groq.com/openai/v1").strip()

        self.client = None
        if self.api_key and OpenAI is not None:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _deterministic_decision(self, telemetry_data: Dict[str, Any], operational_goal: str) -> Dict[str, Any]:
        metrics = telemetry_data.get("metrics", {})
        cpu = float(metrics.get("cpu_load_percentage", 0))
        mem = float(metrics.get("memory_usage_percentage", 0))
        disk = float(metrics.get("disk_usage_percentage", 0))
        proc = int(metrics.get("process_count", 0))

        score = 0
        reasons: List[str] = []

        if cpu >= 90:
            score += 3
            reasons.append(f"CPU critically high at {cpu}%.")
        elif cpu >= 75:
            score += 2
            reasons.append(f"CPU elevated at {cpu}%.")

        if mem >= 90:
            score += 3
            reasons.append(f"Memory critically high at {mem}%.")
        elif mem >= 80:
            score += 2
            reasons.append(f"Memory elevated at {mem}%.")

        if disk >= 95:
            score += 3
            reasons.append(f"Disk critically high at {disk}%.")
        elif disk >= 85:
            score += 2
            reasons.append(f"Disk elevated at {disk}%.")

        if proc >= 400:
            score += 1
            reasons.append(f"Process count unusually high at {proc}.")

        if score >= 5:
            verdict = "TRIGGER_SELF_HEALING"
            priority = "CRITICAL"
        elif score >= 2:
            verdict = "REVIEW_AND_MONITOR"
            priority = "HIGH"
        else:
            verdict = "MAINTAIN_STEADY_STATE"
            priority = "LOW"

        if not reasons:
            reasons.append("All monitored system metrics are within normal thresholds.")

        return {
            "verdict": verdict,
            "execution_priority": priority,
            "reasoning_topology": " ".join(reasons),
            "goal": operational_goal,
            "used_llm": False,
        }

    def _llm_summary(self, telemetry_data: Dict[str, Any], deterministic_result: Dict[str, Any]) -> Optional[str]:
        if not self.client:
            return None

        system_prompt = (
            "You are a systems operations assistant. "
            "Summarize telemetry and deterministic verdict in 2 short factual sentences. "
            "Do not invent incidents. Do not change the verdict. Plain English only."
        )

        user_prompt = json.dumps(
            {
                "telemetry": telemetry_data,
                "deterministic_result": deterministic_result,
            },
            indent=2,
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return None

    def consult_ai_core(self, telemetry_data: Dict[str, Any], operational_goal: str) -> Dict[str, Any]:
        deterministic = self._deterministic_decision(telemetry_data, operational_goal)
        llm_summary = self._llm_summary(telemetry_data, deterministic)

        if llm_summary:
            deterministic["reasoning_topology"] = llm_summary
            deterministic["used_llm"] = True

        return deterministic

    def formulate_execution_strategy(self, task_objective: str) -> Dict[str, Any]:
        raw_telemetry = self.sensor.capture_runtime_vectors()
        strategy = self.consult_ai_core(raw_telemetry, task_objective)
        strategy["telemetry"] = raw_telemetry
        return strategy
