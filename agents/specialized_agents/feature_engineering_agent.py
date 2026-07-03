"""
Feature Engineering Agent - Automatic feature engineering and generation
"""

import asyncio
import logging
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
from base_agents.base_agent import BaseAgent


class FeatureEngineeringAgent(BaseAgent):
    """
    Agent specialized in automatic feature engineering and generation.
    
    Capabilities:
    - Feature generation
    - Feature selection
    - Feature transformation
    - Domain-specific feature creation
    """
    
    def __init__(self):
        super().__init__(
            agent_id="feature_engineering_agent",
            name="Feature Engineering Agent",
            description="Automatic feature engineering and generation with AI-powered analysis"
        )
        
        # Feature engineering templates
        self.feature_templates = {
            "vital_sign_combinations": [
                "shock_index", "pulse_pressure", "mean_arterial_pressure",
                "respiratory_rate_oxygen_saturation_ratio", "temperature_heart_rate_ratio"
            ],
            "lab_combinations": [
                "bun_creatinine_ratio", "anion_gap", "oxygen_saturation_gap",
                "lactate_clearance", "wbc_neutrophil_ratio"
            ],
            "temporal_features": [
                "trend_analysis", "rate_of_change", "volatility",
                "time_above_threshold", "area_under_curve"
            ],
            "interaction_features": [
                "age_comorbidity_interaction", "severity_score_interaction",
                "organ_failure_count", "support_level_interaction"
            ]
        }
        
        # Model selection: Claude Opus for complex feature generation
        self.model_preference = "claude-opus"
        self.model_reasoning = "Complex reasoning required for feature engineering"

    def _initialize_capabilities(self):
        self.add_capability("feature_generation")
        self.add_capability("feature_selection")
        self.add_capability("feature_transformation")
        self.add_capability("domain_feature_creation")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for feature engineering."""
        return "raw_features" in input_data or "base_features" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform feature engineering on input data.
        
        Args:
            input_data: Contains raw features and configuration
            
        Returns:
            Dict with engineered features
        """
        raw_features = input_data.get("raw_features") or input_data.get("base_features", {})
        config = input_data.get("config", {})
        
        self.logger.info(f"Engineering features from {len(raw_features)} raw features")
        
        # Generate vital sign combinations
        vital_features = await self._generate_vital_features(raw_features)
        
        # Generate lab combinations
        lab_features = await self._generate_lab_features(raw_features)
        
        # Generate temporal features
        temporal_features = await self._generate_temporal_features(raw_features, config)
        
        # Generate interaction features
        interaction_features = await self._generate_interaction_features(raw_features)
        
        # Select most important features
        selected_features = await self._select_features(
            {**vital_features, **lab_features, **temporal_features, **interaction_features},
            config
        )
        
        return {
            "engineered_features": selected_features,
            "feature_categories": {
                "vital_sign_combinations": vital_features,
                "lab_combinations": lab_features,
                "temporal_features": temporal_features,
                "interaction_features": interaction_features
            },
            "engineering_metadata": {
                "raw_features_count": len(raw_features),
                "engineered_features_count": len(selected_features),
                "engineering_time": datetime.now().isoformat(),
                "model_used": self.model_preference
            }
        }
    
    async def _generate_vital_features(self, raw_features: Dict[str, Any]) -> Dict[str, Any]:
        """Generate vital sign combination features."""
        engineered = {}
        
        # Shock Index (HR/SBP)
        hr = raw_features.get("heart_rate")
        sbp = raw_features.get("blood_pressure_systolic")
        if hr and sbp and sbp > 0:
            engineered["shock_index"] = round(hr / sbp, 3)
        
        # Pulse Pressure
        sbp = raw_features.get("blood_pressure_systolic")
        dbp = raw_features.get("blood_pressure_diastolic")
        if sbp and dbp:
            engineered["pulse_pressure"] = sbp - dbp
        
        # Mean Arterial Pressure
        if sbp and dbp:
            engineered["mean_arterial_pressure"] = round((sbp + 2 * dbp) / 3, 1)
        
        # Respiratory Rate/Oxygen Saturation Ratio
        rr = raw_features.get("respiratory_rate")
        spo2 = raw_features.get("oxygen_saturation")
        if rr and spo2 and spo2 > 0:
            engineered["rr_spo2_ratio"] = round(rr / spo2, 3)
        
        # Temperature/Heart Rate Ratio
        temp = raw_features.get("temperature")
        hr = raw_features.get("heart_rate")
        if temp and hr and hr > 0:
            engineered["temp_hr_ratio"] = round(temp / hr, 3)
        
        return engineered
    
    async def _generate_lab_features(self, raw_features: Dict[str, Any]) -> Dict[str, Any]:
        """Generate lab combination features."""
        engineered = {}
        
        # BUN/Creatinine Ratio
        bun = raw_features.get("bun")
        creatinine = raw_features.get("creatinine")
        if bun and creatinine and creatinine > 0:
            engineered["bun_creatinine_ratio"] = round(bun / creatinine, 1)
        
        # Anion Gap
        sodium = raw_features.get("sodium")
        potassium = raw_features.get("potassium")
        chloride = raw_features.get("chloride")
        bicarbonate = raw_features.get("bicarbonate")
        if all([sodium, potassium, chloride, bicarbonate]):
            engineered["anion_gap"] = sodium - (chloride + bicarbonate)
        
        # Lactate Clearance (if historical data available)
        lactate = raw_features.get("lactate")
        lactate_baseline = raw_features.get("lactate_baseline")
        if lactate and lactate_baseline and lactate_baseline > 0:
            engineered["lactate_clearance"] = round((lactate_baseline - lactate) / lactate_baseline, 3)
        
        return engineered
    
    async def _generate_temporal_features(self, raw_features: Dict[str, Any], 
                                        config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate temporal features."""
        engineered = {}
        
        # Check for time series data
        time_series_data = raw_features.get("time_series", {})
        
        if time_series_data:
            # Trend analysis (simplified)
            for vital_name, values in time_series_data.items():
                if isinstance(values, list) and len(values) >= 2:
                    # Calculate trend
                    trend = values[-1] - values[0]
                    engineered[f"{vital_name}_trend"] = round(trend, 3)
                    
                    # Calculate rate of change
                    if len(values) >= 3:
                        recent_change = values[-1] - values[-2]
                        engineered[f"{vital_name}_rate_of_change"] = round(recent_change, 3)
                    
                    # Calculate volatility (standard deviation)
                    if len(values) >= 2:
                        volatility = np.std(values) if len(values) > 1 else 0
                        engineered[f"{vital_name}_volatility"] = round(volatility, 3)
        
        # Length of stay feature
        icu_length_hours = raw_features.get("icu_length_hours")
        if icu_length_hours:
            engineered["icu_length_days"] = round(icu_length_hours / 24, 1)
        
        return engineered
    
    async def _generate_interaction_features(self, raw_features: Dict[str, Any]) -> Dict[str, Any]:
        """Generate interaction features."""
        engineered = {}
        
        # Age-Comorbidity Interaction
        age = raw_features.get("age")
        comorbidity_count = raw_features.get("comorbidity_count", 0)
        if age and comorbidity_count:
            engineered["age_comorbidity_interaction"] = round(age * (1 + comorbidity_count * 0.1), 1)
        
        # Severity Score Interaction
        sofa_score = raw_features.get("sofa_score")
        organ_failure_count = raw_features.get("organ_failure_count", 0)
        if sofa_score and organ_failure_count:
            engineered["severity_organ_interaction"] = round(sofa_score * (1 + organ_failure_count * 0.2), 1)
        
        # Organ Failure Count
        organ_failures = 0
        if raw_features.get("respiratory_failure"):
            organ_failures += 1
        if raw_features.get("cardiovascular_failure"):
            organ_failures += 1
        if raw_features.get("renal_failure"):
            organ_failures += 1
        if raw_features.get("hepatic_failure"):
            organ_failures += 1
        if raw_features.get("hematologic_failure"):
            organ_failures += 1
        if raw_features.get("neurologic_failure"):
            organ_failures += 1
        
        engineered["organ_failure_count"] = organ_failures
        
        # Support Level Interaction
        ventilation = raw_features.get("mechanical_ventilation", False)
        vasopressors = raw_features.get("vasopressor_use", False)
        dialysis = raw_features.get("dialysis", False)
        
        support_level = sum([ventilation, vasopressors, dialysis])
        engineered["support_level"] = support_level
        
        if sofa_score:
            engineered["support_severity_interaction"] = round(sofa_score * (1 + support_level * 0.3), 1)
        
        return engineered
    
    async def _select_features(self, engineered_features: Dict[str, Any], 
                             config: Dict[str, Any]) -> Dict[str, Any]:
        """Select most important features."""
        # Simplified feature selection based on variance and domain knowledge
        
        # Domain-important features (always include)
        important_features = [
            "shock_index", "mean_arterial_pressure", "organ_failure_count",
            "support_level", "bun_creatinine_ratio"
        ]
        
        selected = {}
        
        # Include important features if available
        for feature in important_features:
            if feature in engineered_features:
                selected[feature] = engineered_features[feature]
        
        # Include other engineered features
        for feature_name, feature_value in engineered_features.items():
            if feature_name not in selected:
                # Include if value is not None and not extreme
                if feature_value is not None and abs(feature_value) < 1000:
                    selected[feature_name] = feature_value
        
        # Apply feature limit if specified
        max_features = config.get("max_features", 50)
        if len(selected) > max_features:
            # Sort by absolute value and keep top features
            sorted_features = sorted(
                selected.items(),
                key=lambda x: abs(x[1]) if isinstance(x[1], (int, float)) else 0,
                reverse=True
            )
            selected = dict(sorted_features[:max_features])
        
        return selected