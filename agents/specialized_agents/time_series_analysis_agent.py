"""
Time Series Analysis Agent - Analyzes temporal patterns in clinical data
"""

import asyncio
import logging
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
from base_agents.base_agent import BaseAgent


class TimeSeriesAnalysisAgent(BaseAgent):
    """
    Agent specialized in time series analysis of clinical data.
    
    Capabilities:
    - Temporal pattern recognition
    - Trend analysis
    - Anomaly detection in time series
    - Forecasting and prediction
    """
    
    def __init__(self):
        super().__init__(
            agent_id="time_series_analysis_agent",
            name="Time Series Analysis Agent",
            description="Analyzes temporal patterns in clinical data with AI-powered analysis"
        )
        
        # Time series patterns
        self.pattern_types = [
            "trending_up", "trending_down", "stable", "cyclical",
            "volatile", "step_change", "intermittent"
        ]
        
        # Anomaly thresholds
        self.anomaly_thresholds = {
            "statistical": 2.0,  # Standard deviations
            "rate_of_change": 0.5,  # 50% change
            "persistence": 3  # Consecutive anomalous points
        }
        
        # Model selection: GLM for efficient time series analysis
        self.model_preference = "glm"
        self.model_reasoning = "Efficient temporal analysis and pattern recognition"

    def _initialize_capabilities(self):
        self.add_capability("temporal_pattern_recognition")
        self.add_capability("trend_analysis")
        self.add_capability("anomaly_detection")
        self.add_capability("time_series_forecasting")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for time series analysis."""
        return "time_series" in input_data or "temporal_data" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze time series data.
        
        Args:
            input_data: Contains time series data
            
        Returns:
            Dict with time series analysis results
        """
        time_series = input_data.get("time_series") or input_data.get("temporal_data", {})
        config = input_data.get("config", {})
        
        self.logger.info(f"Analyzing time series for {len(time_series)} parameters")
        
        # Recognize temporal patterns
        patterns = await self._recognize_patterns(time_series)
        
        # Analyze trends
        trends = await self._analyze_trends(time_series)
        
        # Detect anomalies
        anomalies = await self._detect_anomalies(time_series)
        
        # Generate forecasts
        forecasts = await self._generate_forecasts(time_series, config)
        
        return {
            "temporal_patterns": patterns,
            "trend_analysis": trends,
            "anomaly_detection": anomalies,
            "forecasts": forecasts,
            "analysis_metadata": {
                "parameters_analyzed": len(time_series),
                "analysis_time": datetime.now().isoformat(),
                "model_used": self.model_preference
            }
        }
    
    async def _recognize_patterns(self, time_series: Dict[str, List[float]]) -> Dict[str, Any]:
        """Recognize temporal patterns in time series data."""
        pattern_results = {}
        
        for param_name, values in time_series.items():
            if not isinstance(values, list) or len(values) < 3:
                continue
            
            pattern = await self._classify_pattern(values)
            
            pattern_results[param_name] = {
                "pattern": pattern,
                "confidence": await self._calculate_pattern_confidence(values, pattern),
                "description": self._get_pattern_description(pattern)
            }
        
        return pattern_results
    
    async def _classify_pattern(self, values: List[float]) -> str:
        """Classify the pattern of a time series."""
        if len(values) < 3:
            return "insufficient_data"
        
        # Calculate basic statistics
        values_array = np.array(values)
        mean_val = np.mean(values_array)
        std_val = np.std(values_array)
        
        # Calculate trend
        if len(values) >= 2:
            x = np.arange(len(values))
            slope, _ = np.polyfit(x, values_array, 1)
            
            # Determine trend direction
            if abs(slope) < std_val * 0.1:
                trend = "stable"
            elif slope > 0:
                trend = "trending_up"
            else:
                trend = "trending_down"
        else:
            trend = "stable"
        
        # Check for volatility
        if std_val > abs(mean_val) * 0.3:
            volatility = "volatile"
        else:
            volatility = "stable"
        
        # Combine classifications
        if volatility == "volatile":
            if trend == "stable":
                return "volatile"
            else:
                return "volatile_with_trend"
        else:
            return trend
    
    async def _calculate_pattern_confidence(self, values: List[float], pattern: str) -> float:
        """Calculate confidence in pattern classification."""
        if len(values) < 3:
            return 0.0
        
        # Simple confidence based on data length and consistency
        length_factor = min(len(values) / 10, 1.0)  # More data = higher confidence
        consistency_factor = 0.8  # Simplified
        
        return round(length_factor * consistency_factor, 2)
    
    def _get_pattern_description(self, pattern: str) -> str:
        """Get description for pattern type."""
        descriptions = {
            "trending_up": "Consistent upward trend over time",
            "trending_down": "Consistent downward trend over time",
            "stable": "Relatively stable values over time",
            "volatile": "High variability with no clear trend",
            "volatile_with_trend": "High variability with directional trend",
            "insufficient_data": "Insufficient data for pattern recognition"
        }
        return descriptions.get(pattern, "Unknown pattern")
    
    async def _analyze_trends(self, time_series: Dict[str, List[float]]) -> Dict[str, Any]:
        """Analyze trends in time series data."""
        trend_results = {}
        
        for param_name, values in time_series.items():
            if not isinstance(values, list) or len(values) < 2:
                continue
            
            values_array = np.array(values)
            x = np.arange(len(values))
            
            # Linear regression for trend
            slope, intercept = np.polyfit(x, values_array, 1)
            
            # Calculate R-squared
            y_pred = slope * x + intercept
            ss_res = np.sum((values_array - y_pred) ** 2)
            ss_tot = np.sum((values_array - np.mean(values_array)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            # Calculate rate of change
            if len(values) >= 2:
                rate_of_change = (values[-1] - values[0]) / len(values)
            else:
                rate_of_change = 0
            
            trend_results[param_name] = {
                "slope": round(slope, 4),
                "intercept": round(intercept, 4),
                "r_squared": round(r_squared, 3),
                "rate_of_change": round(rate_of_change, 4),
                "trend_strength": "strong" if r_squared > 0.7 else 
                                 "moderate" if r_squared > 0.4 else "weak",
                "direction": "increasing" if slope > 0 else 
                            "decreasing" if slope < 0 else "stable"
            }
        
        return trend_results
    
    async def _detect_anomalies(self, time_series: Dict[str, List[float]]) -> Dict[str, Any]:
        """Detect anomalies in time series data."""
        anomaly_results = {}
        
        for param_name, values in time_series.items():
            if not isinstance(values, list) or len(values) < 3:
                continue
            
            values_array = np.array(values)
            mean_val = np.mean(values_array)
            std_val = np.std(values_array)
            
            anomalies = []
            
            # Statistical anomalies (z-score)
            if std_val > 0:
                z_scores = np.abs((values_array - mean_val) / std_val)
                for i, z_score in enumerate(z_scores):
                    if z_score > self.anomaly_thresholds["statistical"]:
                        anomalies.append({
                            "index": i,
                            "value": values[i],
                            "z_score": round(z_score, 2),
                            "type": "statistical"
                        })
            
            # Rate of change anomalies
            if len(values) >= 2:
                for i in range(1, len(values)):
                    if values[i-1] != 0:
                        rate_change = abs((values[i] - values[i-1]) / values[i-1])
                        if rate_change > self.anomaly_thresholds["rate_of_change"]:
                            anomalies.append({
                                "index": i,
                                "value": values[i],
                                "rate_change": round(rate_change, 3),
                                "type": "rate_of_change"
                            })
            
            anomaly_results[param_name] = {
                "anomaly_count": len(anomalies),
                "anomalies": anomalies,
                "anomaly_rate": round(len(anomalies) / len(values), 3) if values else 0
            }
        
        return anomaly_results
    
    async def _generate_forecasts(self, time_series: Dict[str, List[float]], 
                                 config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate simple forecasts for time series data."""
        forecast_results = {}
        forecast_horizon = config.get("forecast_horizon", 5)
        
        for param_name, values in time_series.items():
            if not isinstance(values, list) or len(values) < 3:
                continue
            
            values_array = np.array(values)
            
            # Simple linear extrapolation
            x = np.arange(len(values))
            slope, intercept = np.polyfit(x, values_array, 1)
            
            # Generate forecast
            forecast_x = np.arange(len(values), len(values) + forecast_horizon)
            forecast_values = slope * forecast_x + intercept
            
            # Calculate confidence intervals (simplified)
            forecast_std = np.std(values_array)
            confidence_upper = forecast_values + 1.96 * forecast_std
            confidence_lower = forecast_values - 1.96 * forecast_std
            
            forecast_results[param_name] = {
                "forecast_values": [round(val, 3) for val in forecast_values],
                "confidence_upper": [round(val, 3) for val in confidence_upper],
                "confidence_lower": [round(val, 3) for val in confidence_lower],
                "forecast_horizon": forecast_horizon,
                "method": "linear_extrapolation"
            }
        
        return forecast_results