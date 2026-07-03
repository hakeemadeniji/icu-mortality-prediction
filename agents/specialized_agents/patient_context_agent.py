"""
Patient Context Agent - Incorporates patient-specific context into analysis
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from base_agents.base_agent import BaseAgent


class PatientContextAgent(BaseAgent):
    """
    Agent specialized in patient-specific context incorporation.
    
    Capabilities:
    - Patient history integration
    - Context-aware prediction adjustment
    - Individualized risk assessment
    - Personalized recommendation generation
    """
    
    def __init__(self):
        super().__init__(
            agent_id="patient_context_agent",
            name="Patient Context Agent",
            description="Incorporates patient-specific context with AI-powered analysis"
        )
        
        # Context factors
        self.context_factors = {
            "previous_icu_admissions": "ICU readmission risk",
            "baseline_functional_status": "Pre-admission functional level",
            "advance_directives": "Goals of care preferences",
            "social_support": "Discharge planning considerations",
            "home_medications": "Medication reconciliation needs"
        }
        
        # Model selection: Claude Opus for complex context integration
        self.model_preference = "claude-opus"
        self.model_reasoning = "Complex reasoning required for patient context integration"

    def _initialize_capabilities(self):
        self.add_capability("history_integration")
        self.add_capability("context_adjustment")
        self.add_capability("individualized_risk")
        self.add_capability("personalized_recommendations")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for patient context."""
        return "patient_context" in input_data or "patient_history" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Incorporate patient-specific context into analysis.
        
        Args:
            input_data: Contains patient context and current data
            
        Returns:
            Dict with context-enhanced analysis
        """
        patient_context = input_data.get("patient_context", {})
        current_data = input_data.get("current_data", {})
        base_prediction = input_data.get("base_prediction", {})
        
        self.logger.info("Incorporating patient context")
        
        # Integrate patient history
        history_integration = await self._integrate_history(patient_context)
        
        # Adjust predictions based on context
        context_adjustment = await self._adjust_predictions(base_prediction, patient_context)
        
        # Generate individualized risk assessment
        individualized_risk = await self._assess_individualized_risk(current_data, patient_context)
        
        # Generate personalized recommendations
        personalized_recommendations = await self._generate_personalized_recommendations(
            patient_context, context_adjustment
        )
        
        return {
            "history_integration": history_integration,
            "context_adjustment": context_adjustment,
            "individualized_risk": individualized_risk,
            "personalized_recommendations": personalized_recommendations,
            "context_metadata": {
                "context_factors_used": len(patient_context),
                "analysis_time": datetime.now().isoformat(),
                "model_used": self.model_preference
            }
        }
    
    async def _integrate_history(self, patient_context: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate patient history into current analysis."""
        history_summary = {
            "previous_admissions": [],
            "chronic_conditions": [],
            "baseline_status": None,
            "relevant_history": []
        }
        
        # Extract previous ICU admissions
        if "previous_icu_admissions" in patient_context:
            admissions = patient_context["previous_icu_admissions"]
            history_summary["previous_admissions"] = admissions
            if len(admissions) >= 2:
                history_summary["relevant_history"].append("Frequent ICU readmissions - higher complexity")
        
        # Extract chronic conditions
        if "chronic_conditions" in patient_context:
            conditions = patient_context["chronic_conditions"]
            history_summary["chronic_conditions"] = conditions
            high_risk_conditions = ["heart_failure", "copd", "chronic_kidney_disease"]
            if any(cond.lower() in [c.lower() for c in conditions] for cond in high_risk_conditions):
                history_summary["relevant_history"].append("High-risk chronic conditions present")
        
        # Extract baseline functional status
        if "baseline_functional_status" in patient_context:
            history_summary["baseline_status"] = patient_context["baseline_functional_status"]
            if patient_context["baseline_functional_status"] == "dependent":
                history_summary["relevant_history"].append("Baseline functional dependence affects outcomes")
        
        return history_summary
    
    async def _adjust_predictions(self, base_prediction: Dict[str, Any], 
                                 patient_context: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust predictions based on patient context."""
        base_risk = base_prediction.get("probability", base_prediction.get("value", 0.5))
        adjustment_factor = 1.0
        adjustment_reasons = []
        
        # Adjust for previous admissions
        if patient_context.get("previous_icu_admissions"):
            admission_count = len(patient_context["previous_icu_admissions"])
            if admission_count >= 3:
                adjustment_factor *= 1.2
                adjustment_reasons.append("Multiple previous ICU admissions increase risk")
            elif admission_count >= 1:
                adjustment_factor *= 1.1
                adjustment_reasons.append("Previous ICU admission history")
        
        # Adjust for baseline status
        baseline_status = patient_context.get("baseline_functional_status", "independent")
        if baseline_status == "dependent":
            adjustment_factor *= 1.15
            adjustment_reasons.append("Baseline functional dependence")
        elif baseline_status == "partially_dependent":
            adjustment_factor *= 1.05
            adjustment_reasons.append("Partial functional dependence")
        
        # Adjust for advance directives
        if patient_context.get("advance_directives") == "comfort_care_only":
            adjustment_factor *= 0.9  # Lower acute intervention expectations
            adjustment_reasons.append("Comfort care focus may affect intervention intensity")
        
        adjusted_risk = min(base_risk * adjustment_factor, 1.0)
        
        return {
            "original_risk": base_risk,
            "adjusted_risk": round(adjusted_risk, 3),
            "adjustment_factor": round(adjustment_factor, 3),
            "adjustment_reasons": adjustment_reasons
        }
    
    async def _assess_individualized_risk(self, current_data: Dict[str, Any], 
                                        patient_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate individualized risk assessment."""
        risk_factors = []
        protective_factors = []
        
        # Analyze current condition in context of history
        if "chronic_conditions" in patient_context:
            chronic_conditions = patient_context["chronic_conditions"]
            if "heart_failure" in [c.lower() for c in chronic_conditions]:
                if current_data.get("current_diagnosis", "").lower() == "acute_decompensated_heart_failure":
                    risk_factors.append("Acute on chronic heart failure")
                else:
                    protective_factors.append("Stable chronic heart failure")
        
        # Social support assessment
        social_support = patient_context.get("social_support", "adequate")
        if social_support == "limited":
            risk_factors.append("Limited social support affects recovery potential")
        elif social_support == "adequate":
            protective_factors.append("Good social support system")
        
        # Age in context
        age = patient_context.get("age", 65)
        if age >= 80 and patient_context.get("baseline_functional_status") == "independent":
            protective_factors.append("High functional status despite advanced age")
        
        return {
            "risk_factors": risk_factors,
            "protective_factors": protective_factors,
            "individualized_risk_level": "high" if len(risk_factors) >= 3 else 
                                       "moderate" if len(risk_factors) >= 1 else "low"
        }
    
    async def _generate_personalized_recommendations(self, patient_context: Dict[str, Any], 
                                                   context_adjustment: Dict[str, Any]) -> List[str]:
        """Generate personalized recommendations based on context."""
        recommendations = []
        
        # Based on functional status
        if patient_context.get("baseline_functional_status") == "dependent":
            recommendations.append("Early involvement of physical therapy for maintenance")
            recommendations.append("Consider rehabilitation medicine consultation")
        
        # Based on social support
        if patient_context.get("social_support") == "limited":
            recommendations.append("Early case management for discharge planning")
            recommendations.append("Evaluate for support services needs")
        
        # Based on advance directives
        advance_directives = patient_context.get("advance_directives")
        if advance_directives == "full_code":
            recommendations.append("Continue aggressive care per patient preferences")
        elif advance_directives == "comfort_care_only":
            recommendations.append("Focus on symptom management and comfort measures")
        
        # Based on adjustment reasons
        for reason in context_adjustment.get("adjustment_reasons", []):
            if "admission" in reason.lower():
                recommendations.append("Consider underlying causes of readmission")
        
        if not recommendations:
            recommendations.append("Continue standard ICU care per protocols")
        
        return recommendations