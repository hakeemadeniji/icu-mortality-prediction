"""
Data API endpoints for data source management and ingestion
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class DataSourceInfo(BaseModel):
    """Data source information model."""
    
    source_id: str = Field(..., description="Data source identifier")
    name: str = Field(..., description="Data source name")
    type: str = Field(..., description="Data source type")
    description: str = Field(..., description="Data source description")
    status: str = Field(..., description="Connection status")
    last_updated: Optional[str] = Field(None, description="Last update timestamp")
    record_count: Optional[int] = Field(None, description="Total record count")
    enabled: bool = Field(..., description="Whether source is enabled")


class DataIngestionRequest(BaseModel):
    """Data ingestion request model."""
    
    source_id: str = Field(..., description="Data source to ingest from")
    batch_size: Optional[int] = Field(1000, description="Batch size for ingestion")
    transform: Optional[bool] = Field(True, description="Apply transformations")
    validate: Optional[bool] = Field(True, description="Validate data")


class DataIngestionResponse(BaseModel):
    """Data ingestion response model."""
    
    source_id: str = Field(..., description="Data source ID")
    status: str = Field(..., description="Ingestion status")
    records_processed: int = Field(..., description="Number of records processed")
    records_failed: int = Field(..., description="Number of failed records")
    processing_time: float = Field(..., description="Processing time in seconds")
    errors: List[str] = Field(default_factory=list, description="Error messages")


class DataQueryRequest(BaseModel):
    """Data query request model."""
    
    query: str = Field(..., description="SQL or natural language query")
    sources: Optional[List[str]] = Field(None, description="Specific data sources")
    limit: Optional[int] = Field(100, description="Result limit")
    filters: Optional[Dict[str, Any]] = Field(None, description="Query filters")


class DataQueryResponse(BaseModel):
    """Data query response model."""
    
    query: str = Field(..., description="Executed query")
    results: List[Dict[str, Any]] = Field(..., description="Query results")
    result_count: int = Field(..., description="Number of results")
    execution_time: float = Field(..., description="Query execution time")
    sources_queried: List[str] = Field(..., description="Data sources used")


@router.get("/sources", response_model=List[DataSourceInfo])
async def list_data_sources():
    """List all available data sources."""
    try:
        from services.data_service import DataService
        
        data_service = DataService()
        sources = await data_service.list_sources()
        return sources
        
    except Exception as e:
        logger.error(f"Error listing data sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources/{source_id}", response_model=DataSourceInfo)
async def get_data_source(source_id: str):
    """Get detailed information about a specific data source."""
    try:
        from services.data_service import DataService
        
        data_service = DataService()
        source = await data_service.get_source(source_id)
        if not source:
            raise HTTPException(status_code=404, detail=f"Data source {source_id} not found")
        
        return source
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting data source {source_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest", response_model=DataIngestionResponse)
async def ingest_data(request: DataIngestionRequest):
    """
    Ingest data from a specific source.
    
    Supports batch ingestion with transformation and validation.
    """
    try:
        from services.data_service import DataService
        
        data_service = DataService()
        result = await data_service.ingest_data(
            request.source_id,
            request.batch_size,
            request.transform,
            request.validate
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error ingesting data from {request.source_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=DataQueryResponse)
async def query_data(request: DataQueryRequest):
    """
    Query data across multiple sources.
    
    Supports both SQL and natural language queries.
    """
    try:
        from services.data_service import DataService
        
        data_service = DataService()
        result = await data_service.query_data(
            request.query,
            request.sources,
            request.limit,
            request.filters
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error querying data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_data(file: UploadFile = File(...)):
    """
    Upload custom data file.
    
    Supports CSV, JSON, and Parquet formats.
    """
    try:
        from services.data_service import DataService
        
        data_service = DataService()
        result = await data_service.upload_file(file)
        
        return {
            "status": "uploaded",
            "file_id": result["file_id"],
            "filename": file.filename,
            "record_count": result.get("record_count", 0)
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sources/{source_id}/enable")
async def enable_data_source(source_id: str):
    """Enable a data source."""
    try:
        from services.data_service import DataService
        
        data_service = DataService()
        success = await data_service.enable_source(source_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Data source {source_id} not found")
        
        return {"status": "enabled", "source_id": source_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling data source {source_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sources/{source_id}/disable")
async def disable_data_source(source_id: str):
    """Disable a data source."""
    try:
        from services.data_service import DataService
        
        data_service = DataService()
        success = await data_service.disable_source(source_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Data source {source_id} not found")
        
        return {"status": "disabled", "source_id": source_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling data source {source_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_data_statistics():
    """Get overall data statistics across all sources."""
    try:
        from services.data_service import DataService
        
        data_service = DataService()
        stats = await data_service.get_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting data statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))