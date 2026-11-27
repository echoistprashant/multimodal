"""Thread-Safe Lightweight Observability Metrics Collector."""

import threading
from typing import Any, Dict, List


class MetricsCollector:
    """Tracks operational counters and latency histograms across MDIS pipeline stages."""

    _instance: "MetricsCollector | None" = None
    _singleton_lock = threading.Lock()

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._counters: Dict[str, int] = {}
        self._timings_ms: Dict[str, List[float]] = {}

    @classmethod
    def get_instance(cls) -> "MetricsCollector":
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def increment(self, metric_name: str, value: int = 1) -> None:
        with self._lock:
            self._counters[metric_name] = self._counters.get(metric_name, 0) + value

    def record_latency(self, stage_name: str, latency_ms: float) -> None:
        with self._lock:
            self._timings_ms.setdefault(stage_name, []).append(round(latency_ms, 2))

    def snapshot(self) -> Dict[str, Any]:
        """Return JSON-serializable snapshot of all counters and latency percentiles."""
        with self._lock:
            timing_summary: Dict[str, Dict[str, float]] = {}
            for name, vals in self._timings_ms.items():
                if not vals:
                    continue
                sorted_v = sorted(vals)
                p95_idx = min(len(sorted_v) - 1, int(0.95 * len(sorted_v)))
                timing_summary[name] = {
                    "count": float(len(vals)),
                    "avg_ms": round(sum(vals) / len(vals), 2),
                    "p95_ms": sorted_v[p95_idx],
                }
            return {
                "counters": dict(self._counters),
                "latencies": timing_summary,
            }

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._timings_ms.clear()
