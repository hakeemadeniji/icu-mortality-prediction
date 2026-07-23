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
import logging

from services import clinical_scores

logger = logging.getLogger(__name__)
router = APIRouter()


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

    # Context
    suspected_infection: Optional[bool] = Field(None)


@router.post("/assess")
async def assess_risk(snapshot: ClinicalSnapshot):
    """Compute all applicable clinical risk scores for a patient snapshot."""
    try:
        return clinical_scores.assess(snapshot.model_dump())
    except Exception as e:
        logger.error(f"Risk assessment error: {e}")
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
