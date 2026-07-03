"""
Model Ensemble Agent - Orchestrates multiple model predictions
"""

import asyncio
import logging
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
from base_agents.base_agent import BaseAgent


class ModelEnsembleAgent(BaseAgent):
    """
    Agent responsible for orchestrating multiple model predictions.
    
    Capabilities:
    - Multi-model prediction coordination
    - Ensemble weight optimization
    - Confidence estimation
    - Model selection
    """
    
    def __init__(self):
        super().__init__(
            agent_id="model_ensemble_agent",
            name="Model Ensemble Agent",
            description="Orchestrates predictions from multiple models"
        )
        
        # Model configurations
        self.models = {
            "lstm": {"weight": 0.3, "enabled": True},
            "transformer": {"weight": 0.3, "enabled": True},
            "fusion": {"weight": 0.4, "enabled": True}
        }
        
    def _initialize_capabilities(self):
        self.add_capability("multi_model_coordination")
        self.add_capability("ensemble_weighting")
        self.add_capability("confidence_estimation")
        self.add_capability("model_selection")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for model ensemble."""
        return "patient_data" in input_data or "features" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute ensemble prediction across multiple models.
        
        Args:
            input_data: Contains patient features/data
            
        Returns:
            Dict with ensemble prediction and individual model predictions
        """
        self.logger.info("Starting ensemble prediction")
        
        # Get predictions from individual models
        individual_predictions = await self._get_individual_predictions(input_data)
        
        # Calculate ensemble prediction
        ensemble_prediction = await self._calculate_ensemble(individual_predictions)
        
        # Estimate confidence
        confidence = await self._estimate_confidence(individual_predictions)
        
        # Select best performing model for this case
        best_model = await self._select_best_model(individual_predictions)
        
        return {
            "ensemble_prediction": ensemble_prediction,
            "individual_predictions": individual_predictions,
            "confidence": confidence,
            "best_model": best_model,
            "model_weights": self.models,
            "ensemble_metadata": {
                "timestamp": datetime.now().isoformat(),
                "models_used": len([m for m in self.models if self.models[m]["enabled"]])
            }
        }
    
    async def _get_individual_predictions(self, input_data: Dict[str, Any]) -> Dict[str, float]:
        """Get predictions from individual models."""
        predictions = {}
        
        for model_name, config in self.models.items():
            if config["enabled"]:
                # Simulate model prediction (in real implementation, call actual models)
                prediction = await self._simulate_model_prediction(model_name, input_data)
                predictions[model_name] = prediction
        
        return predictions
    
    async def _simulate_model_prediction(self, model_name: str, input_data: Dict[str, Any]) -> float:
        """Simulate model prediction (placeholder for actual model calls)."""
        # In real implementation, this would call the actual ONNX models
        # For now, return simulated predictions
        base_risk = 0.3
        
        # Add some variation based on model type
        if model_name == "lstm":
            return base_risk + np.random.normal(0, 0.05)
        elif model_name == "transformer":
            return base_risk + np.random.normal(0.02, 0.04)
        elif model_name == "fusion":
            return base_risk + np.random.normal(0.01, 0.03)
        
        return base_risk
    
    async def _calculate_ensemble(self, predictions: Dict[str, float]) -> float:
        """Calculate weighted ensemble prediction."""
        ensemble_pred = 0.0
        total_weight = 0.0
        
        for model_name, prediction in predictions.items():
            weight = self.models[model_name]["weight"]
            ensemble_pred += prediction * weight
            total_weight += weight
        
        return ensemble_pred / total_weight if total_weight > 0 else 0.0
    
    async def _estimate_confidence(self, predictions: Dict[str, float]) -> float:
        """Estimate prediction confidence based on model agreement."""
        if not predictions:
            return 0.0
        
        values = list(predictions.values())
        std_dev = np.std(values)
        
        # Lower standard deviation = higher confidence
        confidence = max(0.0, 1.0 - (std_dev * 2))
        
        return confidence
    
    async def _select_best_model(self, predictions: Dict[str, float]) -> str:
        """Select the best performing model for this case."""
        if not predictions:
            return "none"
        
        # In real implementation, this would use historical performance
        # For now, return the model with median prediction
        values = list(predictions.items())
        values.sort(key=lambda x: x[1])
        
        return values[len(values) // 2][0]