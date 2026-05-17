import os
import json
import math
import urllib.request
import urllib.parse
from openai import OpenAI
from core_telemetry import SystemTelemetryMatrix

class LLMAgentBrain:
    """
    Hyper-Advanced Operational Brain with Live Internet Search Tools.
    Can autonomously search the web and parse real-time global logs.
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
        """
        Tool: Autonomous Internet Web Scraper.
        Fetches live search context using an open search deployment layer.
        """
        try:
            encoded_query = urllib.parse.quote(query)
            # Connecting to an open-source high-speed search lookup layer
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            
            with urllib.request.urlopen(req, timeout=6) as response:
                html = response.read().decode('utf-8')
                
            # Quick autonomous snippet parsing
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            snippets = [r.get_text() for r in soup.find_all('a', class_='result__snippet')][:3]
            
            if snippets:
                return "\n".join(snippets)
            return "Internet search yielded nominal results. No patch logs found."
        except Exception as e:
            return f"Web Search Tool Error: Failed to fetch live data. Trace: {str(e)}"

    def consult_ai_bot(self, telemetry_data: dict, task: str) -> dict:
        if not self.client:
            return {"verdict": "MAINTAIN_STEADY_STATE", "reasoning_topology": "AI Client Offline."}

        # Step 1: Internet Context Injection
        print("🌐 [Agent Action] Initializing live web search protocol...")
        internet_context = self.execute_live_web_search("latest python optimization patch scripts 2026")

        system_prompt = (
            "You are a high-level Autonomous Mythos Agent with live internet access. "
            "You will receive live system telemetry AND real-time internet context regarding software optimization patches. "
            "Analyze both inputs. If telemetry shows drift OR if internet logs suggest a critical patch optimization, "
            "respond with a valid JSON object only. "
            "Keys required: 'verdict' ('TRIGGER_SELF_HEALING' or 'MAINTAIN_STEADY_STATE') "
            "and 'reasoning_topology' (Combine your internal thoughts with what you found live on the internet)."
        )
        
        user_prompt = (
            f"Objective: {task}\n"
            f"Live System Telemetry: {json.dumps(telemetry_data)}\n"
            f"Live Internet Context Found: {internet_context}"
        )

        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                response_format={ "type": "json_object" },
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"verdict": "MAINTAIN_STEADY_STATE", "reasoning_topology": f"Execution error: {str(e)}"}

    def formulate_execution_strategy(self, task_objective: str) -> dict:
        raw_telemetry = self.sensor.capture_runtime_vectors()
        ai_strategy = self.consult_ai_bot(raw_telemetry, task_objective)
        
        return {
            "verdict": ai_strategy.get("verdict", "MAINTAIN_STEADY_STATE"),
            "reasoning_topology": ai_strategy.get("reasoning_topology", "System diagnostic active."),
            "execution_priority": "CRITICAL" if ai_strategy.get("verdict") == "TRIGGER_SELF_HEALING" else "LOW"
        }
