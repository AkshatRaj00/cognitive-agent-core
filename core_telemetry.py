import os
import platform
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import psutil


class SystemTelemetryMatrix:
    """
    Safe local telemetry collector.
    Collects real host metrics without fake fallback values.
    """

    def __init__(self):
        self.os_type = platform.system()
        self.architecture = platform.machine()
        self.hostname = platform.node()
        self._prime_cpu_reader()

    def _prime_cpu_reader(self) -> None:
        try:
            psutil.cpu_percent(interval=None)
        except Exception:
            pass

    @staticmethod
    def _safe_load_average() -> Optional[Tuple[float, float, float]]:
        if hasattr(os, "getloadavg"):
            try:
                return tuple(round(x, 2) for x in os.getloadavg())
            except OSError:
                return None
        return None

    def capture_runtime_vectors(self) -> Dict[str, Any]:
        vm = psutil.virtual_memory()
        disk = psutil.disk_usage(str(Path.home()))
        net = psutil.net_io_counters()
        boot_time = datetime.fromtimestamp(psutil.boot_time()).isoformat(timespec="seconds")

        cpu_load = psutil.cpu_percent(interval=0.1)

        return {
            "telemetry_status": "ONLINE",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "environment_signature": f"{self.os_type}_{self.architecture}",
            "hostname": self.hostname,
            "boot_time": boot_time,
            "metrics": {
                "cpu_load_percentage": round(cpu_load, 2),
                "memory_usage_percentage": round(vm.percent, 2),
                "memory_used_gb": round(vm.used / (1024 ** 3), 2),
                "memory_total_gb": round(vm.total / (1024 ** 3), 2),
                "disk_usage_percentage": round(disk.percent, 2),
                "disk_used_gb": round(disk.used / (1024 ** 3), 2),
                "disk_total_gb": round(disk.total / (1024 ** 3), 2),
                "process_count": len(psutil.pids()),
                "network_bytes_sent": int(net.bytes_sent),
                "network_bytes_recv": int(net.bytes_recv),
                "load_average": self._safe_load_average(),
            },
            "python_version": sys.version.split()[0],
        }
