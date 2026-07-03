"""
In-process metrics store.

A single shared instance tracks real activity (predictions served, latencies,
risk-category mix, uptime) so the analytics/monitoring endpoints can report live
numbers instead of hard-coded placeholders. Thread-safe for the mixed sync/async
access pattern of FastAPI.
"""

import time
from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional


class Metrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self.started_at = time.time()
        self.predictions_total = 0
        self.errors_total = 0
        self.latencies_ms: deque = deque(maxlen=500)
        self.category_counts: Dict[str, int] = {
            "LOW": 0,
            "MODERATE": 0,
            "HIGH": 0,
            "CRITICAL": 0,
        }
        self.risk_sum = 0.0
        self.last_prediction_at: Optional[str] = None

    def record_prediction(self, latency_ms: float, category: str, risk: float) -> None:
        with self._lock:
            self.predictions_total += 1
            self.latencies_ms.append(float(latency_ms))
            if category in self.category_counts:
                self.category_counts[category] += 1
            self.risk_sum += float(risk)
            self.last_prediction_at = datetime.now(timezone.utc).isoformat()

    def record_error(self) -> None:
        with self._lock:
            self.errors_total += 1

    def uptime_seconds(self) -> float:
        return time.time() - self.started_at

    def _percentile(self, pct: float) -> float:
        data = sorted(self.latencies_ms)
        if not data:
            return 0.0
        k = max(0, min(len(data) - 1, int(round((pct / 100.0) * (len(data) - 1)))))
        return round(data[k], 1)

    def latency_percentiles(self) -> Dict[str, float]:
        return {
            "p50": self._percentile(50),
            "p95": self._percentile(95),
            "p99": self._percentile(99),
        }

    def throughput_per_min(self) -> float:
        minutes = max(self.uptime_seconds() / 60.0, 1e-6)
        return round(self.predictions_total / minutes, 2)

    def error_rate(self) -> float:
        total = self.predictions_total + self.errors_total
        return round(self.errors_total / total, 4) if total else 0.0

    def recent_latencies(self, n: int = 7) -> List[float]:
        return [round(x, 1) for x in list(self.latencies_ms)[-n:]]

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "predictions_total": self.predictions_total,
                "errors_total": self.errors_total,
                "category_counts": dict(self.category_counts),
                "avg_risk": round(self.risk_sum / self.predictions_total, 3)
                if self.predictions_total
                else 0.0,
                "uptime_seconds": round(self.uptime_seconds(), 1),
                "last_prediction_at": self.last_prediction_at,
                "latency_percentiles": self.latency_percentiles(),
                "throughput_per_min": self.throughput_per_min(),
                "error_rate": self.error_rate(),
            }


# Shared singleton — import `metrics` everywhere.
metrics = Metrics()
