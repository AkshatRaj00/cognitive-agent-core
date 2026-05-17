import json
import logging
import re
from typing import Any, Dict, List, Optional

from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_ENABLE_WEB_SEARCH

logger = logging.getLogger(__name__)


class SovereignBrainEngine:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

    def _deterministic_triage(self, ingested_payload: Dict[str, Any]) -> Dict[str, Any]:
        if ingested_payload.get("status") != "SUCCESS":
            return {
                "risk_level": "UNKNOWN",
                "autonomous_action": "CONTINUE_MONITORING",
                "priority": "LOW",
                "reasoning_topology": f"Ingestion failed: {ingested_payload.get('reason', 'UNKNOWN')}",
                "signals": [],
            }

        text = ingested_payload.get("raw_payload", "")
        lowered = text.lower()
        signals: List[str] = []
        score = 0

        if re.search(r"CVE-\d{4}-\d{4,7}", text, re.I):
            signals.append("cve_reference")
            score += 2
        for keyword, weight in [
            ("critical", 2),
            ("rce", 3),
            ("remote code execution", 3),
            ("zero-day", 3),
            ("exploit", 2),
            ("privilege escalation", 2),
            ("malware", 2),
            ("ransomware", 3),
        ]:
            if keyword in lowered:
                signals.append(keyword)
                score += weight

        if score >= 7:
            risk = "CRITICAL"
            action = "TRIGGER_CONTAINMENT"
            priority = "CRITICAL"
        elif score >= 4:
            risk = "HIGH"
            action = "TRIGGER_CONTAINMENT"
            priority = "HIGH"
        elif score >= 2:
            risk = "MEDIUM"
            action = "CONTINUE_MONITORING"
            priority = "MEDIUM"
        else:
            risk = "LOW"
            action = "CONTINUE_MONITORING"
            priority = "LOW"

        reason = (
            "Deterministic triage completed based on source text indicators. "
            f"Detected signals: {signals if signals else ['none']}."
        )

        return {
            "risk_level": risk,
            "autonomous_action": action,
            "priority": priority,
            "reasoning_topology": reason,
            "signals": signals,
        }

    def _llm_enrichment(self, source_url: str, payload_text: str, deterministic_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None

        system_prompt = (
            "You are a defensive security analysis assistant. "
            "Do not invent facts. Respect the deterministic result and only enrich the explanation. "
            "Return strict JSON with keys: summary, recommended_next_step."
        )

        user_prompt = (
            f"Source: {source_url}\n"
            f"Deterministic result: {json.dumps(deterministic_result)}\n"
            f"Payload excerpt:\n{payload_text[:4000]}"
        )

        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                timeout=20,
            )
            parsed = json.loads(response.choices[0].message.content)
            return parsed
        except Exception as e:
            logger.warning(f"LLM enrichment failed: {e}")
            return None

    def execute_cognitive_triage(self, ingested_payload: Dict[str, Any]) -> Dict[str, Any]:
        deterministic = self._deterministic_triage(ingested_payload)

        enrichment = self._llm_enrichment(
            source_url=ingested_payload.get("source", ""),
            payload_text=ingested_payload.get("raw_payload", ""),
            deterministic_result=deterministic,
        )

        result = dict(deterministic)
        result["llm_enrichment"] = enrichment
        result["used_llm"] = enrichment is not None
        result["used_web_search_flag"] = OPENAI_ENABLE_WEB_SEARCH
        return result
