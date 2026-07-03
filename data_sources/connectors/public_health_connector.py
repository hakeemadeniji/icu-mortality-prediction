"""
Public Health Data Connector
Accesses WHO, CDC, and other public health mortality datasets
"""

import logging
import requests
import pandas as pd
from typing import Dict, Any, List, Optional
from pathlib import Path
import io


class PublicHealthConnector:
    """
    Connector for public health mortality data.
    
    Provides access to:
    - WHO Mortality Database
    - CDC Public-Use Linked Mortality Files
    - WHO Global Health Observatory data
    """
    
    def __init__(self, cache_dir: str = "./data_sources/cache"):
        self.logger = logging.getLogger("public_health_connector")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Public health data sources
        self.sources = {
            "who_mortality": {
                "name": "WHO Mortality Database",
                "url": "https://www.who.int/data/data-collection-tools/who-mortality-database",
                "access_type": "public",
                "description": "Global mortality data reported by Member States"
            },
            "cdc_linked_mortality": {
                "name": "CDC Public-Use Linked Mortality Files",
                "url": "https://data.cdc.gov/National-Center-for-Health-Statistics/Public-Use-Linked-Mortality-Files/r9nv-zxge",
                "access_type": "public",
                "description": "US mortality data linked to survey data"
            },
            "who_gho": {
                "name": "WHO Global Health Observatory",
                "url": "https://www.who.int/data/gho",
                "access_type": "public_api",
                "description": "WHO health statistics and mortality estimates"
            }
        }
    
    def list_available_sources(self) -> List[Dict[str, Any]]:
        """List all available public health data sources."""
        return [
            {
                "source_id": key,
                **value
            }
            for key, value in self.sources.items()
        ]
    
    async def fetch_who_mortality_data(self, 
                                      countries: Optional[List[str]] = None,
                                      years: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Fetch WHO mortality data.
        
        Args:
            countries: List of country codes (optional)
            years: List of years (optional)
            
        Returns:
            Dictionary with mortality data
        """
        try:
            self.logger.info("Fetching WHO mortality data")
            
            # WHO Mortality Database requires manual download
            # This is a placeholder for the actual implementation
            
            return {
                "status": "requires_manual_download",
                "source": "who_mortality",
                "message": "WHO Mortality Database requires manual download from WHO website",
                "url": self.sources["who_mortality"]["url"],
                "instructions": "Download from WHO website and provide local path",
                "data_structure": {
                    "format": "CSV",
                    "includes": ["Deaths by cause", "Age groups", "Sex", "Year", "Country"],
                    "size": "Large (millions of records)"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching WHO mortality data: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def fetch_cdc_mortality_data(self, 
                                       dataset: str = "nhps") -> Dict[str, Any]:
        """
        Fetch CDC mortality data.
        
        Args:
            dataset: Specific CDC dataset identifier
            
        Returns:
            Dictionary with mortality data
        """
        try:
            self.logger.info(f"Fetching CDC mortality data for dataset: {dataset}")
            
            # CDC data is available through Socrata API
            base_url = "https://data.cdc.gov/resource/r9nv-zxge.json"
            
            # Try to fetch sample data
            response = requests.get(f"{base_url}?$limit=5", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "source": "cdc_linked_mortality",
                    "sample_data": data,
                    "total_available": "Large dataset - requires API queries",
                    "access_method": "Socrata API",
                    "documentation": self.sources["cdc_linked_mortality"]["url"]
                }
            else:
                return {
                    "status": "api_error",
                    "message": f"API returned status {response.status_code}",
                    "documentation": self.sources["cdc_linked_mortality"]["url"]
                }
            
        except Exception as e:
            self.logger.error(f"Error fetching CDC mortality data: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def fetch_who_gho_data(self, 
                                indicator: str = "Mortality") -> Dict[str, Any]:
        """
        Fetch WHO Global Health Observatory data.
        
        Args:
            indicator: Health indicator to fetch
            
        Returns:
            Dictionary with GHO data
        """
        try:
            self.logger.info(f"Fetching WHO GHO data for indicator: {indicator}")
            
            # WHO GHO provides OData API
            base_url = "https://ghoapi.azureedge.net/api"
            
            # Fetch indicators
            indicators_response = requests.get(f"{base_url}/Indicator", timeout=30)
            
            if indicators_response.status_code == 200:
                indicators = indicators_response.json()
                mortality_indicators = [
                    ind for ind in indicators.get('value', [])
                    if 'mortality' in ind.get('IndicatorName', '').lower()
                ]
                
                return {
                    "status": "success",
                    "source": "who_gho",
                    "indicator": indicator,
                    "available_indicators": mortality_indicators[:10],  # First 10
                    "api_endpoint": base_url,
                    "documentation": self.sources["who_gho"]["url"]
                }
            else:
                return {
                    "status": "api_error",
                    "message": f"API returned status {indicators_response.status_code}"
                }
            
        except Exception as e:
            self.logger.error(f"Error fetching WHO GHO data: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def load_local_mortality_data(self, 
                                       file_path: str) -> Dict[str, Any]:
        """
        Load locally stored mortality data file.
        
        Args:
            file_path: Path to local data file
            
        Returns:
            Dictionary with loaded data
        """
        try:
            self.logger.info(f"Loading local mortality data from {file_path}")
            
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Determine file type and load accordingly
            if file_path.suffix == '.csv':
                data = pd.read_csv(file_path)
            elif file_path.suffix in ['.xlsx', '.xls']:
                data = pd.read_excel(file_path)
            elif file_path.suffix == '.json':
                data = pd.read_json(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
            
            return {
                "status": "success",
                "file_path": str(file_path),
                "rows": len(data),
                "columns": list(data.columns),
                "sample_data": data.head().to_dict(),
                "data_types": data.dtypes.astype(str).to_dict()
            }
            
        except Exception as e:
            self.logger.error(f"Error loading local data: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_mortality_statistics(self, 
                                      region: str = "global") -> Dict[str, Any]:
        """
        Get general mortality statistics.
        
        Args:
            region: Geographic region
            
        Returns:
            Dictionary with mortality statistics
        """
        try:
            self.logger.info(f"Fetching mortality statistics for region: {region}")
            
            # This would aggregate data from various sources
            # For now, return placeholder statistics
            
            stats = {
                "region": region,
                "leading_causes": [
                    "Ischaemic heart disease",
                    "Stroke",
                    "Chronic obstructive pulmonary disease",
                    "Lower respiratory infections",
                    "Neonatal conditions"
                ],
                "icu_specific_factors": [
                    "Sepsis",
                    "Respiratory failure",
                    "Cardiovascular events",
                    "Multi-organ failure"
                ],
                "data_sources": [
                    "WHO Mortality Database",
                    "CDC Wonder Database",
                    "Global Burden of Disease Study"
                ]
            }
            
            return {
                "status": "success",
                "statistics": stats
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching mortality statistics: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_source_info(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific data source."""
        return self.sources.get(source_id)