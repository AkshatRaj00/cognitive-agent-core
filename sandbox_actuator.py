import json
from datetime import datetime
from typing import Any, Dict

from config import ALLOW_DOCKER, AUDIT_LOG_PATH, DOCKER_TARGET_CONTAINER

try:
    import docker
except Exception:
    docker = None


class SandboxActuatorEngine:
    def __init__(self):
        self.containment_cycles = 0

    def _append_audit(self, payload: Dict[str, Any]):
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _docker_containment(self) -> Dict[str, Any]:
        if not ALLOW_DOCKER:
            return {"status": "SKIPPED", "reason": "DOCKER_DISABLED"}
        if docker is None:
            return {"status": "FAILED", "reason": "DOCKER_SDK_NOT_AVAILABLE"}
        if not DOCKER_TARGET_CONTAINER:
            return {"status": "FAILED", "reason": "NO_TARGET_CONTAINER_CONFIGURED"}

        try:
            client = docker.from_env()
            container = client.containers.get(DOCKER_TARGET_CONTAINER)
            container.stop(timeout=5)
            return {"status": "COMPLETED", "target": DOCKER_TARGET_CONTAINER}
        except Exception as e:
            return {"status": "FAILED", "reason": str(e)}

    def execute_infrastructure_containment(self, strategic_payload: Dict[str, Any]) -> Dict[str, Any]:
        self.containment_cycles += 1
        action_result = self._docker_containment()

        audit_payload = {
            "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
            "event": "containment_attempt",
            "risk_level": strategic_payload.get("risk_level"),
            "action_result": action_result,
            "reasoning": strategic_payload.get("reasoning_topology"),
        }
        self._append_audit(audit_payload)
        return audit_payload
