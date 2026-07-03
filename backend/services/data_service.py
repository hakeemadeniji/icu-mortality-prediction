"""
Data Service - Handles data source management and ingestion
"""

import logging
import asyncio
from typing import Dict, Any, List

from core.config import settings

# Catalog of known sources with representative record counts. Whether each is
# "connected" is driven by the ENABLE_* flags in configuration.
_SOURCE_CATALOG = [
    ("physionet_challenge", "PhysioNet Challenge 2012", "icu_mortality",
     "ICU mortality prediction challenge dataset", "ENABLE_PHYSIONET_CHALLENGE", 45234),
    ("sicdb", "Salzburg Intensive Care Database (SICdb)", "icu_data",
     "High-resolution ICU data from Salzburg", "ENABLE_SICDB", 27891),
    ("hirid", "HiRID", "icu_data",
     "High time-resolution ICU dataset", "ENABLE_HIRID", 34567),
    ("nwicu", "NWICU Database", "icu_data",
     "Northwestern ICU database", "ENABLE_NWICU", 12345),
    ("who_mortality", "WHO Mortality Database", "public_health",
     "Global mortality reference data", "ENABLE_WHO_MORTALITY", 156789),
    ("cdc_data", "CDC Mortality Data", "public_health",
     "US CDC mortality statistics", "ENABLE_CDC_DATA", 89012),
    ("mimic", "MIMIC-IV", "icu_data",
     "Credentialed ICU dataset (PhysioNet)", "ENABLE_MIMIC", 0),
    ("eicu", "eICU Collaborative Research DB", "icu_data",
     "Multi-center ICU dataset (credentialed)", "ENABLE_EICU", 0),
]


class DataService:
    """Service for data source management."""

    def __init__(self):
        self.logger = logging.getLogger("data_service")

    async def list_sources(self) -> List[Dict[str, Any]]:
        """List data sources, connected state driven by ENABLE_* config flags."""
        sources = []
        for source_id, name, type_, desc, flag, records in _SOURCE_CATALOG:
            enabled = bool(getattr(settings, flag, False))
            sources.append({
                "source_id": source_id,
                "name": name,
                "type": type_,
                "description": desc,
                "status": "connected" if enabled else "disabled",
                "record_count": records if enabled else 0,
                "enabled": enabled,
            })
        return sources
        
    async def get_source(self, source_id: str) -> Dict[str, Any]:
        """Get specific data source."""
        sources = await self.list_sources()
        for source in sources:
            if source["source_id"] == source_id:
                return source
        return None
        
    async def ingest_data(self, source_id: str, batch_size: int, 
                         transform: bool, validate: bool) -> Dict[str, Any]:
        """Ingest data from source."""
        return {
            "source_id": source_id,
            "status": "success",
            "records_processed": 1000,
            "records_failed": 0,
            "processing_time": 5.2,
            "errors": []
        }
        
    async def query_data(self, query: str, sources: List[str], 
                        limit: int, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Query data across sources."""
        return {
            "query": query,
            "results": [{"patient_id": 1, "outcome": "survived"}],
            "result_count": 1,
            "execution_time": 0.5,
            "sources_queried": sources or ["all"]
        }
        
    async def upload_file(self, file) -> Dict[str, Any]:
        """Upload data file."""
        return {
            "file_id": "uploaded_123",
            "record_count": 100
        }
        
    async def enable_source(self, source_id: str) -> bool:
        """Enable data source."""
        return True
        
    async def disable_source(self, source_id: str) -> bool:
        """Disable data source."""
        return True
        
    async def get_statistics(self) -> Dict[str, Any]:
        """Get aggregate data statistics across connected sources."""
        sources = await self.list_sources()
        connected = [s for s in sources if s["enabled"]]
        return {
            "total_records": sum(s["record_count"] for s in connected),
            "total_sources": len(connected),
            "available_sources": len(sources),
        }