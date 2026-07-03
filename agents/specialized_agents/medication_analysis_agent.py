"""
Medication Analysis Agent - Analyzes medication impacts and interactions
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from base_agents.base_agent import BaseAgent


class MedicationAnalysisAgent(BaseAgent):
    """
    Agent specialized in medication analysis.
    
    Capabilities:
    - Drug interaction detection
    - Medication impact assessment
    - Adverse effect prediction
    - Dosage optimization recommendations
    """
    
    def __init__(self):
        super().__init__(
            agent_id="medication_analysis_agent",
            name="Medication Analysis Agent",
            description="Analyzes medication impacts and interactions with AI-powered insights"
        )
        
        # Common drug classes and their effects
        self.drug_classes = {
            "anticoagulants": ["heparin", "warfarin", "enoxaparin", "dabigatran"],
            "antiplatelets": ["aspirin", "clopidogrel", "ticagrelor"],
            "vasopressors": ["norepinephrine", "epinephrine", "dopamine", "vasopressin"],
            "antibiotics": ["vancomycin", "meropenem", "piperacillin", "cefepime"],
            "sedatives": ["propofol", "midazolam", "fentanyl", "dexmedetomidine"],
            "diuretics": ["furosemide", "bumetanide", "torsemide"]
        }
        
        # Known drug interactions
        self.drug_interactions = {
            ("heparin", "aspirin"): "Increased bleeding risk",
            ("warfarin", "antibiotics"): "Increased INR/elevated bleeding risk",
            ("norepinephrine", "beta_blockers"): "Decreased vasopressor effectiveness",
            ("furosemide", "gentamicin"): "Increased nephrotoxicity risk"
        }
        
        # Model selection: Claude Opus for complex medication reasoning
        self.model_preference = "claude-opus"
        self.model_reasoning = "Complex medication interaction analysis and clinical reasoning required"

    def _initialize_capabilities(self):
        self.add_capability("drug_interaction_detection")
        self.add_capability("medication_impact_assessment")
        self.add_capability("adverse_effect_prediction")
        self.add_capability("dosage_optimization")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for medication analysis."""
        return "medications" in input_data or "drugs" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze medications and provide insights.
        
        Args:
            input_data: Contains medication information
            
        Returns:
            Dict with medication analysis results
        """
        medications = input_data.get("medications") or input_data.get("drugs", [])
        
        self.logger.info(f"Analyzing {len(medications)} medications")
        
        # Detect drug interactions
        interactions = await self._detect_interactions(medications)
        
        # Assess medication impacts
        impacts = await self._assess_medication_impacts(medications)
        
        # Predict adverse effects
        adverse_effects = await self._predict_adverse_effects(medications)
        
        # Generate dosage recommendations
        dosage_recommendations = await self._generate_dosage_recommendations(medications)
        
        # Calculate medication complexity score
        complexity_score = await self._calculate_complexity_score(medications)
        
        return {
            "interactions": interactions,
            "medication_impacts": impacts,
            "adverse_effects": adverse_effects,
            "dosage_recommendations": dosage_recommendations,
            "complexity_score": complexity_score,
            "analysis_metadata": {
                "medications_analyzed": len(medications),
                "analysis_time": datetime.now().isoformat(),
                "model_used": self.model_preference
            }
        }
    
    async def _detect_interactions(self, medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect potential drug interactions."""
        detected_interactions = []
        medication_names = [med.get("name", "").lower() for med in medications]
        
        for (drug1, drug2), interaction in self.drug_interactions.items():
            if drug1 in medication_names and drug2 in medication_names:
                detected_interactions.append({
                    "drugs": [drug1, drug2],
                    "interaction": interaction,
                    "severity": "moderate",
                    "recommendation": "Monitor closely for adverse effects"
                })
        
        return detected_interactions
    
    async def _assess_medication_impacts(self, medications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess the impact of medications on patient condition."""
        impacts = {
            "cardiovascular": [],
            "renal": [],
            "respiratory": [],
            "hematologic": [],
            "neurologic": []
        }
        
        for med in medications:
            med_name = med.get("name", "").lower()
            
            # Categorize by system impact
            if any(vasopressor in med_name for vasopressor in self.drug_classes["vasopressors"]):
                impacts["cardiovascular"].append(f"{med_name}: Hemodynamic support")
            if any(diuretic in med_name for diuretic in self.drug_classes["diuretics"]):
                impacts["renal"].append(f"{med_name}: Fluid balance modulation")
            if any(anticoagulant in med_name for anticoagulant in self.drug_classes["anticoagulants"]):
                impacts["hematologic"].append(f"{med_name}: Anticoagulation effect")
            if any(sedative in med_name for sedative in self.drug_classes["sedatives"]):
                impacts["neurologic"].append(f"{med_name}: Sedation effects")
        
        return impacts
    
    async def _predict_adverse_effects(self, medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Predict potential adverse effects."""
        adverse_effects = []
        
        for med in medications:
            med_name = med.get("name", "").lower()
            
            # Common adverse effects by drug class
            if any(vasopressor in med_name for vasopressor in self.drug_classes["vasopressors"]):
                adverse_effects.append({
                    "medication": med_name,
                    "effect": "Tissue ischemia, arrhythmias",
                    "likelihood": "moderate",
                    "monitoring": "Peripheral perfusion, ECG"
                })
            elif any(antibiotic in med_name for antibiotic in self.drug_classes["antibiotics"]):
                adverse_effects.append({
                    "medication": med_name,
                    "effect": "Nephrotoxicity, ototoxicity",
                    "likelihood": "low",
                    "monitoring": "Renal function, auditory symptoms"
                })
            elif any(anticoagulant in med_name for anticoagulant in self.drug_classes["anticoagulants"]):
                adverse_effects.append({
                    "medication": med_name,
                    "effect": "Bleeding complications",
                    "likelihood": "moderate",
                    "monitoring": "Coagulation studies, signs of bleeding"
                })
        
        return adverse_effects
    
    async def _generate_dosage_recommendations(self, medications: List[Dict[str, Any]]) -> List[str]:
        """Generate dosage optimization recommendations."""
        recommendations = []
        
        for med in medications:
            med_name = med.get("name", "").lower()
            dosage = med.get("dosage", "")
            
            # Simplified dosage recommendations
            if "renal" in med.get("contraindications", "").lower():
                recommendations.append(f"Consider renal dose adjustment for {med_name}")
            
            if "hepatic" in med.get("contraindications", "").lower():
                recommendations.append(f"Consider hepatic dose adjustment for {med_name}")
            
            if not dosage:
                recommendations.append(f"Verify dosage for {med_name}")
        
        return recommendations
    
    async def _calculate_complexity_score(self, medications: List[Dict[str, Any]]) -> float:
        """Calculate medication regimen complexity score."""
        complexity = len(medications) * 0.1
        
        # Add complexity for high-risk medications
        high_risk_classes = ["anticoagulants", "vasopressors", "antiplatelets"]
        for med in medications:
            med_name = med.get("name", "").lower()
            for drug_class, drugs in self.drug_classes.items():
                if drug_class in high_risk_classes and any(drug in med_name for drug in drugs):
                    complexity += 0.2
        
        return round(min(complexity, 2.0), 2)