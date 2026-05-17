import os
import json
import math
from openai import OpenAI
from core_telemetry import SystemTelemetryMatrix

class LLMAgentBrain:
    """
    Advanced AI Bot Brain powered by Groq's Hyper-Fast Free API.
    """
    def __init__(self, sensor_node: SystemTelemetryMatrix):
        self.sensor = sensor_node
        self.cognitive_threshold = 65.0
        self.api_key = os.environ.get("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", "")
        
        if self.api_key:
            # Connecting directly to Groq's high-speed free cloud server
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1"
            )
        else:
            self.client = None

    def compute_math_fallback(self, metrics: dict) -> dict:
        cpu = metrics.get("cpu_load_percentage", 0.0)
        drift = metrics.get("memory_drift_coefficient", 0.0)
        base_vector = (cpu * 0.4) + (drift * 0.6)
        entropy_factor = math.sin(base_vector) * 5.0
        anomaly_index = round(base_vector + entropy_factor, 4)
        
        if anomaly_index > self.cognitive_threshold:
            return {
                "verdict": "TRIGGER_SELF_HEALING",
                "reasoning_topology": f"Fallback: High entropy detected ({anomaly_index})."
            }
        else:
            return {
                "verdict": "MAINTAIN_STEADY_STATE",
                "reasoning_topology": f"Fallback: Nominal state ({anomaly_index})."
            }

    def consult_ai_bot(self, telemetry_data: dict, task: str) -> dict:
        if not self.client:
            return self.compute_math_fallback(telemetry_data.get("metrics", {}))

        system_prompt = (
            "You are the autonomous execution core of a hybrid AI Agent. "
            "Analyze raw system telemetry for anomalies. Respond ONLY in a valid JSON object "
            "with keys: 'verdict' ('TRIGGER_SELF_HEALING' or 'MAINTAIN_STEADY_STATE') "
            "and 'reasoning_topology' (technical analysis description)."
        )
        user_prompt = f"Objective: {task}\nTelemetry: {json.dumps(telemetry_data)}"

        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Ultra-fast, high-limit free model on Groq
                response_format={ "type": "json_object" },
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return self.compute_math_fallback(telemetry_data.get("metrics", {}))

    def formulate_execution_strategy(self, task_objective: str) -> dict:
        raw_telemetry = self.sensor.capture_runtime_vectors()
        ai_strategy = self.consult_ai_bot(raw_telemetry, task_objective)
        
        return {
            "verdict": ai_strategy.get("verdict", "MAINTAIN_STEADY_STATE"),
            "reasoning_topology": ai_strategy.get("reasoning_topology", "System diagnostic active."),
            "execution_priority": "CRITICAL" if ai_strategy.get("verdict") == "TRIGGER_SELF_HEALING" else "LOW"
        }
