"""
Risk Assessment Agent - Comprehensive risk assessment and stratification
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from base_agents.base_agent import BaseAgent


class RiskAssessmentAgent(BaseAgent):
    """
    Agent specialized in comprehensive risk assessment and stratification.
    
    Capabilities:
    - Multidimensional risk scoring
    - Risk stratification
    - Risk trajectory analysis
    - Individualized risk communication
    """
    
    def __init__(self):
        super().__init__(
            agent_id="risk_assessment_agent",
            name="Risk Assessment Agent",
            description="Comprehensive risk assessment and stratification with AI-powered analysis"
        )
        
        # Risk dimensions
        self.risk_dimensions = {
            "physiological": {"weight": 0.4, "factors": ["sofa_score", "organ_failures", "vital_stability"]},
            "comorbidity": {"weight": 0.2, "factors": ["comorbidity_count", "severity"]},
            "age_related": {"weight": 0.15, "factors": ["age", "functional_status"]},
            "acute_severity": {"weight": 0.15, "factors": ["admission_type", "emergency_status"]},
            "treatment_intensity": {"weight": 0.1, "factors": ["ventilation", "vasopressors", "dialysis"]}
        }
        
        # Risk categories
        self.risk_categories = {
            "very_low": (0.0, 0.2),
            "low": (0.2, 0.4),
            "moderate": (0.4, 0.6),
            "high": (0.6, 0.8),
            "very_high": (0.8, 1.0)
        }
        
        # Model selection: Claude Opus for complex risk calculation
        self.model_preference = "claude-opus"
        self.model_reasoning = "Complex reasoning required for comprehensive risk assessment"

    def _initialize_capabilities(self):
        self.add_capability("multidimensional_risk_scoring")
        self.add_capability("risk_stratification")
        self.add_capability("risk_trajectory_analysis")
        self.add_capability("risk_communication")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for risk assessment."""
        return "patient_data" in input_data or "clinical_data" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive risk assessment.
        
        Args:
            input_data: Contains patient and clinical data
            
        Returns:
            Dict with risk assessment results
        """
        patient_data = input_data.get("patient_data") or input_data.get("clinical_data", {})
        
        self.logger.info("Performing comprehensive risk assessment")
        
        # Calculate multidimensional risk scores
        risk_scores = await self._calculate_multidimensional_risk(patient_data)
        
        # Stratify risk
        risk_stratification = await self._stratify_risk(risk_scores)
        
        # Analyze risk trajectory
        risk_trajectory = await self._analyze_risk_trajectory(patient_data)
        
        # Generate risk communication
        risk_communication = await self._generate_risk_communication(risk_scores, risk_stratification)
        
        return {
            "risk_scores": risk_scores,
            "risk_stratification": risk_stratification,
            "risk_trajectory": risk_trajectory,
            "risk_communication": risk_communication,
            "assessment_metadata": {
                "assessment_time": datetime.now().isoformat(),
                "model_used": self.model_preference
            }
        }
    
    async def _calculate_multidimensional_risk(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk scores across multiple dimensions."""
        dimension_scores = {}
        
        # Physiological risk
        sofa_score = patient_data.get("sofa_score", 0)
        organ_failures = patient_data.get("organ_failure_count", 0)
        vital_stability = patient_data.get("vital_stability", 0.5)  # 0-1 scale
        
        physiological_risk = (sofa_score / 24) * 0.5 + (organ_failures / 6) * 0.3 + (1 - vital_stability) * 0.2
        dimension_scores["physiological"] = round(min(physiological_risk, 1.0), 3)
        
        # Comorbidity risk
        comorbidity_count = patient_data.get("comorbidity_count", 0)
        comorbidity_severity = patient_data.get("comorbidity_severity", 0.5)  # 0-1 scale
        
        comorbidity_risk = min(comorbidity_count / 10, 1.0) * 0.6 + comorbidity_severity * 0.4
        dimension_scores["comorbidity"] = round(comorbidity_risk, 3)
        
        # Age-related risk
        age = patient_data.get("age", 65)
        functional_status = patient_data.get("functional_status", 0.5)  # 0-1 scale (1 = independent)
        
        age_risk = min(age / 90, 1.0) * 0.7 + (1 - functional_status) * 0.3
        dimension_scores["age_related"] = round(age_risk, 3)
        
        # Acute severity risk
        admission_type = patient_data.get("admission_type", "elective")
        emergency_status = patient_data.get("emergency_admission", False)
        
        acute_risk = 0.3 if admission_type == "elective" else 0.7
        if emergency_status:
            acute_risk += 0.2
        
        dimension_scores["acute_severity"] = round(min(acute_risk, 1.0), 3)
        
        # Treatment intensity risk
        ventilation = patient_data.get("mechanical_ventilation", False)
        vasopressors = patient_data.get("vasopressor_use", False)
        dialysis = patient_data.get("dialysis", False)
        
        support_level = sum([ventilation, vasopressors, dialysis])
        treatment_risk = min(support_level / 3, 1.0)
        
        dimension_scores["treatment_intensity"] = round(treatment_risk, 3)
        
        # Calculate overall risk score
        overall_risk = 0
        for dimension, score in dimension_scores.items():
            weight = self.risk_dimensions[dimension]["weight"]
            overall_risk += score * weight
        
        dimension_scores["overall"] = round(overall_risk, 3)
        
        return dimension_scores
    
    async def _stratify_risk(self, risk_scores: Dict[str, float]) -> Dict[str, Any]:
        """Stratify risk into categories."""
        overall_risk = risk_scores.get("overall", 0.5)
        
        # Determine risk category
        risk_category = "moderate"
        for category, (min_val, max_val) in self.risk_categories.items():
            if min_val <= overall_risk < max_val:
                risk_category = category
                break
        
        # Generate risk-specific recommendations
        recommendations = self._generate_category_recommendations(risk_category)
        
        return {
            "risk_category": risk_category,
            "risk_level": risk_category.replace("_", " ").title(),
            "risk_percentage": round(overall_risk * 100, 1),
            "confidence": "high" if overall_risk < 0.3 or overall_risk > 0.7 else "moderate",
            "recommendations": recommendations
        }
    
    def _generate_category_recommendations(self, risk_category: str) -> List[str]:
        """Generate recommendations based on risk category."""
        recommendations = {
            "very_low": [
                "Continue standard monitoring protocols",
                "Maintain current care plan",
                "Regular reassessment per schedule"
            ],
            "low": [
                "Standard monitoring with increased vigilance",
                "Review care plan for optimization",
                "Consider early intervention planning"
            ],
            "moderate": [
                "Increased monitoring frequency",
                "Multidisciplinary team involvement",
                "Advance care planning discussion",
                "Prepare for potential deterioration"
            ],
            "high": [
                "Intensive monitoring protocols",
                "Immediate specialist consultation",
                "Goals of care discussion",
                "Prepare family for potential outcomes"
            ],
            "very_high": [
                "Maximum intensity monitoring",
                "Continuous specialist involvement",
                "Urgent goals of care clarification",
                "Palliative care consultation",
                "Family conference recommended"
            ]
        }
        
        return recommendations.get(risk_category, ["Standard monitoring protocols"])
    
    async def _analyze_risk_trajectory(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze risk trajectory over time."""
        trajectory = {
            "current_trend": "stable",
            "predicted_direction": "stable",
            "time_to_potential_outcome": "unknown",
            "trajectory_confidence": "moderate"
        }
        
        # Analyze historical data if available
        historical_scores = patient_data.get("historical_risk_scores", [])
        if len(historical_scores) >= 2:
            recent_trend = historical_scores[-1] - historical_scores[-2]
            
            if recent_trend > 0.05:
                trajectory["current_trend"] = "worsening"
                trajectory["predicted_direction"] = "continuing_worsening"
            elif recent_trend < -0.05:
                trajectory["current_trend"] = "improving"
                trajectory["predicted_direction"] = "continuing_improvement"
            else:
                trajectory["current_trend"] = "stable"
                trajectory["predicted_direction"] = "stable"
            
            # Estimate time to potential outcome
            if trajectory["current_trend"] == "worsening":
                current_score = historical_scores[-1]
                if current_score > 0.7:
                    trajectory["time_to_potential_outcome"] = "< 24 hours"
                elif current_score > 0.5:
                    trajectory["time_to_potential_outcome"] = "24-48 hours"
                else:
                    trajectory["time_to_potential_outcome"] = "48-72 hours"
        
        # Adjust based on clinical factors
        if patient_data.get("clinical_deterioration", False):
            trajectory["current_trend"] = "worsening"
            trajectory["predicted_direction"] = "rapid_worsening"
            trajectory["time_to_potential_outcome"] = "< 12 hours"
            trajectory["trajectory_confidence"] = "high"
        
        return trajectory
    
    async def _generate_risk_communication(self, risk_scores: Dict[str, float], 
                                         risk_stratification: Dict[str, Any]) -> Dict[str, Any]:
        """Generate patient-specific risk communication."""
        risk_category = risk_stratification["risk_category"]
        overall_risk = risk_scores["overall"]
        
        # Generate clinical summary
        clinical_summary = f"Patient risk assessment indicates {risk_stratification['risk_level']} risk "
        clinical_summary += f"({risk_stratification['risk_percentage']}%). "
        
        # Highlight key risk dimensions
        high_risk_dimensions = [
            dim for dim, score in risk_scores.items() 
            if dim != "overall" and score > 0.7
        ]
        
        if high_risk_dimensions:
            clinical_summary += f"Primary risk drivers: {', '.join(high_risk_dimensions)}. "
        
        # Generate action items
        action_items = []
        
        if overall_risk > 0.7:
            action_items.append("Initiate rapid response team evaluation")
            action_items.append("Schedule urgent family conference")
            action_items.append("Review and update goals of care")
        elif overall_risk > 0.5:
            action_items.append("Increase monitoring frequency")
            action_items.append("Consult relevant specialists")
            action_items.append("Discuss prognosis with family")
        else:
            action_items.append("Continue current monitoring plan")
            action_items.append("Regular reassessment")
        
        return {
            "clinical_summary": clinical_summary,
            "key_risk_drivers": high_risk_dimensions,
            "action_items": action_items,
            "follow_up_recommendations": risk_stratification["recommendations"],
            "communication_tone": "urgent" if overall_risk > 0.7 else 
                                 "serious" if overall_risk > 0.5 else "standard"
        }