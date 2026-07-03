"""
Data Quality Agent - Validates and ensures data quality
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from base_agents.base_agent import BaseAgent


class DataQualityAgent(BaseAgent):
    """
    Agent specialized in data validation and quality assurance.
    
    Capabilities:
    - Data completeness validation
    - Outlier detection
    - Consistency checking
    - Data quality scoring
    """
    
    def __init__(self):
        super().__init__(
            agent_id="data_quality_agent",
            name="Data Quality Agent",
            description="Validates and ensures data quality with AI-powered analysis"
        )
        
        # Data quality thresholds
        self.quality_thresholds = {
            "completeness": 0.8,
            "validity": 0.9,
            "consistency": 0.85,
            "overall_quality": 0.8
        }
        
        # Valid ranges for common clinical values
        self.valid_ranges = {
            "age": (0, 120),
            "heart_rate": (0, 300),
            "blood_pressure_systolic": (0, 300),
            "blood_pressure_diastolic": (0, 200),
            "temperature": (20, 45),
            "respiratory_rate": (0, 60),
            "oxygen_saturation": (0, 100),
            "glucose": (0, 1000),
            "creatinine": (0, 20),
            "sodium": (100, 200),
            "potassium": (0, 10)
        }
        
        # Model selection: GLM for efficient data validation
        self.model_preference = "glm"
        self.model_reasoning = "Efficient data validation and quality assessment"

    def _initialize_capabilities(self):
        self.add_capability("completeness_validation")
        self.add_capability("outlier_detection")
        self.add_capability("consistency_checking")
        self.add_capability("quality_scoring")
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for data quality assessment."""
        return "data" in input_data or "patient_data" in input_data
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and assess data quality.
        
        Args:
            input_data: Contains data to be validated
            
        Returns:
            Dict with data quality assessment results
        """
        data = input_data.get("data") or input_data.get("patient_data", {})
        
        self.logger.info(f"Assessing data quality for {len(data)} fields")
        
        # Validate data completeness
        completeness = await self._validate_completeness(data)
        
        # Detect outliers
        outliers = await self._detect_outliers(data)
        
        # Check consistency
        consistency = await self._check_consistency(data)
        
        # Calculate overall quality score
        quality_score = await self._calculate_quality_score(completeness, outliers, consistency)
        
        # Generate data quality report
        quality_report = await self._generate_quality_report(completeness, outliers, consistency, quality_score)
        
        return {
            "completeness": completeness,
            "outliers": outliers,
            "consistency": consistency,
            "quality_score": quality_score,
            "quality_report": quality_report,
            "quality_metadata": {
                "fields_assessed": len(data),
                "assessment_time": datetime.now().isoformat(),
                "model_used": self.model_preference
            }
        }
    
    async def _validate_completeness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data completeness."""
        total_fields = len(data)
        missing_fields = []
        empty_fields = []
        
        for field_name, field_value in data.items():
            if field_value is None:
                missing_fields.append(field_name)
            elif field_value == "" or (isinstance(field_value, list) and len(field_value) == 0):
                empty_fields.append(field_name)
        
        missing_count = len(missing_fields) + len(empty_fields)
        completeness_ratio = (total_fields - missing_count) / total_fields if total_fields > 0 else 0
        
        return {
            "total_fields": total_fields,
            "missing_fields": missing_fields,
            "empty_fields": empty_fields,
            "completeness_ratio": round(completeness_ratio, 3),
            "threshold_met": completeness_ratio >= self.quality_thresholds["completeness"]
        }
    
    async def _detect_outliers(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect outliers in the data."""
        detected_outliers = []
        
        for field_name, field_value in data.items():
            if field_name in self.valid_ranges and isinstance(field_value, (int, float)):
                min_val, max_val = self.valid_ranges[field_name]
                
                if field_value < min_val or field_value > max_val:
                    detected_outliers.append({
                        "field": field_name,
                        "value": field_value,
                        "valid_range": (min_val, max_val),
                        "severity": "high" if field_value < min_val * 0.5 or field_value > max_val * 1.5 else "moderate"
                    })
        
        return {
            "outlier_count": len(detected_outliers),
            "outliers": detected_outliers,
            "outlier_ratio": round(len(detected_outliers) / len(data), 3) if data else 0
        }
    
    async def _check_consistency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check data consistency."""
        consistency_issues = []
        
        # Check blood pressure consistency
        if "blood_pressure_systolic" in data and "blood_pressure_diastolic" in data:
            sbp = data["blood_pressure_systolic"]
            dbp = data["blood_pressure_diastolic"]
            
            if isinstance(sbp, (int, float)) and isinstance(dbp, (int, float)):
                if dbp >= sbp:
                    consistency_issues.append({
                        "type": "logical_inconsistency",
                        "description": "Diastolic pressure cannot be higher than systolic",
                        "fields": ["blood_pressure_systolic", "blood_pressure_diastolic"]
                    })
                elif (sbp - dbp) < 20:
                    consistency_issues.append({
                        "type": "physiological_unlikely",
                        "description": "Pulse pressure unusually narrow",
                        "fields": ["blood_pressure_systolic", "blood_pressure_diastolic"]
                    })
        
        # Check MAP consistency
        if "blood_pressure_systolic" in data and "blood_pressure_diastolic" in data:
            sbp = data.get("blood_pressure_systolic")
            dbp = data.get("blood_pressure_diastolic")
            if isinstance(sbp, (int, float)) and isinstance(dbp, (int, float)):
                calculated_map = (sbp + 2 * dbp) / 3
                if "mean_arterial_pressure" in data:
                    reported_map = data["mean_arterial_pressure"]
                    if isinstance(reported_map, (int, float)):
                        if abs(calculated_map - reported_map) > 10:
                            consistency_issues.append({
                                "type": "calculation_discrepancy",
                                "description": f"MAP discrepancy: calculated {calculated_map:.1f}, reported {reported_map}",
                                "fields": ["mean_arterial_pressure", "blood_pressure_systolic", "blood_pressure_diastolic"]
                            })
        
        # Check age-related consistency
        if "age" in data:
            age = data["age"]
            if isinstance(age, (int, float)):
                if age < 0 or age > 120:
                    consistency_issues.append({
                        "type": "value_out_of_range",
                        "description": f"Age {age} outside valid range",
                        "fields": ["age"]
                    })
        
        consistency_ratio = 1.0 - (len(consistency_issues) / max(len(data), 1))
        
        return {
            "consistency_issues": consistency_issues,
            "consistency_ratio": round(consistency_ratio, 3),
            "threshold_met": consistency_ratio >= self.quality_thresholds["consistency"]
        }
    
    async def _calculate_quality_score(self, completeness: Dict[str, Any], 
                                     outliers: Dict[str, Any], 
                                     consistency: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall data quality score."""
        completeness_score = completeness["completeness_ratio"]
        consistency_score = consistency["consistency_ratio"]
        outlier_penalty = outliers["outlier_ratio"] * 0.5
        
        overall_score = (completeness_score + consistency_score) / 2 - outlier_penalty
        overall_score = max(0.0, min(1.0, overall_score))
        
        return {
            "overall_score": round(overall_score, 3),
            "completeness_score": completeness_score,
            "consistency_score": consistency_score,
            "outlier_penalty": round(outlier_penalty, 3),
            "threshold_met": overall_score >= self.quality_thresholds["overall_quality"],
            "quality_level": "high" if overall_score >= 0.8 else 
                           "moderate" if overall_score >= 0.6 else "low"
        }
    
    async def _generate_quality_report(self, completeness: Dict[str, Any], 
                                     outliers: Dict[str, Any], 
                                     consistency: Dict[str, Any],
                                     quality_score: Dict[str, Any]) -> str:
        """Generate data quality report."""
        report = f"Data Quality Assessment - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Overall Quality Score: {quality_score['overall_score']:.2%} ({quality_score['quality_level']})\n"
        report += f"Completeness: {completeness['completeness_ratio']:.2%}\n"
        report += f"Consistency: {consistency['consistency_ratio']:.2%}\n"
        report += f"Outliers Detected: {outliers['outlier_count']}\n"
        
        if completeness["missing_fields"]:
            report += f"Missing Fields: {', '.join(completeness['missing_fields'][:5])}\n"
        
        if consistency["consistency_issues"]:
            report += f"Consistency Issues: {len(consistency['consistency_issues'])}\n"
        
        if quality_score["quality_level"] == "low":
            report += "Recommendation: Data quality improvements needed before analysis"
        elif quality_score["quality_level"] == "moderate":
            report += "Recommendation: Address missing fields and outliers for improved accuracy"
        else:
            report += "Recommendation: Data quality is acceptable for analysis"
        
        return report