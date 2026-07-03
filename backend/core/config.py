"""
Configuration settings for ICU Mortality Prediction System
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8054
    DEBUG: bool = True
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3054", "http://localhost:8054"]
    
    # Database Settings
    DATABASE_URL: str = "sqlite:///./icu_mortality.db"
    VECTOR_DB_PATH: str = "./rag_system/vector_db/chroma"
    
    # Model Settings
    MODEL_PATH: str = "./onnx_models"
    ONNX_OPTIMIZED: bool = True
    ARM64_OPTIMIZED: bool = True
    USE_NPU: bool = True
    BATCH_SIZE: int = 32
    MAX_SEQUENCE_LENGTH: int = 48
    
    # Agent Settings
    NUM_AGENTS: int = 21
    AGENT_TIMEOUT: int = 300
    ENABLE_RAG: bool = True
    AGENT_PARALLEL_EXECUTION: bool = True
    MAX_CONCURRENT_AGENTS: int = 5
    
    # Anthropic API Settings for AI Agents
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL_DEFAULT: str = "claude-opus-4-8"
    ANTHROPIC_MODEL_FAST: str = "claude-haiku-4-5"
    ANTHROPIC_MAX_TOKENS: int = 4096
    ANTHROPIC_TEMPERATURE: float = 0.7
    
    # GLM Model Settings
    ENABLE_GLM: bool = False
    GLM_API_KEY: str = ""
    GLM_MODEL: str = "glm-4-plus"
    
    # RAG Settings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 5
    
    # Data Sources
    ENABLE_MIMIC: bool = False  # Requires credentialing
    ENABLE_EICU: bool = False  # Requires credentialing
    ENABLE_SICDB: bool = True  # Freely accessible
    ENABLE_NWICU: bool = True  # Freely accessible
    ENABLE_HIRID: bool = True  # Freely accessible
    ENABLE_PHYSIONET_CHALLENGE: bool = True  # Open access
    ENABLE_WHO_MORTALITY: bool = True  # Public data
    ENABLE_CDC_DATA: bool = True  # Public data
    
    # Evaluation Settings
    ENABLE_CONTINUOUS_EVAL: bool = True
    EVAL_INTERVAL_HOURS: int = 24
    DRIFT_THRESHOLD: float = 0.1
    
    # Monitoring Settings
    ENABLE_PROMETHEUS: bool = True
    PROMETHEUS_PORT: int = 9090
    ENABLE_GRAFANA: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # Frontend Configuration
    FRONTEND_URL: str = "http://localhost:3054"
    ENABLE_CORS: bool = True
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    MODELS_DIR: Path = BASE_DIR / "onnx_models"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Create necessary directories
settings.LOGS_DIR.mkdir(exist_ok=True)
settings.MODELS_DIR.mkdir(exist_ok=True)
settings.DATA_DIR.mkdir(exist_ok=True)