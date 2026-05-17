import os
import json
from openai import OpenAI  # AI Bot core library
from core_telemetry import SystemTelemetryMatrix

class LLMAgentBrain:
    """
    Advanced AI Bot Brain. Passes raw system telemetry vectors 
    directly to an LLM (Gemini/OpenAI) to make autonomous decisions.
    """
    def __init__(self, sensor_node: SystemTelemetryMatrix):
        self.sensor = sensor_node
        # Initializing the AI Client (Can be pointed to Google Gemini or OpenAI)
        self.client = OpenAI(
            api_key=os.environ.get("AI_AGENT_API_KEY", "your-fallback-key")
        )

    def consult_ai_bot(self, telemetry_data: dict, task: str) -> dict:
        """Sends telemetry matrices to the AI Bot and gets a structured JSON verdict."""
        
        # System instructions to lock the AI into a strict Developer/Agent mindset
        system_prompt = (
            "You are the autonomous execution core of a hybrid AI Agent. "
            "You will receive raw system telemetry. Analyze it for memory leaks, "
            "high CPU stress, or environment drift. You must respond ONLY in a valid JSON object "
            "with keys: 'verdict' (either 'TRIGGER_SELF_HEALING' or 'MAINTAIN_STEADY_STATE') "
            "and 'reasoning_topology' (a short technical description of your analysis)."
        )

        user_prompt = f"Objective: {task}\nLive System Telemetry: {json.dumps(telemetry_data)}"

        try:
            # Triggering the AI Bot (Gemini-flash / GPT-4o style execution)
            response = self.client.chat.completions.create(
                model="gpt-4o-mini", # Or gemini-2.5-flash / gemini-1.5-pro
                response_format={ "type": "json_object" }, # Enforcing strict JSON outputs
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2 # Keeping it precise and low-entropy
            )
            
            # Parsing the AI Bot's thoughts
            ai_verdict = json.loads(response.choices[0].message.content)
            return ai_verdict
            
        except Exception as e:
            # Self-healing fallback if API fails or times out
            return {
                "verdict": "MAINTAIN_STEADY_STATE",
                "reasoning_topology": f"AI Bot Connection Timeout. Fallback active. Error: {str(e)}"
            }

    def formulate_execution_strategy(self, task_objective: str) -> dict:
        print(f"\n🧠 [AI-Brain] Dispatching system logs to LLM Cloud Engine...")
        
        # 1. Fetch live telemetry from our first module
        raw_telemetry = self.sensor.capture_runtime_vectors()
        
        # 2. Consult the AI Bot (Gemini/OpenAI)
        ai_strategy = self.consult_ai_bot(raw_telemetry, task_objective)
        
        print(f"🤖 [AI Bot Verdict]: {ai_strategy.get('verdict')}")
        print(f"📖 [AI Bot Reasoning]: {ai_strategy.get('reasoning_topology')}")
        
        return {
            "verdict": ai_strategy.get("verdict"),
            "reasoning_topology": ai_strategy.get("reasoning_topology"),
            "execution_priority": "CRITICAL" if ai_strategy.get("verdict") == "TRIGGER_SELF_HEALING" else "LOW"
        }
