"""
Correction Trigger Agent - Triggers model retraining and correction
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from base_agents.base_agent import BaseAgent


class CorrectionTriggerAgent(BaseAgent):
    """
    Agent specialized in triggering model corrections and retraining.
    
    Capabilities:
    - Automatic retraining trigger
    - Performance degradation response
    - Drift-based correction
    - Model version management
    """
    
    def __init__(self):
        super().__init__(
            agent_id="correction_trigger_agent",
            name="Correction Trigger Agent",
            description="Triggers model retraining and correction with AI-powered decision making"
        )
        
        # Correction triggers
        self.correction_triggers = {
            "performance_degradation": 0.1,  # 10% performance drop
            "data_drift_severity": 0.2,     # 20% data drift
            "concept_drift_severity": 0.15, # 15% concept drift
            "prediction_confidence_drop": 0.2 # 20% confidence drop
        }
        
        # Model selection: Claude Opus for complex decision making
        self.model_preference = "claude-opus"
        self.model_reasoning = "Complex decision making required for retraining triggers"

    def _initialize_capabilities(self):
        self.add_capability("automatic_retraining")
        self.add_capability("performance_degradation_response")
        self.add_capability("drift_based_correction")
        self.add_capability("model_version_management")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for correction triggering."""
        return "evaluation_results" in input_data or "performance_metrics" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate if model correction is needed and trigger appropriate actions.
        
        Args:
            input_data: Contains evaluation results and performance metrics
            
        Returns:
            Dict with correction trigger results
        """
        evaluation_results = input_data.get("evaluation_results", {})
        performance_metrics = input_data.get("performance_metrics", {})
        drift_analysis = input_data.get("drift_analysis", {})
        
        self.logger.info("Evaluating correction triggers")
        
        # Evaluate if correction is needed
        correction_needed = await self._evaluate_correction_needed(
            performance_metrics, drift_analysis, evaluation_results
        )
        
        # Determine correction type
        correction_type = await self._determine_correction_type(correction_needed)
        
        # Generate correction plan
        correction_plan = await self._generate_correction_plan(correction_type, performance_metrics)
        
        # Check if automatic retraining should be triggered
        retraining_trigger = await self._evaluate_retraining_trigger(correction_needed)
        
        return {
            "correction_needed": correction_needed["needed"],
            "correction_type": correction_type,
            "correction_plan": correction_plan,
            "retraining_trigger": retraining_trigger,
            "correction_metadata": {
                "evaluation_time": datetime.now().isoformat(),
                "model_used": self.model_preference,
                "current_model_version": input_data.get("model_version", "1.0.0")
            }
        }
    
    async def _evaluate_correction_needed(self, performance_metrics: Dict[str, Any], 
                                         drift_analysis: Dict[str, Any],
                                         evaluation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate if model correction is needed."""
        correction_triggers = []
        severity_score = 0.0
        
        # Check performance degradation
        if performance_metrics:
            degradation = performance_metrics.get("model_degradation", {})
            if degradation.get("degradation_detected", False):
                severity_score += 0.3
                correction_triggers.append({
                    "type": "performance_degradation",
                    "severity": "high",
                    "details": degradation.get("degraded_metrics", [])
                })
        
        # Check data drift
        if drift_analysis:
            data_drift = drift_analysis.get("data_drift", {})
            if data_drift.get("drift_detected", False):
                drift_score = data_drift.get("overall_drift_score", 0)
                if drift_score > self.correction_triggers["data_drift_severity"]:
                    severity_score += 0.2
                    correction_triggers.append({
                        "type": "data_drift",
                        "severity": "high" if drift_score > 0.3 else "moderate",
                        "drift_score": drift_score
                    })
        
        # Check concept drift
        if drift_analysis:
            concept_drift = drift_analysis.get("concept_drift", {})
            if concept_drift.get("concept_drift_detected", False):
                severity_score += 0.3
                correction_triggers.append({
                    "type": "concept_drift",
                    "severity": "high",
                    "details": concept_drift
                })
        
        # Check evaluation results
        if evaluation_results:
            thresholds_met = evaluation_results.get("thresholds_met", {})
            failed_thresholds = [k for k, v in thresholds_met.items() if not v]
            if failed_thresholds:
                severity_score += 0.2 * len(failed_thresholds)
                correction_triggers.append({
                    "type": "threshold_failure",
                    "severity": "moderate",
                    "failed_thresholds": failed_thresholds
                })
        
        return {
            "needed": severity_score >= 0.5,
            "severity_score": round(min(severity_score, 1.0), 2),
            "triggers": correction_triggers
        }
    
    async def _determine_correction_type(self, correction_needed: Dict[str, Any]) -> str:
        """Determine the type of correction needed."""
        if not correction_needed["needed"]:
            return "none"
        
        triggers = correction_needed.get("triggers", [])
        trigger_types = [t["type"] for t in triggers]
        
        if "performance_degradation" in trigger_types and "concept_drift" in trigger_types:
            return "full_retraining"
        elif "data_drift" in trigger_types:
            return "data_update_recalibration"
        elif "concept_drift" in trigger_types:
            return "model_retraining"
        elif "threshold_failure" in trigger_types:
            return "threshold_adjustment"
        else:
            return "monitoring_increase"
    
    async def _generate_correction_plan(self, correction_type: str, 
                                      performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Generate correction plan based on type."""
        plans = {
            "none": {
                "action": "continue_monitoring",
                "steps": ["Maintain current monitoring frequency", "Continue standard evaluation"]
            },
            "full_retraining": {
                "action": "full_model_retraining",
                "steps": [
                    "Collect new training data",
                    "Perform data quality validation",
                    "Retrain all model components",
                    "Validate new model performance",
                    "Deploy new model version"
                ],
                "estimated_time": "24-48 hours",
                "priority": "high"
            },
            "data_update_recalibration": {
                "action": "data_update_and_recalibration",
                "steps": [
                    "Update feature distributions",
                    "Recalibrate model thresholds",
                    "Validate calibration",
                    "Deploy updated model"
                ],
                "estimated_time": "4-8 hours",
                "priority": "moderate"
            },
            "model_retraining": {
                "action": "model_retraining_only",
                "steps": [
                    "Analyze concept drift patterns",
                    "Retrain affected model components",
                    "Validate performance",
                    "Deploy updated components"
                ],
                "estimated_time": "12-24 hours",
                "priority": "high"
            },
            "threshold_adjustment": {
                "action": "threshold_adjustment",
                "steps": [
                    "Analyze failed thresholds",
                    "Adjust decision thresholds",
                    "Validate new thresholds",
                    "Deploy threshold updates"
                ],
                "estimated_time": "1-2 hours",
                "priority": "moderate"
            },
            "monitoring_increase": {
                "action": "increase_monitoring",
                "steps": [
                    "Increase evaluation frequency",
                    "Add additional monitoring metrics",
                    "Set up automated alerts"
                ],
                "estimated_time": "immediate",
                "priority": "low"
            }
        }
        
        return plans.get(correction_type, plans["monitoring_increase"])
    
    async def _evaluate_retraining_trigger(self, correction_needed: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate if automatic retraining should be triggered."""
        if not correction_needed["needed"]:
            return {
                "trigger_retraining": False,
                "reason": "No correction needed"
            }
        
        severity_score = correction_needed.get("severity_score", 0)
        
        # Only trigger automatic retraining for high severity
        if severity_score >= 0.8:
            return {
                "trigger_retraining": True,
                "reason": "High severity issues detected",
                "automatic": True,
                "approval_required": False
            }
        elif severity_score >= 0.5:
            return {
                "trigger_retraining": True,
                "reason": "Moderate severity issues detected",
                "automatic": False,
                "approval_required": True
            }
        else:
            return {
                "trigger_retraining": False,
                "reason": "Severity below retraining threshold",
                "automatic": False,
                "approval_required": False
            }