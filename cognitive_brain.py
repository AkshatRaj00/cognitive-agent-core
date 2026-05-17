import os
import json
from openai import OpenAI
from core_telemetry import SystemTelemetryMatrix

class LLMAgentBrain:
    """
    Production-Grade Grounded Cognitive Engine. 
    Analyzes real-time metrics against hard host environments without hallucination.
    """
    def __init__(self, sensor_node: SystemTelemetryMatrix):
        self.sensor = sensor_node
        # Utilizing our secure Groq Cloud pipeline
        self.api_key = os.environ.get("AI_AGENT_API_KEY", "")
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1"
            )
        else:
            self.client = None

    def consult_ai_core(self, telemetry_data: dict, operational_goal: str) -> dict:
        if not self.client:
            return {"verdict": "MAINTAIN_STEADY_STATE", "reasoning_topology": "AI Client Offline."}

        # Hardened system prompt: Explicitly forcing the model to stick to reality
        system_prompt = (
            "You are a production-grade Infrastructure Operations Agent. You manage real-world host telemetry. "
            "Analyze the incoming metrics dictionary. Do not hallucinate external exploits or fake CVE threats. "
            "If the memory_drift_coefficient is above 75.0% OR CPU load is consistently high, issue a TRIGGER_SELF_HEALING mandate. "
            "Otherwise, maintain baseline operations. You must respond ONLY in a valid JSON object with keys: "
            "'verdict' ('TRIGGER_SELF_HEALING' or 'MAINTAIN_STEADY_STATE') and 'reasoning_topology' (a precise, fact-based engineering summary)."
        )
        
        user_prompt = f"Operational Objective: {operational_goal}\nLive Telemetry Stream: {json.dumps(telemetry_data)}"

        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                response_format={ "type": "json_object" },
                messages=[
                    {"role": "system", "prompt": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1  # Absolute lowest entropy for factual precision
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"verdict": "MAINTAIN_STEADY_STATE", "reasoning_topology": f"Inference pipeline exception: {str(e)}"}

    def formulate_execution_strategy(self, task_objective: str) -> dict:
        raw_telemetry = self.sensor.capture_runtime_vectors()
        ai_strategy = self.consult_ai_core(raw_telemetry, task_objective)
        
        return {
            "verdict": ai_strategy.get("verdict", "MAINTAIN_STEADY_STATE"),
            "reasoning_topology": ai_strategy.get("reasoning_topology", "Telemetry verification cycle secure."),
            "execution_priority": "CRITICAL" if ai_strategy.get("verdict") == "TRIGGER_SELF_HEALING" else "LOW"
        }
