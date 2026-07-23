"""
Clinical risk API — multi-score ICU deterioration & adverse-event assessment.

POST /api/v1/risk/assess takes a bedside clinical snapshot and returns every
validated score that can be computed from it (NEWS2, qSOFA, SOFA, SIRS, CURB-65,
Shock Index, ROX, PaO2/FiO2, KDIGO AKI), plus prioritized alerts and an overall
risk level. See services/clinical_scores.py and docs/CLINICAL_SCORES.md.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pathlib import Path
import json
import logging
import uuid

from services import clinical_scores, clinical_trends
from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Append-only audit trail (traceability). Privacy-conscious: records the input
# HASH + result summary, not raw PHI. A production deployment would persist the
# full inputs in a secured, access-controlled, retention-managed store.
_AUDIT_LOG = Path(settings.LOGS_DIR) / "risk_audit.jsonl"


def _audit(entry: Dict[str, Any]) -> None:
    try:
        _AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as exc:  # audit must never break the clinical response
        logger.warning("audit write failed: %s", exc)


class ClinicalSnapshot(BaseModel):
    """Bedside snapshot. Every field is optional; each score computes from the
    subset it needs and reports what's missing. Units are noted per field."""

    model_config = ConfigDict(extra="ignore")

    # Demographics
    age: Optional[float] = Field(None, description="years")
    sex: Optional[str] = Field(None, description="'M'/'F'")

    # Vitals
    heart_rate: Optional[float] = Field(None, description="bpm")
    resp_rate: Optional[float] = Field(None, description="breaths/min")
    sbp: Optional[float] = Field(None, description="systolic BP, mmHg")
    dbp: Optional[float] = Field(None, description="diastolic BP, mmHg")
    map: Optional[float] = Field(None, description="mean arterial pressure, mmHg (derived if absent)")
    temperature: Optional[float] = Field(None, description="°C")
    spo2: Optional[float] = Field(None, description="oxygen saturation, %")
    fio2: Optional[float] = Field(None, description="fraction inspired O2 (0.21-1.0 or %)")
    on_supplemental_o2: Optional[bool] = Field(None, description="receiving supplemental O2")
    gcs: Optional[float] = Field(None, description="Glasgow Coma Scale, 3-15")
    consciousness: Optional[str] = Field(None, description="ACVPU: A/C/V/P/U")
    confusion: Optional[bool] = Field(None, description="new confusion / altered mentation")

    # Support
    mechanical_ventilation: Optional[bool] = Field(None)
    vasopressors: Optional[bool] = Field(None)

    # Labs
    wbc: Optional[float] = Field(None, description="white cells, x10³/µL")
    platelets: Optional[float] = Field(None, description="x10³/µL")
    bilirubin: Optional[float] = Field(None, description="mg/dL")
    creatinine: Optional[float] = Field(None, description="mg/dL")
    baseline_creatinine: Optional[float] = Field(None, description="mg/dL")
    bun: Optional[float] = Field(None, description="blood urea nitrogen, mg/dL")
    urea: Optional[float] = Field(None, description="urea, mmol/L")
    lactate: Optional[float] = Field(None, description="mmol/L")
    pao2: Optional[float] = Field(None, description="arterial PaO2, mmHg")
    paco2: Optional[float] = Field(None, description="arterial PaCO2, mmHg")
    arterial_ph: Optional[float] = Field(None, description="arterial pH")
    sodium: Optional[float] = Field(None, description="serum sodium, mmol/L")
    potassium: Optional[float] = Field(None, description="serum potassium, mmol/L")
    bicarbonate: Optional[float] = Field(None, description="serum HCO3, mEq/L")
    hematocrit: Optional[float] = Field(None, description="hematocrit, %")
    urine_output_ml: Optional[float] = Field(None, description="urine output, mL/24h")

    # Context (chronic health / admission — APACHE II & SAPS II)
    suspected_infection: Optional[bool] = Field(None)
    severe_comorbidity: Optional[bool] = Field(None, description="APACHE II: severe organ insufficiency / immunocompromised")
    postop_elective: Optional[bool] = Field(None, description="APACHE II: elective post-op (else nonop/emergency)")
    metastatic_cancer: Optional[bool] = Field(None)
    hematologic_malignancy: Optional[bool] = Field(None)
    aids: Optional[bool] = Field(None)
    admission_type: Optional[str] = Field(None, description="SAPS II: medical | scheduled_surgical | unscheduled_surgical")


@router.post("/assess")
async def assess_risk(snapshot: ClinicalSnapshot):
    """Compute all applicable clinical risk scores for a patient snapshot.

    The response carries traceability metadata (engine version, deterministic
    input hash, unique assessment id + timestamp) and any input-validation
    warnings, and the assessment is recorded to the audit trail.
    """
    try:
        result = clinical_scores.assess(snapshot.model_dump())
        result["assessment_id"] = str(uuid.uuid4())
        result["assessed_at"] = datetime.now(timezone.utc).isoformat()

        _audit({
            "assessment_id": result["assessment_id"],
            "assessed_at": result["assessed_at"],
            "engine_version": result["engine_version"],
            "input_hash": result["input_hash"],
            "overall_risk": result["overall_risk"],
            "computed_count": result["computed_count"],
            "n_warnings": len(result["input_warnings"]),
        })
        return result
    except Exception as e:
        logger.error(f"Risk assessment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intended-use")
async def intended_use():
    """Intended use, users, population and limitations (safety metadata)."""
    return clinical_scores.INTENDED_USE


class TrendPoint(BaseModel):
    """One timed observation in a trend series."""
    hours: float = Field(..., description="hours from the first reading")
    snapshot: ClinicalSnapshot


class TrendRequest(BaseModel):
    timepoints: List[TrendPoint] = Field(..., min_length=1, description="ordered time series")


@router.post("/trend")
async def assess_trend(req: TrendRequest):
    """Trend-based indicators over a time series (NEWS2 trajectory, lactate clearance)."""
    try:
        tps = [{"hours": tp.hours, "snapshot": tp.snapshot.model_dump()}
               for tp in req.timepoints]
        return clinical_trends.assess_trends(tps)
    except Exception as e:
        logger.error(f"Trend assessment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/catalog")
async def score_catalog():
    """List the scores in the engine and the clinical targets they predict."""
    demo: Dict[str, Any] = {}
    catalog = []
    for fn in clinical_scores._SCORERS:
        r = fn(demo)  # computable=False on empty input, but carries name/target/ref
        catalog.append({
            "key": r.key,
            "name": r.name,
            "target": r.target,
            "reference": r.reference,
        })
    return {"count": len(catalog), "scores": catalog}
