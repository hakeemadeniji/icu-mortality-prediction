"""
Model Service - Handles ONNX model loading and inference
"""

import logging
import math
from typing import Dict, Any, List

MODEL_VERSION = "heuristic-v1"


class ModelService:
    """Service for managing models and inference.

    No trained ONNX weights ship with the repo yet, so :meth:`predict`
    implements a transparent, rule-based risk score (a logistic model with
    hand-set, clinically-oriented weights). It is deterministic and clearly a
    heuristic — swap it for real ONNX inference once weights are available.
    """

    def __init__(self):
        self.logger = logging.getLogger("model_service")
        self.models = {}
        self._ready = False

    async def initialize(self):
        """Initialize model service."""
        self.logger.info("Initializing Model Service...")
        # Load ONNX models here when weights are available.
        self._ready = True
        self.logger.info("Model Service initialized (model=%s)", MODEL_VERSION)

    async def list_models(self) -> List[str]:
        """List available models."""
        return ["lstm_model.onnx", "transformer_model.onnx", "fusion_model.onnx"]

    def is_ready(self) -> bool:
        """Check if service is ready."""
        return self._ready

    async def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up Model Service...")
        self._ready = False

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Score a single patient snapshot.

        ``features`` uses the camelCase keys sent by the frontend dashboard.
        Returns mortality risk, confidence, category, key factors and
        recommendations. Heuristic — not a trained/validated clinical model.
        """
        age = float(features.get("age", 65))
        hr = float(features.get("heartRate", 80))
        sbp = float(features.get("bloodPressureSystolic", 120))
        temp = float(features.get("temperature", 37.0))
        rr = float(features.get("respiratoryRate", 16))
        spo2 = float(features.get("oxygenSaturation", 98))
        sofa = float(features.get("sofaScore", 0))
        comorbid = float(features.get("comorbidityCount", 0))

        # Weighted contributions to the log-odds of in-hospital mortality.
        contributions = {
            "SOFA Score": 0.35 * sofa,
            "Age": 0.02 * max(age - 40.0, 0.0),
            "Comorbidities": 0.25 * comorbid,
            "Hypotension (SBP)": 0.9 if sbp < 90 else 0.0,
            "Hypoxemia (SpO2)": 0.6 if spo2 < 92 else 0.0,
            "Tachypnea (RR)": 0.4 if rr > 22 else 0.0,
            "Heart Rate": 0.3 if (hr > 110 or hr < 50) else 0.0,
            "Temperature": 0.3 if (temp > 38.5 or temp < 35.5) else 0.0,
        }

        z = -4.0 + sum(contributions.values())
        risk = 1.0 / (1.0 + math.exp(-z))

        # Confidence: more decisive predictions (further from 0.5) are reported
        # with higher confidence. Bounded to a sensible [0.60, 0.95] range.
        confidence = min(0.95, 0.60 + 0.70 * abs(risk - 0.5))

        if risk < 0.15:
            category = "LOW"
        elif risk < 0.40:
            category = "MODERATE"
        elif risk < 0.70:
            category = "HIGH"
        else:
            category = "CRITICAL"

        # Raw values for the key factors, for display alongside the impact.
        raw_values = {
            "SOFA Score": sofa,
            "Age": age,
            "Comorbidities": comorbid,
            "Hypotension (SBP)": sbp,
            "Hypoxemia (SpO2)": spo2,
            "Tachypnea (RR)": rr,
            "Heart Rate": hr,
            "Temperature": temp,
        }

        def impact_label(weight: float) -> str:
            if weight >= 0.6:
                return "high"
            if weight >= 0.3:
                return "moderate"
            return "low"

        key_factors = [
            {
                "factor": name,
                "value": round(raw_values[name], 1),
                "impact": impact_label(weight),
            }
            for name, weight in sorted(
                contributions.items(), key=lambda kv: kv[1], reverse=True
            )
            if weight > 0
        ][:3]

        recommendations = self._recommendations(category)

        return {
            "mortality_risk": round(risk, 3),
            "confidence": round(confidence, 3),
            "risk_category": category,
            "key_factors": key_factors,
            "recommendations": recommendations,
            "model_version": MODEL_VERSION,
        }

    @staticmethod
    def _recommendations(category: str) -> List[str]:
        base = {
            "LOW": [
                "Continue standard monitoring protocols",
                "Reassess vitals per unit routine",
            ],
            "MODERATE": [
                "Continue standard monitoring protocols",
                "Increase vital sign frequency to every 2 hours",
                "Consider early specialist consultation",
            ],
            "HIGH": [
                "Escalate to senior clinician for review",
                "Increase monitoring to hourly vitals",
                "Evaluate for ICU-level interventions",
            ],
            "CRITICAL": [
                "Immediate clinician review recommended",
                "Consider transfer to higher level of care",
                "Initiate continuous monitoring and rapid response",
            ],
        }
        return base.get(category, base["MODERATE"])