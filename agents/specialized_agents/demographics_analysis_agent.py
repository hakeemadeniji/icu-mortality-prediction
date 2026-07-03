"""
Demographics Analysis Agent - Analyzes demographic factors and their impact
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from base_agents.base_agent import BaseAgent


class DemographicsAnalysisAgent(BaseAgent):
    """
    Agent specialized in demographic factor analysis.
    
    Capabilities:
    - Age-based risk assessment
    - Gender-specific considerations
    - Socioeconomic factor analysis
    - Demographic risk stratification
    """
    
    def __init__(self):
        super().__init__(
            agent_id="demographics_analysis_agent",
            name="Demographics Analysis Agent",
            description="Analyzes demographic factors and their impact on ICU outcomes"
        )
        
        # Age-based risk factors
        self.age_risk_factors = {
            "young_adult": (18, 40, 0.3),
            "middle_aged": (41, 60, 0.5),
            "older_adult": (61, 75, 0.7),
            "elderly": (76, 85, 0.9),
            "very_elderly": (86, 120, 1.2)
        }
        
        # Model selection: Claude Haiku for fast demographic processing
        self.model_preference = "claude-haiku"
        self.model_reasoning = "Fast processing of demographic data with standard risk calculations"

    def _initialize_capabilities(self):
        self.add_capability("age_risk_assessment")
        self.add_capability("gender_considerations")
        self.add_capability("socioeconomic_analysis")
        self.add_capability("demographic_stratification")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for demographics analysis."""
        return "age" in input_data or "demographics" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze demographic factors and provide insights.
        
        Args:
            input_data: Contains demographic information
            
        Returns:
            Dict with demographic analysis results
        """
        demographics = input_data.get("demographics", {})
        age = input_data.get("age") or demographics.get("age")
        gender = input_data.get("gender") or demographics.get("gender")
        
        self.logger.info(f"Analyzing demographics for age {age}, gender {gender}")
        
        # Assess age-based risk
        age_risk = await self._assess_age_risk(age)
        
        # Analyze gender considerations
        gender_considerations = await self._analyze_gender_considerations(gender)
        
        # Analyze socioeconomic factors if available
        socioeconomic_analysis = await self._analyze_socioeconomic_factors(demographics)
        
        # Calculate demographic risk score
        demographic_risk_score = await self._calculate_demographic_risk_score(age, gender, demographics)
        
        return {
            "age_risk": age_risk,
            "gender_considerations": gender_considerations,
            "socioeconomic_analysis": socioeconomic_analysis,
            "demographic_risk_score": demographic_risk_score,
            "analysis_metadata": {
                "analysis_time": datetime.now().isoformat(),
                "model_used": self.model_preference
            }
        }
    
    async def _assess_age_risk(self, age: int) -> Dict[str, Any]:
        """Assess risk based on age."""
        age_category = None
        risk_weight = 0.0
        
        for category, (min_age, max_age, weight) in self.age_risk_factors.items():
            if min_age <= age <= max_age:
                age_category = category
                risk_weight = weight
                break
        
        considerations = []
        if age >= 65:
            considerations.append("Increased physiological reserve reduction")
            considerations.append("Higher likelihood of comorbidities")
            considerations.append("Altered drug metabolism")
        if age >= 80:
            considerations.append("Significantly increased frailty risk")
            considerations.append("Higher complication rates")
        
        return {
            "age": age,
            "age_category": age_category,
            "risk_weight": risk_weight,
            "considerations": considerations
        }
    
    async def _analyze_gender_considerations(self, gender: str) -> Dict[str, Any]:
        """Analyze gender-specific considerations."""
        considerations = []
        
        if gender and gender.lower() in ["male", "m"]:
            considerations.append("Higher cardiovascular disease risk")
            considerations.append("Different drug metabolism patterns")
        elif gender and gender.lower() in ["female", "f"]:
            considerations.append("Hormonal influences on immune response")
            considerations.append("Different drug pharmacokinetics")
        
        return {
            "gender": gender,
            "considerations": considerations
        }
    
    async def _analyze_socioeconomic_factors(self, demographics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze socioeconomic factors if available."""
        factors = {}
        
        if "insurance_status" in demographics:
            insurance = demographics["insurance_status"]
            factors["insurance"] = {
                "status": insurance,
                "impact": "Access to care considerations" if insurance != "private" else "Standard access"
            }
        
        if "social_support" in demographics:
            factors["social_support"] = {
                "level": demographics["social_support"],
                "impact": "Discharge planning considerations"
            }
        
        return factors
    
    async def _calculate_demographic_risk_score(self, age: int, gender: str, demographics: Dict[str, Any]) -> float:
        """Calculate overall demographic risk score."""
        risk_score = 0.0
        
        # Age contribution
        for category, (min_age, max_age, weight) in self.age_risk_factors.items():
            if min_age <= age <= max_age:
                risk_score += weight
                break
        
        # Add small adjustments for other factors
        if demographics.get("insurance_status") != "private":
            risk_score += 0.1
        
        return round(min(risk_score, 2.0), 2)