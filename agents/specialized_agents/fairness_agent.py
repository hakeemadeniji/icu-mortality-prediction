"""
Fairness Agent - Monitors and mitigates bias in predictions
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from base_agents.base_agent import BaseAgent


class FairnessAgent(BaseAgent):
    """
    Agent specialized in fairness monitoring and bias mitigation.
    
    Capabilities:
    - Demographic parity analysis
    - Equal opportunity assessment
    - Bias detection and quantification
    - Fairness mitigation recommendations
    """
    
    def __init__(self):
        super().__init__(
            agent_id="fairness_agent",
            name="Fairness Monitoring Agent",
            description="Monitors and mitigates bias in predictions with AI-powered analysis"
        )
        
        # Protected attributes for fairness monitoring
        self.protected_attributes = ["age", "gender", "race", "ethnicity", "insurance_status"]
        
        # Fairness thresholds
        self.fairness_thresholds = {
            "demographic_parity_difference": 0.1,
            "equal_opportunity_difference": 0.1,
            "disparate_impact_ratio": 0.8
        }
        
        # Model selection: Claude Opus for complex bias analysis
        self.model_preference = "claude-opus"
        self.model_reasoning = "Complex bias analysis and fairness reasoning required"

    def _initialize_capabilities(self):
        self.add_capability("demographic_parity_analysis")
        self.add_capability("equal_opportunity_assessment")
        self.add_capability("bias_detection")
        self.add_capability("fairness_mitigation")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for fairness analysis."""
        return "predictions" in input_data or "model_predictions" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor fairness and detect bias.
        
        Args:
            input_data: Contains predictions and demographic information
            
        Returns:
            Dict with fairness analysis results
        """
        predictions = input_data.get("predictions") or input_data.get("model_predictions", [])
        demographics = input_data.get("demographics", [])
        
        self.logger.info(f"Analyzing fairness for {len(predictions)} predictions")
        
        # Analyze demographic parity
        demographic_parity = await self._analyze_demographic_parity(predictions, demographics)
        
        # Assess equal opportunity
        equal_opportunity = await self._assess_equal_opportunity(predictions, demographics)
        
        # Detect and quantify bias
        bias_analysis = await self._detect_bias(predictions, demographics)
        
        # Generate mitigation recommendations
        mitigation_recommendations = await self._generate_mitigation_recommendations(bias_analysis)
        
        return {
            "demographic_parity": demographic_parity,
            "equal_opportunity": equal_opportunity,
            "bias_analysis": bias_analysis,
            "mitigation_recommendations": mitigation_recommendations,
            "fairness_metadata": {
                "predictions_analyzed": len(predictions),
                "analysis_time": datetime.now().isoformat(),
                "model_used": self.model_preference
            }
        }
    
    async def _analyze_demographic_parity(self, predictions: List[Dict[str, Any]], 
                                        demographics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze demographic parity across protected groups."""
        parity_results = {}
        
        for attribute in self.protected_attributes:
            if attribute in demographics[0] if demographics else {}:
                # Group predictions by attribute
                group_predictions = {}
                for i, pred in enumerate(predictions):
                    if i < len(demographics):
                        attr_value = demographics[i].get(attribute, "unknown")
                        if attr_value not in group_predictions:
                            group_predictions[attr_value] = []
                        group_predictions[attr_value].append(pred.get("probability", 0.5))
                
                # Calculate selection rates
                selection_rates = {}
                for group, preds in group_predictions.items():
                    selection_rates[group] = sum(preds) / len(preds) if preds else 0
                
                # Calculate demographic parity difference
                rates = list(selection_rates.values())
                if rates:
                    parity_diff = max(rates) - min(rates)
                    parity_results[attribute] = {
                        "selection_rates": selection_rates,
                        "demographic_parity_difference": round(parity_diff, 3),
                        "threshold_met": parity_diff <= self.fairness_thresholds["demographic_parity_difference"]
                    }
        
        return parity_results
    
    async def _assess_equal_opportunity(self, predictions: List[Dict[str, Any]], 
                                      demographics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess equal opportunity across protected groups."""
        opportunity_results = {}
        
        for attribute in self.protected_attributes:
            if attribute in demographics[0] if demographics else {}:
                # Simplified equal opportunity calculation
                group_tpr = {}  # True positive rates by group
                
                # Calculate TPR for each group (simplified)
                for i, pred in enumerate(predictions):
                    if i < len(demographics):
                        attr_value = demographics[i].get(attribute, "unknown")
                        if attr_value not in group_tpr:
                            group_tpr[attr_value] = []
                        group_tpr[attr_value].append(pred.get("probability", 0.5))
                
                # Calculate average TPR by group
                avg_tpr = {}
                for group, preds in group_tpr.items():
                    avg_tpr[group] = sum(preds) / len(preds) if preds else 0
                
                # Calculate equal opportunity difference
                tprs = list(avg_tpr.values())
                if tprs:
                    eo_diff = max(tprs) - min(tprs)
                    opportunity_results[attribute] = {
                        "true_positive_rates": avg_tpr,
                        "equal_opportunity_difference": round(eo_diff, 3),
                        "threshold_met": eo_diff <= self.fairness_thresholds["equal_opportunity_difference"]
                    }
        
        return opportunity_results
    
    async def _detect_bias(self, predictions: List[Dict[str, Any]], 
                         demographics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect and quantify bias in predictions."""
        bias_detection = {
            "detected_biases": [],
            "bias_scores": {},
            "overall_fairness_score": 0.8
        }
        
        # Simplified bias detection
        for attribute in self.protected_attributes:
            if attribute in demographics[0] if demographics else {}:
                # Calculate bias score for this attribute
                group_predictions = {}
                for i, pred in enumerate(predictions):
                    if i < len(demographics):
                        attr_value = demographics[i].get(attribute, "unknown")
                        if attr_value not in group_predictions:
                            group_predictions[attr_value] = []
                        group_predictions[attr_value].append(pred.get("probability", 0.5))
                
                # Calculate variance between groups
                avg_predictions = {group: sum(preds)/len(preds) for group, preds in group_predictions.items()}
                prediction_values = list(avg_predictions.values())
                
                if prediction_values:
                    variance = max(prediction_values) - min(prediction_values)
                    bias_score = min(variance / 0.5, 1.0)  # Normalize to 0-1
                    
                    bias_detection["bias_scores"][attribute] = round(bias_score, 3)
                    
                    if bias_score > 0.3:
                        bias_detection["detected_biases"].append({
                            "attribute": attribute,
                            "bias_score": round(bias_score, 3),
                            "severity": "high" if bias_score > 0.5 else "moderate"
                        })
        
        # Calculate overall fairness score
        if bias_detection["bias_scores"]:
            avg_bias = sum(bias_detection["bias_scores"].values()) / len(bias_detection["bias_scores"])
            bias_detection["overall_fairness_score"] = round(max(0.0, 1.0 - avg_bias), 3)
        
        return bias_detection
    
    async def _generate_mitigation_recommendations(self, bias_analysis: Dict[str, Any]) -> List[str]:
        """Generate fairness mitigation recommendations."""
        recommendations = []
        
        if bias_analysis["detected_biases"]:
            for bias in bias_analysis["detected_biases"]:
                attribute = bias["attribute"]
                severity = bias["severity"]
                
                if severity == "high":
                    recommendations.append(f"High bias detected in {attribute} - implement reweighting or adversarial debiasing")
                    recommendations.append(f"Consider collecting more representative data for {attribute}")
                else:
                    recommendations.append(f"Moderate bias detected in {attribute} - monitor and consider calibration")
            
            recommendations.append("Implement fairness constraints in model training")
            recommendations.append("Consider post-processing techniques for fairness")
        else:
            recommendations.append("No significant bias detected - continue monitoring")
            recommendations.append("Maintain current fairness practices")
        
        return recommendations