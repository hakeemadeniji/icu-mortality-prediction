"""
Explainability Agent - Generates model explanations and interpretations
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from base_agents.base_agent import BaseAgent


class ExplainabilityAgent(BaseAgent):
    """
    Agent specialized in model explanation and interpretation.
    
    Capabilities:
    - Feature importance analysis
    - Prediction explanation generation
    - Counterfactual analysis
    - Decision path visualization
    """
    
    def __init__(self):
        super().__init__(
            agent_id="explainability_agent",
            name="Explainability Agent",
            description="Generates model explanations and interpretations with AI-powered analysis"
        )
        
        # Common clinical feature explanations
        self.feature_explanations = {
            "age": "Advanced age is associated with reduced physiological reserve and higher mortality risk",
            "sofa_score": "Higher SOFA scores indicate greater organ dysfunction and mortality risk",
            "lactate": "Elevated lactate indicates tissue hypoxia and is associated with poor outcomes",
            "vasopressor_use": "Vasopressor requirement indicates hemodynamic instability",
            "mechanical_ventilation": "Mechanical ventilation indicates respiratory failure",
            "comorbidity_count": "Higher comorbidity burden increases mortality risk",
            "emergency_admission": "Emergency admissions are associated with higher acuity and mortality"
        }
        
        # Model selection: Claude Opus for complex explanation generation
        self.model_preference = "claude-opus"
        self.model_reasoning = "Complex reasoning required for generating comprehensive explanations"

    def _initialize_capabilities(self):
        self.add_capability("feature_importance_analysis")
        self.add_capability("prediction_explanation")
        self.add_capability("counterfactual_analysis")
        self.add_capability("decision_path_visualization")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for explainability."""
        return "prediction" in input_data or "model_output" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate explanations for predictions.
        
        Args:
            input_data: Contains prediction and feature information
            
        Returns:
            Dict with explanation results
        """
        prediction = input_data.get("prediction") or input_data.get("model_output", {})
        features = input_data.get("features") or input_data.get("input_features", {})
        model_info = input_data.get("model_info", {})
        
        self.logger.info("Generating prediction explanations")
        
        # Analyze feature importance
        feature_importance = await self._analyze_feature_importance(features, prediction)
        
        # Generate prediction explanation
        prediction_explanation = await self._generate_prediction_explanation(features, prediction)
        
        # Perform counterfactual analysis
        counterfactual_analysis = await self._perform_counterfactual_analysis(features, prediction)
        
        # Visualize decision path
        decision_path = await self._visualize_decision_path(features, prediction, model_info)
        
        return {
            "feature_importance": feature_importance,
            "prediction_explanation": prediction_explanation,
            "counterfactual_analysis": counterfactual_analysis,
            "decision_path": decision_path,
            "explanation_metadata": {
                "analysis_time": datetime.now().isoformat(),
                "model_used": self.model_preference
            }
        }
    
    async def _analyze_feature_importance(self, features: Dict[str, Any], 
                                        prediction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze feature importance for the prediction."""
        importance_scores = []
        
        # Simplified feature importance calculation
        for feature_name, feature_value in features.items():
            if feature_name in self.feature_explanations:
                # Calculate importance based on deviation from normal
                importance = 0.5
                if isinstance(feature_value, (int, float)):
                    # Add importance for extreme values
                    if feature_value > 1.0 or feature_value < 0.0:
                        importance += 0.3
                    if abs(feature_value) > 2.0:
                        importance += 0.2
                
                importance_scores.append({
                    "feature": feature_name,
                    "value": feature_value,
                    "importance": round(min(importance, 1.0), 3),
                    "explanation": self.feature_explanations.get(feature_name, "Clinical risk factor")
                })
        
        # Sort by importance
        importance_scores.sort(key=lambda x: x["importance"], reverse=True)
        
        return importance_scores[:10]  # Return top 10
    
    async def _generate_prediction_explanation(self, features: Dict[str, Any], 
                                             prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive prediction explanation."""
        predicted_risk = prediction.get("probability", prediction.get("value", 0.5))
        
        # Generate narrative explanation
        if predicted_risk >= 0.7:
            risk_level = "high"
            explanation = "Patient exhibits multiple high-risk factors indicating significant mortality risk"
        elif predicted_risk >= 0.4:
            risk_level = "moderate"
            explanation = "Patient shows moderate risk factors requiring close monitoring"
        else:
            risk_level = "low"
            explanation = "Patient demonstrates relatively stable condition with lower mortality risk"
        
        # Identify key risk factors
        key_factors = []
        for feature_name, feature_value in features.items():
            if feature_name in self.feature_explanations:
                if isinstance(feature_value, (int, float)) and abs(feature_value) > 1.0:
                    key_factors.append({
                        "factor": feature_name,
                        "value": feature_value,
                        "contribution": "increases risk" if feature_value > 0 else "decreases risk"
                    })
        
        return {
            "predicted_risk": round(predicted_risk, 3),
            "risk_level": risk_level,
            "narrative_explanation": explanation,
            "key_risk_factors": key_factors[:5]
        }
    
    async def _perform_counterfactual_analysis(self, features: Dict[str, Any], 
                                             prediction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform counterfactual analysis."""
        counterfactuals = []
        
        # Generate counterfactual scenarios
        modifiable_features = ["lactate", "vasopressor_use", "mechanical_ventilation"]
        
        for feature in modifiable_features:
            if feature in features:
                original_value = features[feature]
                modified_value = original_value * 0.5  # Hypothetical improvement
                
                counterfactuals.append({
                    "feature": feature,
                    "original_value": original_value,
                    "modified_value": modified_value,
                    "expected_impact": "reduced mortality risk",
                    "clinical_relevance": "Potential intervention target"
                })
        
        return counterfactuals
    
    async def _visualize_decision_path(self, features: Dict[str, Any], 
                                      prediction: Dict[str, Any],
                                      model_info: Dict[str, Any]) -> Dict[str, Any]:
        """Visualize the decision path."""
        decision_steps = []
        
        # Simplified decision path
        decision_steps.append({
            "step": 1,
            "decision": "Initial risk assessment",
            "factors": ["age", "comorbidities"],
            "outcome": "Baseline risk calculated"
        })
        
        decision_steps.append({
            "step": 2,
            "decision": "Organ dysfunction evaluation",
            "factors": ["SOFA score", "lactate", "organ support"],
            "outcome": "Physiological severity determined"
        })
        
        decision_steps.append({
            "step": 3,
            "decision": "Treatment intensity assessment",
            "factors": ["vasopressors", "mechanical ventilation", "CRRT"],
            "outcome": "Acuity level established"
        })
        
        decision_steps.append({
            "step": 4,
            "decision": "Final prediction",
            "factors": ["All integrated features"],
            "outcome": f"Mortality risk: {prediction.get('probability', 0.5):.2%}"
        })
        
        return {
            "decision_path": decision_steps,
            "model_type": model_info.get("model_type", "Ensemble"),
            "final_prediction": prediction.get("probability", 0.5)
        }