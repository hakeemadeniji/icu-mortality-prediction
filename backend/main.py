"""
ICU Mortality Prediction System - Main FastAPI Application
Full-stack backend with AI agent orchestration, RAG, and ONNX optimization
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from pathlib import Path

# Import API routers
from api import prediction, agents, data, monitoring, evaluation
from core.config import settings
from core.logging import setup_logging
from services.model_service import ModelService
from services.agent_service import AgentService
from services.rag_service import RAGService

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize services
model_service = None
agent_service = None
rag_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    global model_service, agent_service, rag_service
    
    # Startup
    logger.info("Starting ICU Mortality Prediction System...")
    
    try:
        # Initialize core services
        model_service = ModelService()
        await model_service.initialize()
        
        agent_service = AgentService()
        await agent_service.initialize()
        
        rag_service = RAGService()
        await rag_service.initialize()
        
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down services...")
    if model_service:
        await model_service.cleanup()
    if agent_service:
        await agent_service.cleanup()
    if rag_service:
        await rag_service.cleanup()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="ICU Mortality Prediction System",
    description="Advanced AI-powered ICU mortality prediction with 15+ specialized agents and RAG",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(prediction.router, prefix="/api/v1/prediction", tags=["prediction"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(data.router, prefix="/api/v1/data", tags=["data"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["monitoring"])
app.include_router(evaluation.router, prefix="/api/v1/evaluation", tags=["evaluation"])


@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "system": "ICU Mortality Prediction System",
        "version": "2.0.0",
        "status": "operational",
        "architecture": "full-stack with 15+ AI agents",
        "optimization": "ONNX + ARM64 Snapdragon NPU",
        "features": [
            "Real-time mortality prediction",
            "Multi-agent AI system",
            "RAG-based knowledge retrieval",
            "Continuous evaluation",
            "Model explainability"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    services_status = {
        "model_service": model_service is not None and model_service.is_ready(),
        "agent_service": agent_service is not None and agent_service.is_ready(),
        "rag_service": rag_service is not None and rag_service.is_ready()
    }
    
    overall_status = "healthy" if all(services_status.values()) else "degraded"
    
    return {
        "status": overall_status,
        "services": services_status
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )