"""
Confidence Estimation Agent - Estimates prediction confidence and uncertainty
"""

import asyncio
import logging
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
from base_agents.base_agent import BaseAgent


class ConfidenceEstimationAgent(BaseAgent):
    """
    Agent specialized in confidence estimation and uncertainty quantification.
    
    Capabilities:
    - Prediction confidence scoring
    - Uncertainty quantification
    - Reliability assessment
    - Confidence interval calculation
    """
    
    def __init__(self):
        super().__init__(
            agent_id="confidence_estimation_agent",
            name="Confidence Estimation Agent",
            description="Estimates prediction confidence and uncertainty with AI-powered analysis"
        )
        
        # Model selection: Claude Opus for sophisticated uncertainty quantification
        self.model_preference = "claude-opus"
        self.model_reasoning = "Sophisticated uncertainty quantification and confidence estimation required"

    def _initialize_capabilities(self):
        self.add_capability("confidence_scoring")
        self.add_capability("uncertainty_quantification")
        self.add_capability("reliability_assessment")
        self.add_capability("confidence_interval_calculation")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for confidence estimation."""
        return "prediction" in input_data or "model_output" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate confidence for predictions.
        
        Args:
            input_data: Contains prediction and model information
            
        Returns:
            Dict with confidence estimation results
        """
        prediction = input_data.get("prediction") or input_data.get("model_output", {})
        model_info = input_data.get("model_info", {})
        input_features = input_data.get("input_features", {})
        
        self.logger.info("Estimating prediction confidence")
        
        # Calculate confidence score
        confidence_score = await self._calculate_confidence_score(prediction, model_info, input_features)
        
        # Quantify uncertainty
        uncertainty = await self._quantify_uncertainty(prediction, model_info)
        
        # Assess reliability
        reliability = await self._assess_reliability(prediction, model_info, input_features)
        
        # Calculate confidence intervals
        confidence_intervals = await self._calculate_confidence_intervals(prediction)
        
        return {
            "confidence_score": confidence_score,
            "uncertainty": uncertainty,
            "reliability": reliability,
            "confidence_intervals": confidence_intervals,
            "analysis_metadata": {
                "analysis_time": datetime.now().isoformat(),
                "model_used": self.model_preference
            }
        }
    
    async def _calculate_confidence_score(self, prediction: Dict[str, Any], 
                                         model_info: Dict[str, Any], 
                                         input_features: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate confidence score for prediction."""
        base_confidence = 0.7
        
        # Adjust based on prediction probability
        if "probability" in prediction:
            prob = prediction["probability"]
            if prob > 0.9 or prob < 0.1:
                base_confidence += 0.2
            elif prob > 0.7 or prob < 0.3:
                base_confidence += 0.1
        
        # Adjust based on data quality
        data_quality = input_features.get("data_quality_score", 0.5)
        base_confidence *= (0.5 + data_quality)
        
        # Adjust based on model performance
        model_accuracy = model_info.get("accuracy", 0.8)
        base_confidence *= model_accuracy
        
        return {
            "confidence_score": round(min(base_confidence, 1.0), 3),
            "confidence_level": "high" if base_confidence >= 0.8 else 
                               "moderate" if base_confidence >= 0.6 else "low",
            "factors": {
                "prediction_probability": prediction.get("probability", "N/A"),
                "data_quality": data_quality,
                "model_accuracy": model_accuracy
            }
        }
    
    async def _quantify_uncertainty(self, prediction: Dict[str, Any], 
                                   model_info: Dict[str, Any]) -> Dict[str, Any]:
        """Quantify prediction uncertainty."""
        # Simplified uncertainty quantification
        epistemic_uncertainty = 1.0 - model_info.get("accuracy", 0.8)
        aleatoric_uncertainty = 0.1  # Base data uncertainty
        
        total_uncertainty = epistemic_uncertainty + aleatoric_uncertainty
        
        return {
            "epistemic_uncertainty": round(epistemic_uncertainty, 3),
            "aleatoric_uncertainty": round(aleatoric_uncertainty, 3),
            "total_uncertainty": round(min(total_uncertainty, 1.0), 3),
            "uncertainty_sources": [
                "Model knowledge gaps",
                "Data noise",
                "Feature uncertainty"
            ]
        }
    
    async def _assess_reliability(self, prediction: Dict[str, Any], 
                                 model_info: Dict[str, Any],
                                 input_features: Dict[str, Any]) -> Dict[str, Any]:
        """Assess prediction reliability."""
        reliability_score = 0.7
        
        # Check for missing data
        missing_data_ratio = input_features.get("missing_data_ratio", 0.0)
        reliability_score -= missing_data_ratio * 0.5
        
        # Check for outliers
        outlier_count = input_features.get("outlier_count", 0)
        reliability_score -= outlier_count * 0.1
        
        # Check model calibration
        model_calibration = model_info.get("calibration_score", 0.8)
        reliability_score *= model_calibration
        
        return {
            "reliability_score": round(max(reliability_score, 0.0), 3),
            "reliability_level": "high" if reliability_score >= 0.8 else 
                                "moderate" if reliability_score >= 0.6 else "low",
            "concerns": [
                "High missing data ratio" if missing_data_ratio > 0.3 else None,
                "Multiple outliers detected" if outlier_count > 5 else None,
                "Poor model calibration" if model_calibration < 0.7 else None
            ]
        }
    
    async def _calculate_confidence_intervals(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate confidence intervals for predictions."""
        predicted_value = prediction.get("probability", prediction.get("value", 0.5))
        
        # Calculate 95% confidence interval
        std_error = 0.1  # Simplified standard error
        ci_lower = max(0.0, predicted_value - 1.96 * std_error)
        ci_upper = min(1.0, predicted_value + 1.96 * std_error)
        
        return {
            "predicted_value": predicted_value,
            "confidence_interval_95": {
                "lower": round(ci_lower, 3),
                "upper": round(ci_upper, 3)
            },
            "confidence_interval_90": {
                "lower": round(max(0.0, predicted_value - 1.645 * std_error), 3),
                "upper": round(min(1.0, predicted_value + 1.645 * std_error), 3)
            },
            "interval_width": round(ci_upper - ci_lower, 3)
        }