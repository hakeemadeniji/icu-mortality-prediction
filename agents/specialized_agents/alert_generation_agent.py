"""
Alert Generation Agent - Generates clinical alerts based on predictions
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from base_agents.base_agent import BaseAgent


class AlertGenerationAgent(BaseAgent):
    """
    Agent specialized in clinical alert generation.
    
    Capabilities:
    - Risk-based alert generation
    - Priority classification
    - Alert aggregation and deduplication
    - Clinical context incorporation
    """
    
    def __init__(self):
        super().__init__(
            agent_id="alert_generation_agent",
            name="Alert Generation Agent",
            description="Generates clinical alerts based on predictions with AI-powered prioritization"
        )
        
        # Alert thresholds
        self.alert_thresholds = {
            "critical": 0.8,
            "high": 0.6,
            "moderate": 0.4,
            "low": 0.2
        }
        
        # Alert types
        self.alert_types = {
            "mortality_risk": "High mortality risk detected",
            "clinical_deterioration": "Clinical deterioration detected",
            "vital_sign_abnormality": "Abnormal vital signs detected",
            "lab_abnormality": "Critical lab values detected",
            "medication_interaction": "Potential medication interaction",
            "comorbidity_complication": "Comorbidity complication risk"
        }
        
        # Model selection: Claude Haiku for fast, time-critical alert generation
        self.model_preference = "claude-haiku"
        self.model_reasoning = "Fast processing required for time-critical alert generation"

    def _initialize_capabilities(self):
        self.add_capability("risk_based_alerting")
        self.add_capability("priority_classification")
        self.add_capability("alert_aggregation")
        self.add_capability("context_aware_alerting")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for alert generation."""
        return "prediction" in input_data or "patient_data" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate clinical alerts based on predictions.
        
        Args:
            input_data: Contains predictions and patient data
            
        Returns:
            Dict with generated alerts
        """
        prediction = input_data.get("prediction", {})
        patient_data = input_data.get("patient_data", {})
        clinical_context = input_data.get("clinical_context", {})
        
        self.logger.info("Generating clinical alerts")
        
        # Generate risk-based alerts
        risk_alerts = await self._generate_risk_alerts(prediction)
        
        # Generate clinical alerts
        clinical_alerts = await self._generate_clinical_alerts(patient_data, clinical_context)
        
        # Classify alert priorities
        prioritized_alerts = await self._classify_alert_priorities(risk_alerts + clinical_alerts)
        
        # Aggregate and deduplicate alerts
        aggregated_alerts = await self._aggregate_alerts(prioritized_alerts)
        
        return {
            "alerts": aggregated_alerts,
            "alert_summary": {
                "total_alerts": len(aggregated_alerts),
                "critical_alerts": len([a for a in aggregated_alerts if a["priority"] == "critical"]),
                "high_priority_alerts": len([a for a in aggregated_alerts if a["priority"] == "high"]),
                "moderate_priority_alerts": len([a for a in aggregated_alerts if a["priority"] == "moderate"]),
                "low_priority_alerts": len([a for a in aggregated_alerts if a["priority"] == "low"])
            },
            "alert_metadata": {
                "generation_time": datetime.now().isoformat(),
                "model_used": self.model_preference
            }
        }
    
    async def _generate_risk_alerts(self, prediction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on prediction risk."""
        alerts = []
        
        predicted_risk = prediction.get("probability", prediction.get("value", 0.0))
        
        if predicted_risk >= self.alert_thresholds["critical"]:
            alerts.append({
                "type": "mortality_risk",
                "message": f"CRITICAL: Mortality risk {predicted_risk:.1%} - immediate intervention required",
                "priority": "critical",
                "risk_score": predicted_risk,
                "recommended_action": "Activate rapid response team, consider escalation"
            })
        elif predicted_risk >= self.alert_thresholds["high"]:
            alerts.append({
                "type": "mortality_risk",
                "message": f"HIGH: Mortality risk {predicted_risk:.1%} - close monitoring required",
                "priority": "high",
                "risk_score": predicted_risk,
                "recommended_action": "Increase monitoring frequency, review treatment plan"
            })
        elif predicted_risk >= self.alert_thresholds["moderate"]:
            alerts.append({
                "type": "mortality_risk",
                "message": f"MODERATE: Mortality risk {predicted_risk:.1%} - continue monitoring",
                "priority": "moderate",
                "risk_score": predicted_risk,
                "recommended_action": "Continue standard monitoring protocols"
            })
        
        return alerts
    
    async def _generate_clinical_alerts(self, patient_data: Dict[str, Any], 
                                      clinical_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on clinical data."""
        alerts = []
        
        # Check vital signs
        vital_signs = patient_data.get("vital_signs", {})
        if vital_signs:
            if vital_signs.get("heart_rate", 0) > 120 or vital_signs.get("heart_rate", 0) < 40:
                alerts.append({
                    "type": "vital_sign_abnormality",
                    "message": f"Abnormal heart rate: {vital_signs.get('heart_rate')} bpm",
                    "priority": "high",
                    "value": vital_signs.get("heart_rate"),
                    "recommended_action": "Assess hemodynamic stability"
                })
            
            if vital_signs.get("blood_pressure_systolic", 0) < 90:
                alerts.append({
                    "type": "vital_sign_abnormality",
                    "message": f"Hypotension detected: {vital_signs.get('blood_pressure_systolic')} mmHg",
                    "priority": "critical",
                    "value": vital_signs.get("blood_pressure_systolic"),
                    "recommended_action": "Initiate fluid resuscitation, consider vasopressors"
                })
        
        # Check lab values
        lab_values = patient_data.get("lab_values", {})
        if lab_values:
            if lab_values.get("lactate", 0) > 4.0:
                alerts.append({
                    "type": "lab_abnormality",
                    "message": f"Severe lactic acidosis: lactate {lab_values.get('lactate')} mmol/L",
                    "priority": "critical",
                    "value": lab_values.get("lactate"),
                    "recommended_action": "Evaluate tissue perfusion, consider cause"
                })
        
        return alerts
    
    async def _classify_alert_priorities(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify and prioritize alerts."""
        # Alerts already have priority assigned, but we can refine based on context
        prioritized = []
        
        for alert in alerts:
            # Add timestamp and ID
            alert["alert_id"] = f"alert_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(prioritized)}"
            alert["timestamp"] = datetime.now().isoformat()
            
            # Adjust priority based on multiple factors
            if alert.get("type") == "mortality_risk" and alert.get("risk_score", 0) > 0.9:
                alert["priority"] = "critical"
            
            prioritized.append(alert)
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "moderate": 2, "low": 3}
        prioritized.sort(key=lambda x: priority_order.get(x["priority"], 4))
        
        return prioritized
    
    async def _aggregate_alerts(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate and deduplicate alerts."""
        aggregated = []
        seen_messages = set()
        
        for alert in alerts:
            message = alert.get("message", "")
            if message not in seen_messages:
                seen_messages.add(message)
                aggregated.append(alert)
            else:
                # If duplicate, increment count instead
                for existing_alert in aggregated:
                    if existing_alert.get("message") == message:
                        existing_alert["count"] = existing_alert.get("count", 1) + 1
                        break
        
        return aggregated