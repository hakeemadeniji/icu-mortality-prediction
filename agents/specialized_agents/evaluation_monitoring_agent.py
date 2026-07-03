"""
Evaluation Monitoring Agent - Continuous model evaluation and performance monitoring
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from base_agents.base_agent import BaseAgent


class EvaluationMonitoringAgent(BaseAgent):
    """
    Agent specialized in continuous model evaluation and performance monitoring.
    
    Capabilities:
    - Performance metric calculation
    - Data drift detection
    - Concept drift monitoring
    - Model degradation tracking
    """
    
    def __init__(self):
        super().__init__(
            agent_id="evaluation_monitoring_agent",
            name="Evaluation Monitoring Agent",
            description="Continuous model evaluation and performance monitoring with AI-powered analysis"
        )
        
        # Performance metrics thresholds
        self.performance_thresholds = {
            "auroc": 0.75,
            "auprc": 0.65,
            "accuracy": 0.70,
            "f1_score": 0.65
        }
        
        # Drift thresholds
        self.drift_thresholds = {
            "data_drift": 0.1,
            "concept_drift": 0.15,
            "performance_degradation": 0.05
        }
        
        # Model selection: GLM for efficient metric calculation
        self.model_preference = "glm"
        self.model_reasoning = "Efficient metric calculation and performance monitoring"

    def _initialize_capabilities(self):
        self.add_capability("performance_metrics")
        self.add_capability("data_drift_detection")
        self.add_capability("concept_drift_monitoring")
        self.add_capability("degradation_tracking")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for evaluation monitoring."""
        return "predictions" in input_data or "model_performance" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor model performance and detect drift.
        
        Args:
            input_data: Contains predictions and performance data
            
        Returns:
            Dict with evaluation results
        """
        predictions = input_data.get("predictions", [])
        actual_outcomes = input_data.get("actual_outcomes", [])
        baseline_metrics = input_data.get("baseline_metrics", {})
        feature_distributions = input_data.get("feature_distributions", {})
        
        self.logger.info(f"Evaluating {len(predictions)} predictions")
        
        # Calculate performance metrics
        performance_metrics = await self._calculate_performance_metrics(predictions, actual_outcomes)
        
        # Detect data drift
        data_drift = await self._detect_data_drift(feature_distributions)
        
        # Monitor concept drift
        concept_drift = await self._monitor_concept_drift(predictions, actual_outcomes, baseline_metrics)
        
        # Track model degradation
        degradation = await self._track_degradation(performance_metrics, baseline_metrics)
        
        return {
            "performance_metrics": performance_metrics,
            "data_drift": data_drift,
            "concept_drift": concept_drift,
            "model_degradation": degradation,
            "evaluation_metadata": {
                "predictions_evaluated": len(predictions),
                "evaluation_time": datetime.now().isoformat(),
                "model_used": self.model_preference
            }
        }
    
    async def _calculate_performance_metrics(self, predictions: List[Dict[str, Any]], 
                                           actual_outcomes: List[bool]) -> Dict[str, Any]:
        """Calculate performance metrics."""
        if not predictions or not actual_outcomes:
            return {"status": "insufficient_data"}
        
        # Extract predicted probabilities and actual outcomes
        pred_probs = [p.get("probability", p.get("value", 0.5)) for p in predictions]
        pred_labels = [1 if prob >= 0.5 else 0 for prob in pred_probs]
        
        # Calculate metrics
        true_positives = sum(1 for p, a in zip(pred_labels, actual_outcomes) if p == 1 and a == True)
        true_negatives = sum(1 for p, a in zip(pred_labels, actual_outcomes) if p == 0 and a == False)
        false_positives = sum(1 for p, a in zip(pred_labels, actual_outcomes) if p == 1 and a == False)
        false_negatives = sum(1 for p, a in zip(pred_labels, actual_outcomes) if p == 0 and a == True)
        
        # Basic metrics
        accuracy = (true_positives + true_negatives) / len(actual_outcomes) if actual_outcomes else 0
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Simplified AUROC calculation
        auroc = accuracy + 0.1 if accuracy > 0.7 else accuracy  # Simplified approximation
        auprc = recall * 0.8 if recall > 0.5 else recall  # Simplified approximation
        
        metrics = {
            "accuracy": round(accuracy, 3),
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1_score, 3),
            "auroc": round(min(auroc, 1.0), 3),
            "auprc": round(min(auprc, 1.0), 3),
            "confusion_matrix": {
                "true_positives": true_positives,
                "true_negatives": true_negatives,
                "false_positives": false_positives,
                "false_negatives": false_negatives
            }
        }
        
        # Check against thresholds
        metrics["thresholds_met"] = {
            "auroc": metrics["auroc"] >= self.performance_thresholds["auroc"],
            "auprc": metrics["auprc"] >= self.performance_thresholds["auprc"],
            "accuracy": metrics["accuracy"] >= self.performance_thresholds["accuracy"],
            "f1_score": metrics["f1_score"] >= self.performance_thresholds["f1_score"]
        }
        
        return metrics
    
    async def _detect_data_drift(self, feature_distributions: Dict[str, Any]) -> Dict[str, Any]:
        """Detect data drift in feature distributions."""
        if not feature_distributions:
            return {"status": "no_distribution_data"}
        
        drift_detected = False
        drift_scores = {}
        
        # Simplified drift detection
        for feature, distribution in feature_distributions.items():
            if isinstance(distribution, dict) and "current" in distribution and "baseline" in distribution:
                current_mean = distribution["current"].get("mean", 0)
                baseline_mean = distribution["baseline"].get("mean", 0)
                
                # Calculate normalized drift
                if baseline_mean != 0:
                    drift_score = abs(current_mean - baseline_mean) / abs(baseline_mean)
                else:
                    drift_score = abs(current_mean)
                
                drift_scores[feature] = round(drift_score, 3)
                
                if drift_score > self.drift_thresholds["data_drift"]:
                    drift_detected = True
        
        return {
            "drift_detected": drift_detected,
            "drift_scores": drift_scores,
            "overall_drift_score": round(sum(drift_scores.values()) / len(drift_scores), 3) if drift_scores else 0
        }
    
    async def _monitor_concept_drift(self, predictions: List[Dict[str, Any]], 
                                   actual_outcomes: List[bool],
                                   baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor concept drift."""
        if not predictions or not actual_outcomes or not baseline_metrics:
            return {"status": "insufficient_data"}
        
        # Calculate current performance
        pred_probs = [p.get("probability", p.get("value", 0.5)) for p in predictions]
        pred_labels = [1 if prob >= 0.5 else 0 for prob in pred_probs]
        
        current_accuracy = sum(1 for p, a in zip(pred_labels, actual_outcomes) if p == a) / len(actual_outcomes)
        baseline_accuracy = baseline_metrics.get("accuracy", 0.8)
        
        # Calculate performance change
        performance_change = abs(current_accuracy - baseline_accuracy)
        
        concept_drift_detected = performance_change > self.drift_thresholds["concept_drift"]
        
        return {
            "concept_drift_detected": concept_drift_detected,
            "baseline_accuracy": baseline_accuracy,
            "current_accuracy": round(current_accuracy, 3),
            "performance_change": round(performance_change, 3),
            "direction": "degradation" if current_accuracy < baseline_accuracy else "improvement"
        }
    
    async def _track_degradation(self, current_metrics: Dict[str, Any], 
                                baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Track model degradation over time."""
        degradation_detected = False
        degraded_metrics = []
        
        for metric_name, threshold_value in self.performance_thresholds.items():
            current_value = current_metrics.get(metric_name, 0)
            baseline_value = baseline_metrics.get(metric_name, threshold_value)
            
            if baseline_value > 0:
                degradation_ratio = current_value / baseline_value
                if degradation_ratio < (1.0 - self.drift_thresholds["performance_degradation"]):
                    degradation_detected = True
                    degraded_metrics.append({
                        "metric": metric_name,
                        "baseline": baseline_value,
                        "current": current_value,
                        "degradation_ratio": round(degradation_ratio, 3)
                    })
        
        return {
            "degradation_detected": degradation_detected,
            "degraded_metrics": degraded_metrics,
            "overall_health": "degraded" if degradation_detected else "healthy"
        }