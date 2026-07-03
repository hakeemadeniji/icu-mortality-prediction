"""
Clinical Guidelines Agent - Checks compliance with clinical guidelines
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from base_agents.base_agent import BaseAgent


class ClinicalGuidelinesAgent(BaseAgent):
    """
    Agent specialized in clinical guidelines compliance checking.
    
    Capabilities:
    - Guidelines compliance assessment
    - Best practices verification
    - Protocol adherence monitoring
    - Quality improvement recommendations
    """
    
    def __init__(self):
        super().__init__(
            agent_id="clinical_guidelines_agent",
            name="Clinical Guidelines Agent",
            description="Checks compliance with clinical guidelines with AI-powered analysis"
        )
        
        # Clinical guidelines database
        self.guidelines_database = {
            "sepsis_management": {
                "antibiotic_timing": {"threshold": 60, "unit": "minutes"},
                "fluid_resuscitation": {"minimum": "30ml/kg", "timeframe": "3 hours"},
                "lactate_measurement": {"frequency": "every 2-4 hours"},
                "blood_cultures": {"timing": "before antibiotics"}
            },
            "ventilation_management": {
                "tidal_volume": {"target": "6ml/kg", "max": "8ml/kg"},
                "peep": {"minimum": 5, "unit": "cmH2O"},
                "plateau_pressure": {"maximum": 30, "unit": "cmH2O"}
            },
            "sedation_management": {
                "daily_interruption": {"required": True},
                "sedation_scale": {"required": True, "frequency": "every 4 hours"},
                "pain_assessment": {"required": True, "frequency": "every 4 hours"}
            },
            "vte_prophylaxis": {
                "assessment": {"timing": "within 24 hours"},
                "pharmacologic": {"unless_contraindicated": True}
            }
        }
        
        # Model selection: Claude Opus for complex guideline reasoning
        self.model_preference = "claude-opus"
        self.model_reasoning = "Complex clinical reasoning required for guideline compliance"

    def _initialize_capabilities(self):
        self.add_capability("guidelines_compliance")
        self.add_capability("best_practices_verification")
        self.add_capability("protocol_adherence")
        self.add_capability("quality_improvement")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for guidelines checking."""
        return "clinical_data" in input_data or "patient_care" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check compliance with clinical guidelines.
        
        Args:
            input_data: Contains clinical data and care information
            
        Returns:
            Dict with guidelines compliance results
        """
        clinical_data = input_data.get("clinical_data", {})
        patient_care = input_data.get("patient_care", {})
        condition = input_data.get("condition", "general")
        
        self.logger.info(f"Checking guidelines compliance for condition: {condition}")
        
        # Assess guidelines compliance
        compliance_assessment = await self._assess_compliance(clinical_data, patient_care, condition)
        
        # Verify best practices
        best_practices = await self._verify_best_practices(clinical_data, patient_care)
        
        # Monitor protocol adherence
        protocol_adherence = await self._monitor_adherence(clinical_data, patient_care)
        
        # Generate quality improvement recommendations
        quality_recommendations = await self._generate_recommendations(compliance_assessment, best_practices)
        
        return {
            "compliance_assessment": compliance_assessment,
            "best_practices": best_practices,
            "protocol_adherence": protocol_adherence,
            "quality_recommendations": quality_recommendations,
            "guidelines_metadata": {
                "condition": condition,
                "assessment_time": datetime.now().isoformat(),
                "model_used": self.model_preference
            }
        }
    
    async def _assess_compliance(self, clinical_data: Dict[str, Any], 
                                patient_care: Dict[str, Any], 
                                condition: str) -> Dict[str, Any]:
        """Assess compliance with clinical guidelines."""
        compliance_results = {}
        
        # Check sepsis guidelines if relevant
        if condition in ["sepsis", "septic_shock"] or clinical_data.get("sepsis", False):
            sepsis_guidelines = self.guidelines_database["sepsis_management"]
            
            # Antibiotic timing
            antibiotic_time = patient_care.get("antibiotic_time_minutes", 0)
            antibiotic_compliant = antibiotic_time <= sepsis_guidelines["antibiotic_timing"]["threshold"]
            
            compliance_results["sepsis"] = {
                "antibiotic_timing": {
                    "compliant": antibiotic_compliant,
                    "actual": antibiotic_time,
                    "threshold": sepsis_guidelines["antibiotic_timing"]["threshold"],
                    "unit": "minutes"
                },
                "fluid_resuscitation": {
                    "compliant": patient_care.get("fluids_given_ml", 0) >= 1000,  # Simplified
                    "actual": patient_care.get("fluids_given_ml", 0),
                    "minimum": sepsis_guidelines["fluid_resuscitation"]["minimum"]
                }
            }
        
        # Check ventilation guidelines if relevant
        if clinical_data.get("mechanical_ventilation", False):
            vent_guidelines = self.guidelines_database["ventilation_management"]
            
            tidal_volume = patient_care.get("tidal_volume_ml", 0)
            predicted_body_weight = clinical_data.get("predicted_body_weight", 70)
            tidal_volume_kg = tidal_volume / predicted_body_weight if predicted_body_weight > 0 else 0
            
            compliance_results["ventilation"] = {
                "tidal_volume": {
                    "compliant": 4 <= tidal_volume_kg <= 8,
                    "actual_ml_kg": round(tidal_volume_kg, 1),
                    "target": vent_guidelines["tidal_volume"]["target"]
                }
            }
        
        # Calculate overall compliance score
        all_checks = []
        for category, checks in compliance_results.items():
            for check_name, check_data in checks.items():
                if isinstance(check_data, dict) and "compliant" in check_data:
                    all_checks.append(check_data["compliant"])
        
        overall_compliance = sum(all_checks) / len(all_checks) if all_checks else 0
        
        return {
            "category_compliance": compliance_results,
            "overall_compliance_score": round(overall_compliance, 2),
            "compliance_level": "high" if overall_compliance >= 0.8 else 
                              "moderate" if overall_compliance >= 0.6 else "low"
        }
    
    async def _verify_best_practices(self, clinical_data: Dict[str, Any], 
                                    patient_care: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verify best practices adherence."""
        best_practices = []
        
        # Check for daily sedation interruption
        if clinical_data.get("mechanical_ventilation", False):
            daily_sedation_interruption = patient_care.get("daily_sedation_interruption", False)
            best_practices.append({
                "practice": "Daily sedation interruption",
                "adherent": daily_sedation_interruption,
                "importance": "high",
                "evidence": "Reduces ventilation duration"
            })
        
        # Check for VTE prophylaxis
        vte_prophylaxis = patient_care.get("vte_prophylaxis", False)
        best_practices.append({
            "practice": "VTE prophylaxis",
            "adherent": vte_prophylaxis,
            "importance": "high",
            "evidence": "Prevents venous thromboembolism"
        })
        
        # Check for stress ulcer prophylaxis
        stress_ulcer_prophylaxis = patient_care.get("stress_ulcer_prophylaxis", False)
        best_practices.append({
            "practice": "Stress ulcer prophylaxis",
            "adherent": stress_ulcer_prophylaxis,
            "importance": "moderate",
            "evidence": "Prevents GI bleeding"
        })
        
        return best_practices
    
    async def _monitor_adherence(self, clinical_data: Dict[str, Any], 
                                patient_care: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor protocol adherence."""
        adherence_score = 0.7  # Base adherence
        adherence_factors = []
        
        # Check documentation completeness
        required_documentation = ["admission_note", "daily_progress", "medication_reconciliation"]
        documented = [doc for doc in required_documentation if patient_care.get(doc, False)]
        documentation_adherence = len(documented) / len(required_documentation)
        
        adherence_factors.append({
            "factor": "documentation_completeness",
            "adherence": round(documentation_adherence, 2),
            "impact": "moderate"
        })
        
        # Check timing adherence
        timely_assessments = patient_care.get("timely_assessments", True)
        adherence_factors.append({
            "factor": "timely_assessments",
            "adherence": timely_assessments,
            "impact": "high"
        })
        
        # Calculate overall adherence
        adherence_score = (documentation_adherence + (1.0 if timely_assessments else 0.7)) / 2
        
        return {
            "overall_adherence": round(adherence_score, 2),
            "adherence_factors": adherence_factors,
            "adherence_level": "high" if adherence_score >= 0.8 else 
                             "moderate" if adherence_score >= 0.6 else "low"
        }
    
    async def _generate_recommendations(self, compliance_assessment: Dict[str, Any], 
                                      best_practices: List[Dict[str, Any]]) -> List[str]:
        """Generate quality improvement recommendations."""
        recommendations = []
        
        # Check for non-compliant areas
        if compliance_assessment.get("overall_compliance_score", 1.0) < 0.8:
            recommendations.append("Review and improve guideline compliance for identified deficiencies")
        
        # Check for best practice gaps
        non_adherent_practices = [bp for bp in best_practices if not bp.get("adherent", False)]
        for practice in non_adherent_practices:
            if practice.get("importance") == "high":
                recommendations.append(f"Implement {practice['practice']} - {practice.get('evidence', '')}")
        
        # General recommendations
        if compliance_assessment.get("compliance_level") == "low":
            recommendations.append("Consider implementing clinical decision support for guideline reminders")
            recommendations.append("Provide education on current clinical guidelines")
        
        if not recommendations:
            recommendations.append("Continue current practices - good guideline adherence observed")
        
        return recommendations