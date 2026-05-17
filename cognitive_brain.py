import time
import math
from typing import Dict, Any, List
# Interconnecting with our first module dynamically
from core_telemetry import SystemTelemetryMatrix

class CognitiveMatrixEngine:
    """
    The Central Reasoning Core. Processes real-time environmental 
    telemetry vectors through advanced algorithmic evaluation thresholds.
    """
    def __init__(self, sensor_node: SystemTelemetryMatrix):
        self.sensor = sensor_node
        self.anomaly_log: List[Dict[str, Any]] = []
        self.cognitive_threshold: float = 65.0  # Dynamic control limit

    def compute_anomaly_index(self, metrics: Dict[str, Any]) -> float:
        """
        Calculates localized mathematical entropy from raw system telemetry.
        Uses sinusoidal smoothing to simulate human-like threshold evaluation.
        """
        cpu = metrics.get("cpu_load_percentage", 0.0)
        drift = metrics.get("memory_drift_coefficient", 0.0)
        
        # Advanced weight matrix formula to calculate anomalous system states
        base_load_vector = (cpu * 0.4) + (drift * 0.6)
        entropy_factor = math.sin(base_load_vector) * 5.0
        
        return round(base_load_vector + entropy_factor, 4)

    def formulate_execution_strategy(self, task_objective: str) -> Dict[str, Any]:
        """Reads live data, evaluates state, and self-corrects the path."""
        print(f"\n🧠 [Brain-Core] Analyzing operational vectors for objective: '{task_objective}'")
        
        # Extract live metrics from our interconnected core_telemetry file
        raw_telemetry = self.sensor.capture_runtime_vectors()
        metrics = raw_telemetry.get("metrics", {})
        
        # Algorithmic decision score
        anomaly_index = self.compute_anomaly_index(metrics)
        print(f"🧠 [Brain-Core] Computed System Anomaly Index: {anomaly_index}")

        # Self-correction logic based on live parameters
        if anomaly_index > self.cognitive_threshold:
            decision = "TRIGGER_SELF_HEALING"
            reasoning = f"Anomaly Index ({anomaly_index}) breached threshold ({self.cognitive_threshold}). Resource optimization required."
        else:
            decision = "MAINTAIN_STEADY_STATE"
            reasoning = "System telemetry registers nominal entropy. Operational state is optimal."

        strategy_payload = {
            "timestamp": time.time(),
            "verdict": decision,
            "reasoning_topology": reasoning,
            "target_telemetry_signature": raw_telemetry.get("environment_signature"),
            "execution_priority": "CRITICAL" if anomaly_index > self.cognitive_threshold else "LOW"
        }
        
        self.anomaly_log.append(strategy_payload)
        return strategy_payload

if __name__ == "__main__":
    # Local runtime emulation for interconnected modules
    sensor_instance = SystemTelemetryMatrix()
    brain_instance = CognitiveMatrixEngine(sensor_node=sensor_instance)
    
    # Simulating a core task check
    verdict = brain_instance.formulate_execution_strategy("Verify active micro-service cluster reliability.")
    print("🧠 [Brain verdict payload]:\n", json.dumps(verdict, indent=4))
