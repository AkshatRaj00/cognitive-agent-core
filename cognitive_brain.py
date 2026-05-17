import os
import json
import math
from openai import OpenAI
from core_telemetry import SystemTelemetryMatrix

class LLMAgentBrain:
    """
    Advanced AI Bot Brain. Passes raw system telemetry vectors 
    directly to an LLM or fallback math heuristics to make autonomous decisions.
    """
    def __init__(self, sensor_node: SystemTelemetryMatrix):
        self.sensor = sensor_node
        self.cognitive_threshold = 65.0
        # Safe initialization of OpenAI/Gemini client
        self.api_key = os.environ.get("org_01krvpwrw8ffnsz27mhc1psgzh", "")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def compute_math_fallback(self, metrics: dict) -> dict:
        """Heuristic math engine that triggers if Cloud AI API key is not configured."""
        cpu = metrics.get("cpu_load_percentage", 0.0)
        drift = metrics.get("memory_drift_coefficient", 0.0)
        
        base_vector = (cpu * 0.4) + (drift * 0.6)
        entropy_factor = math.sin(base_vector) * 5.0
        anomaly_index = round(base_vector + entropy_factor, 4)
        
        if anomaly_index > self.cognitive_threshold:
            return {
                "verdict": "TRIGGER_SELF_HEALING",
                "reasoning_topology": f"Heuristic Engine Alert: Anomaly Index ({anomaly_index}) breached safety limits."
            }
        else:
            return {
                "verdict": "MAINTAIN_STEADY_STATE",
                "reasoning_topology": f"Heuristic Engine Nominal: System baseline stable at score {anomaly_index}."
            }

    def consult_ai_bot(self, telemetry_data: dict, task: str) -> dict:
        """Consults LLM Bot if key exists, otherwise gracefully falls back to Math Heuristics."""
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
                model="gpt-4o-mini",
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
