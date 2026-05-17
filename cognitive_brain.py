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
    Deterministic system-risk engine first.
    Structured LLM augmentation second.
    """

    def __init__(self, sensor_node: SystemTelemetryMatrix):
        self.sensor = sensor_node
        self.api_key = os.getenv("AI_AGENT_API_KEY", "").strip()
        self.model_name = os.getenv("AI_AGENT_MODEL", "llama-3.1-8b-instant").strip()
        self.base_url = os.getenv("AI_AGENT_BASE_URL", "https://api.groq.com/openai/v1").strip()

        self.client = None
        if self.api_key and OpenAI is not None:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _normalize_metrics(self, telemetry_data: Dict[str, Any]) -> Dict[str, float]:
        metrics = telemetry_data.get("metrics", {})
        return {
            "cpu": float(metrics.get("cpu_load_percentage", 0) or 0),
            "memory": float(metrics.get("memory_usage_percentage", 0) or 0),
            "disk": float(metrics.get("disk_usage_percentage", 0) or 0),
            "process_count": float(metrics.get("process_count", 0) or 0),
        }

    def _deterministic_decision(self, telemetry_data: Dict[str, Any], operational_goal: str) -> Dict[str, Any]:
        m = self._normalize_metrics(telemetry_data)

        score = 0
        reasons: List[str] = []
        anomalies: List[str] = []

        if m["cpu"] >= 90:
            score += 3
            anomalies.append("cpu_critical")
            reasons.append(f"CPU critically high at {m['cpu']}%.")
        elif m["cpu"] >= 75:
            score += 2
            anomalies.append("cpu_elevated")
            reasons.append(f"CPU elevated at {m['cpu']}%.")

        if m["memory"] >= 90:
            score += 3
            anomalies.append("memory_critical")
            reasons.append(f"Memory critically high at {m['memory']}%.")
        elif m["memory"] >= 80:
            score += 2
            anomalies.append("memory_elevated")
            reasons.append(f"Memory elevated at {m['memory']}%.")

        if m["disk"] >= 95:
            score += 3
            anomalies.append("disk_critical")
            reasons.append(f"Disk critically high at {m['disk']}%.")
        elif m["disk"] >= 85:
            score += 2
            anomalies.append("disk_elevated")
            reasons.append(f"Disk elevated at {m['disk']}%.")

        if m["process_count"] >= 450:
            score += 2
            anomalies.append("process_spike")
            reasons.append(f"Process count unusually high at {int(m['process_count'])}.")
        elif m["process_count"] >= 300:
            score += 1
            anomalies.append("process_elevated")
            reasons.append(f"Process count elevated at {int(m['process_count'])}.")

        if score >= 6:
            verdict = "TRIGGER_SELF_HEALING"
            priority = "CRITICAL"
            confidence = "HIGH"
        elif score >= 3:
            verdict = "REVIEW_AND_MONITOR"
            priority = "HIGH"
            confidence = "MEDIUM"
        else:
            verdict = "MAINTAIN_STEADY_STATE"
            priority = "LOW"
            confidence = "HIGH"

        if not reasons:
            reasons.append("All monitored system metrics are within normal thresholds.")

        return {
            "verdict": verdict,
            "execution_priority": priority,
            "confidence": confidence,
            "anomaly_score": score,
            "anomalies": anomalies,
            "reasoning_topology": " ".join(reasons),
            "goal": operational_goal,
            "used_llm": False,
            "llm_analysis": None,
        }

    def _llm_analysis(self, telemetry_data: Dict[str, Any], deterministic_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None

        system_prompt = (
            "You are a systems operations analysis assistant. "
            "Return valid JSON only. "
            "Do not override the deterministic verdict. "
            "Produce an object with keys: "
            "summary, operational_risk, recommended_next_step, notable_metric."
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
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=250,
            )
            content = response.choices[0].message.content
            if not content:
                return None
            parsed = json.loads(content)

            return {
                "summary": str(parsed.get("summary", "")).strip(),
                "operational_risk": str(parsed.get("operational_risk", "")).strip(),
                "recommended_next_step": str(parsed.get("recommended_next_step", "")).strip(),
                "notable_metric": str(parsed.get("notable_metric", "")).strip(),
            }
        except Exception as e:
            return {
                "summary": "",
                "operational_risk": "UNAVAILABLE",
                "recommended_next_step": "",
                "notable_metric": f"LLM unavailable: {str(e)}",
            }

    def consult_ai_core(self, telemetry_data: Dict[str, Any], operational_goal: str) -> Dict[str, Any]:
        deterministic = self._deterministic_decision(telemetry_data, operational_goal)
        llm_analysis = self._llm_analysis(telemetry_data, deterministic)

        if llm_analysis:
            deterministic["llm_analysis"] = llm_analysis
            deterministic["used_llm"] = True

        return deterministic

    def formulate_execution_strategy(self, task_objective: str) -> Dict[str, Any]:
        raw_telemetry = self.sensor.capture_runtime_vectors()
        strategy = self.consult_ai_core(raw_telemetry, task_objective)
        strategy["telemetry"] = raw_telemetry
        return strategy
