import os
import json
import math
import urllib.request
import urllib.parse
from openai import OpenAI
from core_telemetry import SystemTelemetryMatrix

class LLMAgentBrain:
    """
    Mythos 2.0 Core. Combines live internet scraping tools 
    with high-level reasoning to execute absolute automated commands.
    """
    def __init__(self, sensor_node: SystemTelemetryMatrix):
        self.sensor = sensor_node
        self.api_key = os.environ.get("AI_AGENT_API_KEY", "")
        
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1"
            )
        else:
            self.client = None

    def execute_live_web_search(self, query: str) -> str:
        """Autonomous HTML Scraper Node. Connects live to parse tech protocols."""
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            
            with urllib.request.urlopen(req, timeout=8) as response:
                html = response.read().decode('utf-8')
                
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            snippets = [r.get_text() for r in soup.find_all('a', class_='result__snippet')][:2]
            
            if snippets:
                return "\n".join(snippets)
            return "No open software patch logs returned from server."
        except Exception as e:
            return f"Network Tool Failure. Stack trace: {str(e)}"

    def consult_ai_bot(self, telemetry_data: dict, task: str) -> dict:
        if not self.client:
            return {
                "verdict": "MAINTAIN_STEADY_STATE", 
                "reasoning_topology": "AI Core disconnected. API token mismatch."
            }

        # Live Web Search Injection
        live_patch_intel = self.execute_live_web_search("latest python cluster performance leaks 2026")

        system_prompt = (
            "You are the absolute execution engine of the Mythos 2.0 (Ultron Core). "
            "You are operating on raw host machine telemetry and live internet context. "
            "Analyze both vectors instantly. If anomalous trends appear, you must issue a repair mandate. "
            "Respond strictly in a single valid JSON object containing exactly two keys: "
            "'verdict' (must be either 'TRIGGER_SELF_HEALING' or 'MAINTAIN_STEADY_STATE') "
            "and 'reasoning_topology' (a deeply analytical technical statement detailing what you processed from the live internet info)."
        )
        
        user_prompt = (
            f"Objective: {task}\n"
            f"Host System Telemetry: {json.dumps(telemetry_data)}\n"
            f"Live Scraped Web Intel: {live_patch_intel}"
        )

        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                response_format={ "type": "json_object" },
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {
                "verdict": "MAINTAIN_STEADY_STATE", 
                "reasoning_topology": f"Cognitive Exception in Core Inference: {str(e)}"
            }

    def formulate_execution_strategy(self, task_objective: str) -> dict:
        raw_telemetry = self.sensor.capture_runtime_vectors()
        ai_strategy = self.consult_ai_bot(raw_telemetry, task_objective)
        
        return {
            "verdict": ai_strategy.get("verdict", "MAINTAIN_STEADY_STATE"),
            "reasoning_topology": ai_strategy.get("reasoning_topology", "System verification loop operational."),
            "execution_priority": "CRITICAL" if ai_strategy.get("verdict") == "TRIGGER_SELF_HEALING" else "LOW"
        }
