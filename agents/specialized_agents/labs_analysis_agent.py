"""
Labs Analysis Agent - Analyzes laboratory values with AI-powered insights
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from base_agents.base_agent import BaseAgent


class LabsAnalysisAgent(BaseAgent):
    """
    Agent specialized in laboratory value analysis.
    
    Capabilities:
    - Abnormal lab value detection
    - Trend analysis
    - Critical value identification
    - Lab-clinical correlation
    """
    
    def __init__(self):
        super().__init__(
            agent_id="labs_analysis_agent",
            name="Labs Analysis Agent",
            description="Analyzes laboratory values with AI-powered insights"
        )
        
        # Reference ranges for common labs
        self.reference_ranges = {
            "wbc": {"normal": (4.5, 11.0), "unit": "K/uL", "critical": (0.5, 50.0)},
            "hemoglobin": {"normal": (12.0, 16.0), "unit": "g/dL", "critical": (5.0, 20.0)},
            "platelets": {"normal": (150, 450), "unit": "K/uL", "critical": (10, 1000)},
            "sodium": {"normal": (135, 145), "unit": "mEq/L", "critical": (115, 160)},
            "potassium": {"normal": (3.5, 5.0), "unit": "mEq/L", "critical": (2.5, 6.5)},
            "creatinine": {"normal": (0.6, 1.2), "unit": "mg/dL", "critical": (0.1, 10.0)},
            "bun": {"normal": (7, 20), "unit": "mg/dL", "critical": (1, 100)},
            "glucose": {"normal": (70, 100), "unit": "mg/dL", "critical": (40, 600)},
            "lactate": {"normal": (0.5, 2.0), "unit": "mmol/L", "critical": (0.1, 10.0)},
            "ph": {"normal": (7.35, 7.45), "unit": "", "critical": (6.8, 7.8)},
            "pco2": {"normal": (35, 45), "unit": "mmHg", "critical": (10, 80)},
            "po2": {"normal": (80, 100), "unit": "mmHg", "critical": (40, 200)}
        }
        
        # Model selection: GLM for efficient numerical analysis
        self.model_preference = "glm"
        self.model_reasoning = "Efficient processing of numerical laboratory data with pattern recognition"

    def _initialize_capabilities(self):
        self.add_capability("abnormal_detection")
        self.add_capability("trend_analysis")
        self.add_capability("critical_value_identification")
        self.add_capability("lab_clinical_correlation")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for labs analysis."""
        return "lab_values" in input_data or "labs" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze laboratory values and provide insights.
        
        Args:
            input_data: Contains laboratory values
            
        Returns:
            Dict with lab analysis results
        """
        lab_values = input_data.get("lab_values") or input_data.get("labs", {})
        
        self.logger.info(f"Analyzing {len(lab_values)} laboratory values")
        
        # Detect abnormal values
        abnormal_labs = await self._detect_abnormal_labs(lab_values)
        
        # Identify critical values
        critical_labs = await self._identify_critical_labs(lab_values)
        
        # Analyze trends if historical data available
        trend_analysis = await self._analyze_trends(lab_values)
        
        # Calculate lab severity score
        severity_score = await self._calculate_severity_score(lab_values)
        
        # Generate clinical correlations
        clinical_correlations = await self._generate_clinical_correlations(lab_values)
        
        return {
            "abnormal_labs": abnormal_labs,
            "critical_labs": critical_labs,
            "trend_analysis": trend_analysis,
            "severity_score": severity_score,
            "clinical_correlations": clinical_correlations,
            "analysis_metadata": {
                "labs_analyzed": len(lab_values),
                "analysis_time": datetime.now().isoformat(),
                "model_used": self.model_preference
            }
        }
    
    async def _detect_abnormal_labs(self, lab_values: Dict[str, float]) -> List[Dict[str, Any]]:
        """Detect laboratory values outside normal ranges."""
        abnormal = []
        
        for lab_name, value in lab_values.items():
            if lab_name.lower() in self.reference_ranges:
                ref = self.reference_ranges[lab_name.lower()]
                normal_min, normal_max = ref["normal"]
                
                if value < normal_min or value > normal_max:
                    severity = "mild"
                    if value < normal_min * 0.5 or value > normal_max * 1.5:
                        severity = "moderate"
                    if value < normal_min * 0.25 or value > normal_max * 2.0:
                        severity = "severe"
                    
                    abnormal.append({
                        "lab": lab_name,
                        "value": value,
                        "normal_range": ref["normal"],
                        "unit": ref["unit"],
                        "severity": severity,
                        "deviation_percent": abs((value - ((normal_min + normal_max) / 2)) / 
                                                   ((normal_max - normal_min) / 2)) * 100
                    })
        
        return abnormal
    
    async def _identify_critical_labs(self, lab_values: Dict[str, float]) -> List[Dict[str, Any]]:
        """Identify critically abnormal laboratory values."""
        critical = []
        
        for lab_name, value in lab_values.items():
            if lab_name.lower() in self.reference_ranges:
                ref = self.reference_ranges[lab_name.lower()]
                if "critical" in ref:
                    critical_min, critical_max = ref["critical"]
                    
                    if value < critical_min or value > critical_max:
                        critical.append({
                            "lab": lab_name,
                            "value": value,
                            "critical_range": ref["critical"],
                            "unit": ref["unit"],
                            "urgency": "immediate"
                        })
        
        return critical
    
    async def _analyze_trends(self, lab_values: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze laboratory value trends if historical data available."""
        trends = {}
        
        # Check for historical data
        if "historical_labs" in lab_values or any(isinstance(v, list) for v in lab_values.values()):
            # Simplified trend analysis
            for lab_name, value in lab_values.items():
                if isinstance(value, list) and len(value) > 1:
                    # Calculate trend
                    if len(value) >= 3:
                        recent_trend = value[-1] - value[-2]
                        overall_trend = value[-1] - value[0]
                        
                        trend_direction = "stable"
                        if abs(recent_trend) > 0.1 * (max(value) - min(value)):
                            trend_direction = "increasing" if recent_trend > 0 else "decreasing"
                        
                        trends[lab_name] = {
                            "direction": trend_direction,
                            "recent_change": recent_trend,
                            "overall_change": overall_trend,
                            "rate_of_change": overall_change_rate if len(value) > 2 else 0
                        }
        
        return trends
    
    async def _calculate_severity_score(self, lab_values: Dict[str, float]) -> float:
        """Calculate overall laboratory severity score."""
        severity_score = 0.0
        lab_count = 0
        
        for lab_name, value in lab_values.items():
            if lab_name.lower() in self.reference_ranges:
                ref = self.reference_ranges[lab_name.lower()]
                normal_min, normal_max = ref["normal"]
                
                # Calculate deviation from normal
                if value < normal_min:
                    deviation = (normal_min - value) / normal_min
                elif value > normal_max:
                    deviation = (value - normal_max) / normal_max
                else:
                    deviation = 0
                
                severity_score += min(deviation, 2.0)  # Cap at 2.0 per lab
                lab_count += 1
        
        return round(severity_score / max(lab_count, 1), 2)
    
    async def _generate_clinical_correlations(self, lab_values: Dict[str, float]) -> List[str]:
        """Generate clinical correlations based on lab patterns."""
        correlations = []
        
        # Check for specific patterns
        if "creatinine" in lab_values and "bun" in lab_values:
            bun_creatinine_ratio = lab_values["bun"] / lab_values["creatinine"]
            if bun_creatinine_ratio > 20:
                correlations.append("Elevated BUN/Cr ratio suggests prerenal azotemia")
            elif bun_creatinine_ratio < 10:
                correlations.append("Low BUN/Cr ratio suggests intrinsic renal damage")
        
        if "lactate" in lab_values and lab_values["lactate"] > 2.0:
            correlations.append(f"Elevated lactate ({lab_values['lactate']} mmol/L) indicates tissue hypoxia")
        
        if "wbc" in lab_values:
            if lab_values["wbc"] < 4.5:
                correlations.append("Leukopenia may indicate immunosuppression or sepsis")
            elif lab_values["wbc"] > 11.0:
                correlations.append("Leukocytosis suggests infection or inflammation")
        
        if "platelets" in lab_values and lab_values["platelets"] < 150:
            correlations.append("Thrombocytopenia - consider DIC, sepsis, or bone marrow suppression")
        
        return correlations