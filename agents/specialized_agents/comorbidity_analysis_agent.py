"""
Comorbidity Analysis Agent - Analyzes comorbidities and their interactions
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from base_agents.base_agent import BaseAgent


class ComorbidityAnalysisAgent(BaseAgent):
    """
    Agent specialized in comorbidity analysis.
    
    Capabilities:
    - Comorbidity interaction assessment
    - Risk stratification based on comorbidities
    - Comorbidity-ICU outcome correlation
    - Multimorbidity index calculation
    """
    
    def __init__(self):
        super().__init__(
            agent_id="comorbidity_analysis_agent",
            name="Comorbidity Analysis Agent",
            description="Analyzes comorbidities and their interactions with AI-powered insights"
        )
        
        # Common comorbidities and their ICU risk weights
        self.comorbidity_risk_weights = {
            "heart_failure": 0.8,
            "chronic_kidney_disease": 0.7,
            "copd": 0.6,
            "diabetes": 0.5,
            "cancer": 0.9,
            "liver_disease": 0.8,
            "stroke": 0.7,
            "hypertension": 0.3,
            "coronary_artery_disease": 0.6,
            "obesity": 0.4,
            "immunocompromised": 0.8
        }
        
        # Comorbidity interactions
        self.comorbidity_interactions = {
            ("heart_failure", "chronic_kidney_disease"): "Cardiorenal syndrome - significantly worse outcomes",
            ("diabetes", "chronic_kidney_disease"): "Diabetic nephropathy progression",
            ("copd", "heart_failure"): "Combined cardiopulmonary compromise",
            ("cancer", "immunocompromised"): "Severe infection risk"
        }
        
        # Model selection: Claude Opus for complex comorbidity reasoning
        self.model_preference = "claude-opus"
        self.model_reasoning = "Complex medical reasoning required for comorbidity interactions"

    def _initialize_capabilities(self):
        self.add_capability("comorbidity_interaction_assessment")
        self.add_capability("risk_stratification")
        self.add_capability("outcome_correlation")
        self.add_capability("multimorbidity_index")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for comorbidity analysis."""
        return "comorbidities" in input_data or "diagnoses" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze comorbidities and provide insights.
        
        Args:
            input_data: Contains comorbidity information
            
        Returns:
            Dict with comorbidity analysis results
        """
        comorbidities = input_data.get("comorbidities") or input_data.get("diagnoses", [])
        
        self.logger.info(f"Analyzing {len(comorbidities)} comorbidities")
        
        # Assess comorbidity interactions
        interactions = await self._assess_interactions(comorbidities)
        
        # Calculate risk stratification
        risk_stratification = await self._calculate_risk_stratification(comorbidities)
        
        # Correlate with ICU outcomes
        outcome_correlation = await self._correlate_outcomes(comorbidities)
        
        # Calculate multimorbidity index
        multimorbidity_index = await self._calculate_multimorbidity_index(comorbidities)
        
        return {
            "interactions": interactions,
            "risk_stratification": risk_stratification,
            "outcome_correlation": outcome_correlation,
            "multimorbidity_index": multimorbidity_index,
            "analysis_metadata": {
                "comorbidities_analyzed": len(comorbidities),
                "analysis_time": datetime.now().isoformat(),
                "model_used": self.model_preference
            }
        }
    
    async def _assess_interactions(self, comorbidities: List[str]) -> List[Dict[str, Any]]:
        """Assess interactions between comorbidities."""
        detected_interactions = []
        
        for (comorb1, comorb2), interaction in self.comorbidity_interactions.items():
            if comorb1 in comorbidities and comorb2 in comorbidities:
                detected_interactions.append({
                    "comorbidities": [comorb1, comorb2],
                    "interaction": interaction,
                    "severity": "high",
                    "clinical_impact": "Significantly increases ICU mortality risk"
                })
        
        return detected_interactions
    
    async def _calculate_risk_stratification(self, comorbidities: List[str]) -> Dict[str, Any]:
        """Calculate risk stratification based on comorbidities."""
        total_risk = 0.0
        risk_factors = []
        
        for comorbidity in comorbidities:
            if comorbidity in self.comorbidity_risk_weights:
                weight = self.comorbidity_risk_weights[comorbidity]
                total_risk += weight
                risk_factors.append({
                    "comorbidity": comorbidity,
                    "risk_weight": weight,
                    "contribution": "high" if weight >= 0.7 else "moderate" if weight >= 0.5 else "low"
                })
        
        # Determine risk category
        risk_category = "low"
        if total_risk >= 2.0:
            risk_category = "high"
        elif total_risk >= 1.0:
            risk_category = "moderate"
        
        return {
            "total_risk_score": round(total_risk, 2),
            "risk_category": risk_category,
            "risk_factors": risk_factors
        }
    
    async def _correlate_outcomes(self, comorbidities: List[str]) -> Dict[str, Any]:
        """Correlate comorbidities with ICU outcomes."""
        correlations = []
        
        for comorbidity in comorbidities:
            if comorbidity in self.comorbidity_risk_weights:
                weight = self.comorbidity_risk_weights[comorbidity]
                
                # Simplified outcome correlation
                if weight >= 0.8:
                    outcome_impact = "significantly increased mortality risk"
                elif weight >= 0.6:
                    outcome_impact = "moderately increased mortality risk"
                else:
                    outcome_impact = "mildly increased mortality risk"
                
                correlations.append({
                    "comorbidity": comorbidity,
                    "outcome_impact": outcome_impact,
                    "icu_los_increase": f"+{weight * 2:.1f} days",
                    "ventilation_risk": "increased" if weight >= 0.6 else "slightly increased"
                })
        
        return {"correlations": correlations}
    
    async def _calculate_multimorbidity_index(self, comorbidities: List[str]) -> Dict[str, Any]:
        """Calculate multimorbidity index."""
        index_score = len(comorbidities) * 0.1
        
        # Add weight for high-risk comorbidities
        for comorbidity in comorbidities:
            if comorbidity in self.comorbidity_risk_weights:
                index_score += self.comorbidity_risk_weights[comorbidity] * 0.2
        
        return {
            "multimorbidity_index": round(min(index_score, 3.0), 2),
            "comorbidity_count": len(comorbidities),
            "interpretation": "high multimorbidity burden" if index_score >= 2.0 else 
                             "moderate multimorbidity burden" if index_score >= 1.0 else
                             "low multimorbidity burden"
        }