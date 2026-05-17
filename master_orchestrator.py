from datetime import datetime
from typing import Any, Dict, List, Optional

from cyber_scout import CyberScoutEngine
from memory_store import MemoryStore
from sandbox_actuator import SandboxActuatorEngine
from sovereign_brain import SovereignBrainEngine


class MasterOrchestrator:
    def __init__(self):
        self.scout = CyberScoutEngine()
        self.brain = SovereignBrainEngine()
        self.actuator = SandboxActuatorEngine()
        self.memory = MemoryStore()

    def run_single_cycle(self, target_feed: str) -> Dict[str, Any]:
        ingestion = self.scout.fetch_threat_intelligence_feed(target_feed)
        decision = self.brain.execute_cognitive_triage(ingestion)

        actuator_report = None
        if decision.get("autonomous_action") == "TRIGGER_CONTAINMENT":
            actuator_report = self.actuator.execute_infrastructure_containment(decision)

        result = {
            "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
            "source": target_feed,
            "ingestion": ingestion,
            "decision": decision,
            "actuator_report": actuator_report,
        }

        self.memory.save_run(
            source=target_feed,
            verdict=decision.get("autonomous_action", "UNKNOWN"),
            priority=decision.get("priority", "LOW"),
            payload=result,
        )
        return result

    def recent_runs(self, limit: int = 10):
        return self.memory.recent_runs(limit=limit)

    def recent_memories(self, limit: int = 10):
        return self.memory.recent_memories(limit=limit)
