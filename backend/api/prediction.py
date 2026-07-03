"""
Prediction API endpoints for ICU mortality prediction
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any
import time
import logging

from core.metrics import metrics

logger = logging.getLogger(__name__)

router = APIRouter()


class PatientData(BaseModel):
    """Patient data model for prediction."""
    
    # Demographics
    age: int = Field(..., ge=18, le=120, description="Patient age in years")
    gender: str = Field(..., description="Patient gender (M/F)")
    ethnicity: Optional[str] = Field(None, description="Patient ethnicity")
    
    # Time-series data (48 hours of hourly data)
    vital_signs: List[Dict[str, float]] = Field(
        ...,
        description="Hourly vital signs for 48 hours"
    )
    lab_values: List[Dict[str, float]] = Field(
        ...,
        description="Hourly lab values for 48 hours"
    )
    
    # Clinical notes
    clinical_notes: Optional[str] = Field(None, description="Clinical notes text")
    
    # Comorbidities
    comorbidities: Optional[List[str]] = Field(
        default_factory=list,
        description="List of comorbidities"
    )
    
    # Medications
    medications: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Current medications"
    )


class PredictionResponse(BaseModel):
    """Prediction response model."""
    
    mortality_risk: float = Field(..., ge=0.0, le=1.0, description="Mortality risk score")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Prediction confidence")
    prediction_time: float = Field(..., description="Time taken for prediction (seconds)")
    model_version: str = Field(..., description="Model version used")
    agent_contributions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contributions from different agents"
    )
    risk_factors: List[str] = Field(
        default_factory=list,
        description="Identified risk factors"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Clinical recommendations"
    )
    explanation: Optional[str] = Field(None, description="Prediction explanation")


class BatchPredictionRequest(BaseModel):
    """Batch prediction request model."""
    
    patients: List[PatientData] = Field(..., description="List of patient data")
    priority: Optional[str] = Field("normal", description="Processing priority")


class BatchPredictionResponse(BaseModel):
    """Batch prediction response model."""
    
    predictions: List[PredictionResponse] = Field(..., description="List of predictions")
    total_time: float = Field(..., description="Total processing time (seconds)")
    successful: int = Field(..., description="Number of successful predictions")
    failed: int = Field(..., description="Number of failed predictions")


class ClinicalSnapshot(BaseModel):
    """Bedside snapshot sent by the dashboard (camelCase keys).

    All fields have defaults so a partial payload never fails validation;
    unknown keys are ignored.
    """

    model_config = ConfigDict(extra="ignore")

    age: int = Field(65, ge=0, le=120)
    gender: str = "M"
    heartRate: float = 80
    bloodPressureSystolic: float = 120
    bloodPressureDiastolic: float = 80
    temperature: float = 37.0
    respiratoryRate: float = 16
    oxygenSaturation: float = 98
    sofaScore: float = 0
    comorbidityCount: int = 0


@router.post("/predict")
async def predict_mortality(snapshot: ClinicalSnapshot):
    """
    Predict ICU mortality for a single patient bedside snapshot.

    Returns a JSON shape consumed directly by the dashboard (camelCase):
    ``mortalityRisk``, ``confidence``, ``riskCategory``, ``keyFactors``,
    ``recommendations`` and ``agentStatus``.
    """
    try:
        logger.info(f"Received prediction request for patient age {snapshot.age}")

        # Import here to avoid circular dependencies
        from main import model_service, agent_service

        if not model_service or not model_service.is_ready():
            raise HTTPException(status_code=503, detail="Model service not ready")

        features = snapshot.model_dump()
        start = time.perf_counter()
        result = model_service.predict(features)

        # Live AI-agent narrative (Claude/GLM). Best-effort: None if no key /
        # provider unreachable, in which case the field is simply omitted.
        explanation = None
        if agent_service:
            explanation = await agent_service.generate_clinical_explanation(features, result)

        elapsed = time.perf_counter() - start

        metrics.record_prediction(
            latency_ms=elapsed * 1000.0,
            category=result["risk_category"],
            risk=result["mortality_risk"],
        )

        total_agents = len(await agent_service.list_agents()) if agent_service else 0
        active_agents = agent_service.get_active_agents() if agent_service else 0

        response = {
            "mortalityRisk": result["mortality_risk"],
            "confidence": result["confidence"],
            "riskCategory": result["risk_category"],
            "keyFactors": result["key_factors"],
            "recommendations": result["recommendations"],
            "modelVersion": result["model_version"],
            "agentStatus": {
                "total": total_agents,
                "active": active_agents,
                "processingTime": f"{elapsed:.2f}s",
            },
        }
        if explanation:
            response["explanation"] = explanation
        return response

    except HTTPException:
        raise
    except Exception as e:
        metrics.record_error()
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(batch_request: BatchPredictionRequest):
    """
    Predict ICU mortality for multiple patients in batch.
    
    Optimized for processing multiple patients efficiently using
    parallel processing and batch inference.
    """
    try:
        logger.info(f"Received batch prediction request for {len(batch_request.patients)} patients")
        
        from main import agent_service
        
        if not agent_service or not agent_service.is_ready():
            raise HTTPException(status_code=503, detail="Agent service not ready")
        
        # Process batch
        batch_result = await agent_service.process_batch(batch_request.patients)
        
        return BatchPredictionResponse(**batch_result)
        
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def list_models():
    """List available prediction models."""
    try:
        from main import model_service
        
        if not model_service:
            raise HTTPException(status_code=503, detail="Model service not ready")
        
        models = await model_service.list_models()
        return {
            "models": models,
            "default_model": models[0] if models else None,
            "total_models": len(models)
        }
        
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_prediction_status():
    """Get prediction system status."""
    try:
        from main import model_service, agent_service, rag_service
        
        status = {
            "model_service": {
                "ready": model_service.is_ready() if model_service else False,
                "onnx_optimized": True,
                "arm64_optimized": True,
                "npu_enabled": True
            },
            "agent_service": {
                "ready": agent_service.is_ready() if agent_service else False,
                "active_agents": agent_service.get_active_agents() if agent_service else 0,
                "total_agents": 20
            },
            "rag_service": {
                "ready": rag_service.is_ready() if rag_service else False,
                "knowledge_base_size": await rag_service.get_kb_size() if rag_service else 0
            }
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))