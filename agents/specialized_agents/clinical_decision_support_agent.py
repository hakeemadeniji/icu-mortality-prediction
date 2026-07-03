"""
Clinical Decision Support Agent - Provides AI-powered clinical decision support
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from base_agents.base_agent import BaseAgent


class ClinicalDecisionSupportAgent(BaseAgent):
    """
    Agent specialized in clinical decision support.
    
    Capabilities:
    - Evidence-based recommendations
    - Treatment optimization suggestions
    - Diagnostic support
    - Clinical pathway guidance
    """
    
    def __init__(self):
        super().__init__(
            agent_id="clinical_decision_support_agent",
            name="Clinical Decision Support Agent",
            description="Provides AI-powered clinical decision support with evidence-based recommendations"
        )
        
        # Decision support categories
        self.support_categories = {
            "diagnostic": ["differential_diagnosis", "diagnostic_testing", "interpretation_assistance"],
            "therapeutic": ["treatment_selection", "dosage_optimization", "alternative_therapies"],
            "prognostic": ["outcome_prediction", "risk_stratification", "trajectory_analysis"],
            "monitoring": ["parameter_monitoring", "alert_thresholds", "surveillance_frequency"]
        }
        
        # Clinical pathways
        self.clinical_pathways = {
            "sepsis": ["antibiotics", "fluid_resuscitation", "source_control", "vasopressors", "monitoring"],
            "ards": ["lung_protective_ventilation", "prone_positioning", "fluid_strategy", "adjunctive_therapies"],
            "heart_failure": ["diuretics", "vasodilators", "inotropes", "monitoring", "device_therapy"]
        }
        
        # Model selection: Claude Opus for complex clinical reasoning
        self.model_preference = "claude-opus"
        self.model_reasoning = "Complex clinical reasoning required for decision support"

    def _initialize_capabilities(self):
        self.add_capability("evidence_based_recommendations")
        self.add_capability("treatment_optimization")
        self.add_capability("diagnostic_support")
        self.add_capability("clinical_pathway_guidance")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for clinical decision support."""
        return "clinical_scenario" in input_data or "patient_case" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide clinical decision support.
        
        Args:
            input_data: Contains clinical scenario and patient data
            
        Returns:
            Dict with decision support recommendations
        """
        clinical_scenario = input_data.get("clinical_scenario", {})
        patient_case = input_data.get("patient_case", {})
        question_type = input_data.get("question_type", "general")
        
        self.logger.info(f"Providing decision support for: {question_type}")
        
        # Generate evidence-based recommendations
        recommendations = await self._generate_recommendations(clinical_scenario, patient_case)
        
        # Optimize treatment suggestions
        treatment_optimization = await self._optimize_treatment(clinical_scenario, patient_case)
        
        # Provide diagnostic support
        diagnostic_support = await self._provide_diagnostic_support(clinical_scenario, patient_case)
        
        # Guide clinical pathways
        pathway_guidance = await self._guide_clinical_pathways(clinical_scenario)
        
        return {
            "recommendations": recommendations,
            "treatment_optimization": treatment_optimization,
            "diagnostic_support": diagnostic_support,
            "pathway_guidance": pathway_guidance,
            "support_metadata": {
                "question_type": question_type,
                "support_time": datetime.now().isoformat(),
                "model_used": self.model_preference
            }
        }
    
    async def _generate_recommendations(self, clinical_scenario: Dict[str, Any], 
                                      patient_case: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate evidence-based recommendations."""
        recommendations = []
        
        diagnosis = clinical_scenario.get("diagnosis", "").lower()
        severity = clinical_scenario.get("severity", "moderate")
        
        # Diagnosis-specific recommendations
        if "sepsis" in diagnosis:
            recommendations.append({
                "recommendation": "Administer broad-spectrum antibiotics within 1 hour",
                "evidence_level": "strong",
                "guideline": "Surviving Sepsis Campaign",
                "priority": "critical"
            })
            recommendations.append({
                "recommendation": "Administer 30 mL/kg crystalloid for initial resuscitation",
                "evidence_level": "strong",
                "guideline": "Surviving Sepsis Campaign",
                "priority": "critical"
            })
        
        elif "ards" in diagnosis or "acute_respiratory_distress" in diagnosis:
            recommendations.append({
                "recommendation": "Implement lung-protective ventilation (6 mL/kg PBW)",
                "evidence_level": "strong",
                "guideline": "ARDSNet",
                "priority": "high"
            })
            recommendations.append({
                "recommendation": "Consider prone positioning for moderate-severe ARDS",
                "evidence_level": "moderate",
                "guideline": "ARDSNet",
                "priority": "moderate"
            })
        
        # Severity-based recommendations
        if severity == "severe":
            recommendations.append({
                "recommendation": "Consider early ICU transfer for higher level of care",
                "evidence_level": "moderate",
                "guideline": "Clinical judgment",
                "priority": "high"
            })
        
        # Patient-specific recommendations
        age = patient_case.get("age", 65)
        if age >= 75:
            recommendations.append({
                "recommendation": "Consider age-appropriate treatment goals and potential limitations",
                "evidence_level": "moderate",
                "guideline": "Geriatric ICU guidelines",
                "priority": "moderate"
            })
        
        return recommendations
    
    async def _optimize_treatment(self, clinical_scenario: Dict[str, Any], 
                                patient_case: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize treatment suggestions."""
        optimization = {
            "current_treatments": [],
            "optimization_suggestions": [],
            "alternatives": [],
            "contraindications": []
        }
        
        current_medications = patient_case.get("medications", [])
        optimization["current_treatments"] = current_medications
        
        # Check for potential optimizations
        diagnosis = clinical_scenario.get("diagnosis", "").lower()
        
        if "sepsis" in diagnosis:
            # Check for appropriate antibiotic coverage
            has_antibiotics = any("antibiotic" in med.lower() for med in current_medications)
            if not has_antibiotics:
                optimization["optimization_suggestions"].append({
                    "area": "antibiotic_therapy",
                    "suggestion": "Initiate appropriate empiric antibiotics",
                    "reason": "Delayed antibiotic therapy increases mortality"
                })
            
            # Check for vasopressor need
            if patient_case.get("blood_pressure_systolic", 120) < 90:
                optimization["optimization_suggestions"].append({
                    "area": "hemodynamic_support",
                    "suggestion": "Consider vasopressor support",
                    "reason": "Persistent hypotension despite fluid resuscitation"
                })
        
        # Check for contraindications
        renal_function = patient_case.get("creatinine", 1.0)
        if renal_function > 2.0:
            optimization["contraindications"].append({
                "medication_class": "nephrotoxic_agents",
                "reason": "Elevated creatinine suggests renal impairment",
                "alternative": "Consider renally-dosed alternatives"
            })
        
        return optimization
    
    async def _provide_diagnostic_support(self, clinical_scenario: Dict[str, Any], 
                                        patient_case: Dict[str, Any]) -> Dict[str, Any]:
        """Provide diagnostic support."""
        diagnostic_support = {
            "differential_diagnosis": [],
            "recommended_tests": [],
            "interpretation_assistance": []
        }
        
        symptoms = clinical_scenario.get("symptoms", [])
        vital_signs = patient_case.get("vital_signs", {})
        
        # Generate differential diagnosis based on presentation
        if "fever" in symptoms and vital_signs.get("temperature", 37) > 38.3:
            diagnostic_support["differential_diagnosis"].extend([
                "Sepsis", "Infectious process", "Inflammatory response"
            ])
        
        if "shortness_of_breath" in symptoms:
            diagnostic_support["differential_diagnosis"].extend([
                "Pneumonia", "Pulmonary embolism", "Heart failure", "ARDS"
            ])
        
        # Recommended diagnostic tests
        if "sepsis" in clinical_scenario.get("diagnosis", "").lower():
            diagnostic_support["recommended_tests"].extend([
                {"test": "blood_cultures", "timing": "before antibiotics", "priority": "high"},
                {"test": "lactate", "timing": "immediate", "priority": "high"},
                {"test": "cbc_with_diff", "timing": "immediate", "priority": "high"},
                {"test": "basic_metabolic_panel", "timing": "immediate", "priority": "high"}
            ])
        
        # Interpretation assistance
        lab_values = patient_case.get("lab_values", {})
        if lab_values.get("lactate", 0) > 4:
            diagnostic_support["interpretation_assistance"].append({
                "lab": "lactate",
                "value": lab_values.get("lactate"),
                "interpretation": "Severe lactic acidosis - indicates tissue hypoperfusion",
                "clinical_significance": "high"
            })
        
        return diagnostic_support
    
    async def _guide_clinical_pathways(self, clinical_scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Guide clinical pathways based on diagnosis."""
        diagnosis = clinical_scenario.get("diagnosis", "").lower()
        pathway_guidance = {
            "recommended_pathway": None,
            "pathway_steps": [],
            "milestones": [],
            "deviations": []
        }
        
        # Identify appropriate pathway
        for pathway_name, conditions in self.clinical_pathways.items():
            if pathway_name in diagnosis:
                pathway_guidance["recommended_pathway"] = pathway_name
                pathway_guidance["pathway_steps"] = conditions
                break
        
        # Generate milestones
        if pathway_guidance["recommended_pathway"] == "sepsis":
            pathway_guidance["milestones"] = [
                {"milestone": "time_to_antibiotics", "target": "< 60 minutes"},
                {"milestone": "time_to_fluids", "target": "< 180 minutes"},
                {"milestone": "lactate_clearance", "target": "> 10% decrease at 6 hours"}
            ]
        
        elif pathway_guidance["recommended_pathway"] == "ards":
            pathway_guidance["milestones"] = [
                {"milestone": "tidal_volume_achievement", "target": "≤ 6 mL/kg PBW"},
                {"milestone": "plateau_pressure", "target": "< 30 cmH2O"},
                {"milestone": "oxygenation_target", "target": "SpO2 88-92% or PaO2 55-80 mmHg"}
            ]
        
        # Check for potential deviations
        current_status = clinical_scenario.get("current_status", {})
        if current_status.get("antibiotic_delay", 0) > 60:
            pathway_guidance["deviations"].append({
                "deviation": "antibiotic_delay",
                "severity": "high",
                "impact": "Increased mortality risk",
                "correction": "Document reason and consider quality improvement"
            })
        
        return pathway_guidance