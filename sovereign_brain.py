import json
import re
from typing import Any, Dict, List, Optional

from openai import OpenAI

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


class SovereignBrainEngine:
    def __init__(self):
        self.client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL) if LLM_API_KEY else None

    def _keyword_hits(self, text: str) -> List[str]:
        text_l = text.lower()
        hits = []

        patterns = {
            "cve_reference": r"\bCVE-\d{4}-\d{4,7}\b",
            "remote_code_execution": r"\bremote code execution\b",
            "privilege_escalation": r"\bprivilege escalation\b",
            "zero_day": r"\bzero-day\b|\b0-day\b",
            "ransomware": r"\bransomware\b",
            "malware": r"\bmalware\b",
            "exploit": r"\bexploit(s|ed|ing)?\b",
            "patch": r"\bpatch(ed|es|ing)?\b",
            "advisory": r"\badvisory\b",
            "vulnerability": r"\bvulnerab(il|ility|ilities)\b",
        }

        for name, pattern in patterns.items():
            if re.search(pattern, text, re.I):
                hits.append(name)

        return hits

    def _score(self, hits: List[str], trust_score: int, is_html: bool) -> Dict[str, Any]:
        weights = {
            "cve_reference": 4,
            "remote_code_execution": 4,
            "privilege_escalation": 3,
            "zero_day": 4,
            "ransomware": 4,
            "malware": 2,
            "exploit": 2,
            "patch": 1,
            "advisory": 1,
            "vulnerability": 1,
        }

        score = sum(weights.get(h, 0) for h in hits)
        score += min(trust_score, 3)

        if is_html and trust_score == 0 and "cve_reference" not in hits:
            score = max(0, score - 2)

        if score >= 8:
            return {"risk_level": "HIGH", "autonomous_action": "TRIGGER_CONTAINMENT", "priority": "HIGH", "score": score}
        if score >= 4:
            return {"risk_level": "MEDIUM", "autonomous_action": "CONTINUE_MONITORING", "priority": "MEDIUM", "score": score}
        return {"risk_level": "LOW", "autonomous_action": "CONTINUE_MONITORING", "priority": "LOW", "score": score}

    def _llm_enrichment(self, source_url: str, payload_text: str, hits: List[str], score_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None

        system = (
            "You are a defensive cyber triage assistant. "
            "Return strict JSON with keys: summary, recommended_next_step, confidence_note. "
            "Do not invent incidents. If text looks like generic webpage content, say so."
        )

        user = (
            f"Source URL: {source_url}\n"
            f"Signals: {hits}\n"
            f"Score Result: {json.dumps(score_result)}\n"
            f"Payload excerpt:\n{payload_text[:5000]}"
        )

        try:
            response = self.client.chat.completions.create(
                model=LLM_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.1,
                timeout=20,
            )
            return json.loads(response.choices[0].message.content)
        except Exception:
            return None

    def execute_cognitive_triage(self, ingested_payload: Dict[str, Any]) -> Dict[str, Any]:
        if ingested_payload.get("status") != "SUCCESS":
            return {
                "risk_level": "UNKNOWN",
                "autonomous_action": "CONTINUE_MONITORING",
                "priority": "LOW",
                "reasoning_topology": f"Ingestion failed: {ingested_payload.get('reason', 'UNKNOWN')}",
                "signals": [],
                "llm_enrichment": None,
                "used_llm": False,
            }

        text = ingested_payload.get("raw_payload", "")
        hits = self._keyword_hits(text)
        scored = self._score(
            hits=hits,
            trust_score=ingested_payload.get("trust_score", 0),
            is_html=ingested_payload.get("is_html", False),
        )

        enrichment = self._llm_enrichment(
            source_url=ingested_payload.get("source", ""),
            payload_text=text,
            hits=hits,
            score_result=scored,
        )

        reason = (
            f"Semantic triage completed. Signals={hits if hits else ['none']}, "
            f"trust_score={ingested_payload.get('trust_score', 0)}, "
            f"is_html={ingested_payload.get('is_html', False)}, "
            f"score={scored['score']}."
        )

        return {
            "risk_level": scored["risk_level"],
            "autonomous_action": scored["autonomous_action"],
            "priority": scored["priority"],
            "reasoning_topology": reason,
            "signals": hits,
            "score": scored["score"],
            "llm_enrichment": enrichment,
            "used_llm": enrichment is not None,
        }
