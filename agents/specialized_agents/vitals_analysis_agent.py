"""
Vitals Analysis Agent - Specialized in vital sign patterns
"""

import asyncio
import logging
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
from base_agents.base_agent import BaseAgent


class VitalsAnalysisAgent(BaseAgent):
    """
    Agent specialized in analyzing vital sign patterns.
    
    Capabilities:
    - Trend analysis
    - Anomaly detection
    - Critical threshold monitoring
    - Temporal pattern recognition
    """
    
    def __init__(self):
        super().__init__(
            agent_id="vitals_analysis_agent",
            name="Vitals Analysis Agent",
            description="Analyzes vital sign patterns and trends"
        )
        
        # Normal vital sign ranges
        self.normal_ranges = {
            "heart_rate": (60, 100),
            "systolic_bp": (90, 140),
            "diastolic_bp": (60, 90),
            "mean_bp": (70, 110),
            "respiratory_rate": (12, 20),
            "temperature": (36.1, 37.2),
            "spo2": (95, 100)
        }
        
    def _initialize_capabilities(self):
        self.add_capability("trend_analysis")
        self.add_capability("anomaly_detection")
        self.add_capability("threshold_monitoring")
        self.add_capability("temporal_patterns")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for vitals analysis."""
        return "vital_signs" in input_data or "timeseries_data" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze vital signs and detect patterns.
        
        Args:
            input_data: Contains vital signs time-series data
            
        Returns:
            Dict with vital signs analysis and alerts
        """
        vital_signs = input_data.get("vital_signs", [])
        
        self.logger.info(f"Analyzing {len(vital_signs)} vital sign readings")
        
        # Analyze trends
        trends = await self._analyze_trends(vital_signs)
        
        # Detect anomalies
        anomalies = await self._detect_anomalies(vital_signs)
        
        # Check critical thresholds
        threshold_alerts = await self._check_thresholds(vital_signs)
        
        # Analyze temporal patterns
        temporal_patterns = await self._analyze_temporal_patterns(vital_signs)
        
        # Calculate overall vital score
        vital_score = await self._calculate_vital_score(vital_signs, anomalies, threshold_alerts)
        
        return {
            "trends": trends,
            "anomalies": anomalies,
            "threshold_alerts": threshold_alerts,
            "temporal_patterns": temporal_patterns,
            "vital_score": vital_score,
            "analysis_metadata": {
                "readings_analyzed": len(vital_signs),
                "analysis_time": datetime.now().isoformat()
            }
        }
    
    async def _analyze_trends(self, vital_signs: List[Dict[str, float]]) -> Dict[str, str]:
        """Analyze trends in vital signs."""
        trends = {}
        
        if not vital_signs:
            return trends
        
        for vital in self.normal_ranges.keys():
            if vital in vital_signs[0]:
                values = [reading.get(vital, 0) for reading in vital_signs if vital in reading]
                
                if len(values) > 1:
                    # Calculate trend
                    if values[-1] > values[0]:
                        trend = "increasing"
                    elif values[-1] < values[0]:
                        trend = "decreasing"
                    else:
                        trend = "stable"
                    
                    # Calculate rate of change
                    rate = (values[-1] - values[0]) / len(values)
                    trends[vital] = {
                        "direction": trend,
                        "rate_of_change": rate,
                        "start_value": values[0],
                        "end_value": values[-1]
                    }
        
        return trends
    
    async def _detect_anomalies(self, vital_signs: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """Detect anomalies in vital signs."""
        anomalies = []
        
        if not vital_signs:
            return anomalies
        
        for i, reading in enumerate(vital_signs):
            for vital, (min_normal, max_normal) in self.normal_ranges.items():
                if vital in reading:
                    value = reading[vital]
                    
                    # Check for abnormal values
                    if value < min_normal * 0.5 or value > max_normal * 1.5:
                        anomalies.append({
                            "timestamp": i,
                            "vital": vital,
                            "value": value,
                            "normal_range": (min_normal, max_normal),
                            "severity": "critical" if value < min_normal * 0.3 or value > max_normal * 2.0 else "warning"
                        })
        
        return anomalies
    
    async def _check_thresholds(self, vital_signs: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """Check critical thresholds."""
        alerts = []
        
        critical_thresholds = {
            "heart_rate": (40, 150),
            "systolic_bp": (70, 180),
            "spo2": (85, None),
            "temperature": (35.0, 40.0)
        }
        
        if not vital_signs:
            return alerts
        
        latest_reading = vital_signs[-1] if vital_signs else {}
        
        for vital, (min_crit, max_crit) in critical_thresholds.items():
            if vital in latest_reading:
                value = latest_reading[vital]
                
                if min_crit is not None and value < min_crit:
                    alerts.append({
                        "vital": vital,
                        "value": value,
                        "threshold": min_crit,
                        "type": "below_critical",
                        "message": f"{vital} critically low: {value}"
                    })
                elif max_crit is not None and value > max_crit:
                    alerts.append({
                        "vital": vital,
                        "value": value,
                        "threshold": max_crit,
                        "type": "above_critical",
                        "message": f"{vital} critically high: {value}"
                    })
        
        return alerts
    
    async def _analyze_temporal_patterns(self, vital_signs: List[Dict[str, float]]) -> Dict[str, Any]:
        """Analyze temporal patterns in vital signs."""
        patterns = {
            "variability": {},
            "periodicity": {},
            "stability": {}
        }
        
        if not vital_signs:
            return patterns
        
        for vital in self.normal_ranges.keys():
            if vital in vital_signs[0]:
                values = [reading.get(vital, 0) for reading in vital_signs if vital in reading]
                
                if len(values) > 2:
                    # Calculate variability (standard deviation)
                    variability = np.std(values)
                    patterns["variability"][vital] = variability
                    
                    # Calculate stability (coefficient of variation)
                    mean_val = np.mean(values)
                    stability = 1.0 - (variability / mean_val) if mean_val > 0 else 0.0
                    patterns["stability"][vital] = max(0.0, min(1.0, stability))
        
        return patterns
    
    async def _calculate_vital_score(self, vital_signs: List[Dict[str, float]], 
                                     anomalies: List[Dict[str, Any]], 
                                     alerts: List[Dict[str, Any]]) -> float:
        """Calculate overall vital score (0-1, higher is better)."""
        if not vital_signs:
            return 0.5
        
        # Base score
        score = 1.0
        
        # Penalize anomalies
        score -= len(anomalies) * 0.1
        
        # Penalize critical alerts more heavily
        score -= len(alerts) * 0.2
        
        return max(0.0, min(1.0, score))