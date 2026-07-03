"""
Monitoring Service - real system + application monitoring.

System metrics come from psutil where available; application metrics (prediction
throughput, latency percentiles, error rate) come from the shared in-process
metrics store. Values degrade gracefully if psutil is unavailable.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from core.metrics import metrics

try:
    import psutil
except Exception:  # pragma: no cover
    psutil = None  # type: ignore


class MonitoringService:
    """Service for system monitoring."""

    def __init__(self):
        self.logger = logging.getLogger("monitoring_service")

    # ------------------------------------------------------------------
    # System + performance
    # ------------------------------------------------------------------
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Current system resource metrics (real where psutil is available)."""
        cpu = mem = disk = 0.0
        if psutil is not None:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
            try:
                disk = psutil.disk_usage("/").percent
            except Exception:
                disk = psutil.disk_usage("C:\\").percent if psutil else 0.0
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu_usage": round(cpu, 1),
            "memory_usage": round(mem, 1),
            "disk_usage": round(disk, 1),
            "npu_usage": None,
            "active_connections": 1,
            "request_rate": metrics.throughput_per_min(),
        }

    async def get_service_health(self) -> Dict[str, Any]:
        """Get health status of all services."""
        now = datetime.now(timezone.utc).isoformat()
        uptime = round(metrics.uptime_seconds(), 1)
        pct = metrics.latency_percentiles()
        return {
            "model_service": {
                "service_name": "model_service",
                "status": "healthy",
                "last_check": now,
                "uptime_seconds": uptime,
                "error_rate": metrics.error_rate(),
                "response_time_ms": pct["p50"],
            },
            "agent_service": {
                "service_name": "agent_service",
                "status": "healthy",
                "last_check": now,
                "uptime_seconds": uptime,
                "error_rate": metrics.error_rate(),
                "response_time_ms": pct["p95"],
            },
        }

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Latency percentiles + throughput from the live metrics store."""
        pct = metrics.latency_percentiles()
        return {
            "prediction_latency_p50": pct["p50"],
            "prediction_latency_p95": pct["p95"],
            "prediction_latency_p99": pct["p99"],
            "throughput": metrics.throughput_per_min(),
            "error_rate": metrics.error_rate(),
            "agent_execution_time": {},
        }

    # ------------------------------------------------------------------
    # Alerts (derived from live state)
    # ------------------------------------------------------------------
    async def get_alerts(self, resolved: bool = None) -> List[Dict[str, Any]]:
        """Derive alerts from current system + application state."""
        alerts: List[Dict[str, Any]] = []
        now = datetime.now(timezone.utc).isoformat()

        if psutil is not None:
            mem = psutil.virtual_memory().percent
            if mem > 85:
                alerts.append({
                    "alert_id": "mem_high",
                    "severity": "warning",
                    "message": f"High memory usage ({mem:.0f}%)",
                    "timestamp": now,
                    "service": "system",
                    "resolved": False,
                })

        if metrics.error_rate() > 0.05:
            alerts.append({
                "alert_id": "error_rate",
                "severity": "warning",
                "message": f"Elevated prediction error rate ({metrics.error_rate():.1%})",
                "timestamp": now,
                "service": "prediction",
                "resolved": False,
            })

        if metrics.predictions_total == 0:
            alerts.append({
                "alert_id": "no_traffic",
                "severity": "info",
                "message": "No predictions served yet in this session",
                "timestamp": now,
                "service": "prediction",
                "resolved": True,
            })

        if resolved is not None:
            alerts = [a for a in alerts if a["resolved"] == resolved]
        return alerts

    async def resolve_alert(self, alert_id: str) -> bool:
        return True

    async def get_dashboard_data(self) -> Dict[str, Any]:
        return {
            "system_metrics": await self.get_system_metrics(),
            "service_health": await self.get_service_health(),
            "performance_metrics": await self.get_performance_metrics(),
            "active_alerts": await self.get_alerts(resolved=False),
        }

    # ------------------------------------------------------------------
    # Consolidated analytics summary (feeds the frontend analytics page)
    # ------------------------------------------------------------------
    async def get_analytics_summary(self) -> Dict[str, Any]:
        """One payload with everything the analytics UI needs."""
        from services.data_service import DataService
        from services.evaluation_service import EvaluationService

        snap = metrics.snapshot()
        sources = await DataService().list_sources()
        connected = [s for s in sources if s["enabled"]]
        model_metrics = await EvaluationService().get_current_metrics()
        alerts = await self.get_alerts()
        sys_metrics = await self.get_system_metrics()

        counts = snap["category_counts"]
        total_cat = sum(counts.values()) or 1
        risk_distribution = {
            k.lower(): round(100 * v / total_cat, 1) for k, v in counts.items()
        }

        history = metrics.recent_latencies(7) or [0]
        perf = [
            {
                "title": "Prediction Latency (p50)",
                "value": f"{snap['latency_percentiles']['p50']} ms",
                "target": "< 100 ms",
                "status": "optimal" if snap["latency_percentiles"]["p50"] < 100 else "warning",
                "history": history,
            },
            {
                "title": "Throughput",
                "value": f"{snap['throughput_per_min']}/min",
                "target": "> 0",
                "status": "optimal",
                "history": history,
            },
            {
                "title": "CPU Utilization",
                "value": f"{sys_metrics['cpu_usage']}%",
                "target": "< 80%",
                "status": "optimal" if sys_metrics["cpu_usage"] < 80 else "warning",
                "history": history,
            },
            {
                "title": "Memory Usage",
                "value": f"{sys_metrics['memory_usage']}%",
                "target": "< 85%",
                "status": "optimal" if sys_metrics["memory_usage"] < 85 else "warning",
                "history": history,
            },
        ]

        return {
            "metrics": {
                "total_predictions": snap["predictions_total"],
                "accuracy_rate": model_metrics.get("auroc", 0.0),
                "accuracy_model": model_metrics.get("primary_model"),
                "active_data_sources": len(connected),
                "active_alerts": len([a for a in alerts if not a["resolved"]]),
                "avg_risk": snap["avg_risk"],
                "uptime_seconds": snap["uptime_seconds"],
            },
            "risk_distribution": risk_distribution,
            "category_counts": counts,
            "data_sources": [
                {
                    "name": s["name"],
                    "status": s["status"],
                    "records": f"{s['record_count']:,}" if s["enabled"] else "—",
                    "lastUpdate": snap["last_prediction_at"] or "—",
                }
                for s in sources
            ],
            "performance": perf,
            "alerts": [
                {
                    "id": a["alert_id"],
                    "severity": a["severity"],
                    "message": a["message"],
                    "time": a["timestamp"],
                    "status": "resolved" if a["resolved"] else "active",
                }
                for a in alerts
            ],
            "model_metrics": model_metrics,
            "llm": None,  # populated by the router (needs main.agent_service)
        }
