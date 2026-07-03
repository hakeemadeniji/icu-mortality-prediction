"""
Monitoring API endpoints for system health and performance monitoring
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class SystemMetrics(BaseModel):
    """System metrics model."""
    
    timestamp: str = Field(..., description="Metric timestamp")
    cpu_usage: float = Field(..., description="CPU usage percentage")
    memory_usage: float = Field(..., description="Memory usage percentage")
    disk_usage: float = Field(..., description="Disk usage percentage")
    gpu_usage: Optional[float] = Field(None, description="GPU usage percentage")
    npu_usage: Optional[float] = Field(None, description="NPU usage percentage")
    active_connections: int = Field(..., description="Active connections")
    request_rate: float = Field(..., description="Requests per second")


class ServiceHealth(BaseModel):
    """Service health model."""
    
    service_name: str = Field(..., description="Service name")
    status: str = Field(..., description="Health status")
    last_check: str = Field(..., description="Last health check timestamp")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    error_rate: float = Field(..., description="Error rate")
    response_time_ms: float = Field(..., description="Average response time")


class AlertInfo(BaseModel):
    """Alert information model."""
    
    alert_id: str = Field(..., description="Alert identifier")
    severity: str = Field(..., description="Alert severity")
    message: str = Field(..., description="Alert message")
    timestamp: str = Field(..., description="Alert timestamp")
    service: str = Field(..., description="Affected service")
    resolved: bool = Field(default=False, description="Whether alert is resolved")


class PerformanceMetrics(BaseModel):
    """Performance metrics model."""
    
    prediction_latency_p50: float = Field(..., description="50th percentile latency")
    prediction_latency_p95: float = Field(..., description="95th percentile latency")
    prediction_latency_p99: float = Field(..., description="99th percentile latency")
    throughput: float = Field(..., description="Requests per second")
    error_rate: float = Field(..., description="Error rate")
    agent_execution_time: Dict[str, float] = Field(
        default_factory=dict,
        description="Agent execution times"
    )


@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics():
    """Get current system metrics."""
    try:
        from services.monitoring_service import MonitoringService
        
        monitoring_service = MonitoringService()
        metrics = await monitoring_service.get_system_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=Dict[str, ServiceHealth])
async def get_service_health():
    """Get health status of all services."""
    try:
        from services.monitoring_service import MonitoringService
        
        monitoring_service = MonitoringService()
        health = await monitoring_service.get_service_health()
        return health
        
    except Exception as e:
        logger.error(f"Error getting service health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", response_model=List[AlertInfo])
async def get_alerts(resolved: Optional[bool] = None):
    """Get system alerts."""
    try:
        from services.monitoring_service import MonitoringService
        
        monitoring_service = MonitoringService()
        alerts = await monitoring_service.get_alerts(resolved)
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics():
    """Get performance metrics."""
    try:
        from services.monitoring_service import MonitoringService
        
        monitoring_service = MonitoringService()
        metrics = await monitoring_service.get_performance_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/status")
async def get_agents_status():
    """Get status of all AI agents."""
    try:
        from main import agent_service
        
        if not agent_service:
            raise HTTPException(status_code=503, detail="Agent service not ready")
        
        status = await agent_service.get_all_agents_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting agents status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert."""
    try:
        from services.monitoring_service import MonitoringService
        
        monitoring_service = MonitoringService()
        success = await monitoring_service.resolve_alert(alert_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        
        return {"status": "resolved", "alert_id": alert_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard_data():
    """Get consolidated dashboard data."""
    try:
        from services.monitoring_service import MonitoringService

        monitoring_service = MonitoringService()
        dashboard_data = await monitoring_service.get_dashboard_data()
        return dashboard_data

    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics-summary")
async def get_analytics_summary():
    """Consolidated payload for the analytics UI (metrics, sources, perf, alerts)."""
    try:
        from services.monitoring_service import MonitoringService
        from main import agent_service

        summary = await MonitoringService().get_analytics_summary()
        if agent_service:
            summary["llm"] = agent_service.llm_status()
        return summary

    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))