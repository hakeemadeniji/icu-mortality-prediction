-- ============================================================
-- MIMIC-IV Diagnoses, Comorbidities & Acuity Scores
-- ============================================================
-- Extracts ICD diagnoses, computes Elixhauser comorbidity
-- flags, and gathers SOFA/SAPS scores for the cohort.
-- ============================================================

-- ── Step 1: ICD diagnoses per admission ─────────────────────

DROP TABLE IF EXISTS mimiciv_derived.diagnoses;
CREATE TABLE mimiciv_derived.diagnoses AS

SELECT
    co.subject_id,
    co.hadm_id,
    co.stay_id,
    d.icd_code,
    d.icd_version,
    d.seq_num,
    di.long_title AS diagnosis_description
FROM mimiciv_hosp.diagnoses_icd d
INNER JOIN mimiciv_derived.cohort co
    ON d.subject_id = co.subject_id
    AND d.hadm_id = co.hadm_id
LEFT JOIN mimiciv_hosp.d_icd_diagnoses di
    ON d.icd_code = di.icd_code
    AND d.icd_version = di.icd_version
ORDER BY co.subject_id, d.seq_num;


-- ── Step 2: Elixhauser comorbidity flags ────────────────────
-- Simplified binary flags for the most clinically impactful
-- comorbidities. Uses ICD-10 codes (version 10).

DROP TABLE IF EXISTS mimiciv_derived.comorbidities;
CREATE TABLE mimiciv_derived.comorbidities AS

SELECT
    co.subject_id,
    co.hadm_id,
    co.stay_id,
    -- Cardiovascular
    MAX(CASE WHEN d.icd_code LIKE 'I50%' THEN 1 ELSE 0 END)   AS chf,
    MAX(CASE WHEN d.icd_code LIKE 'I48%' THEN 1 ELSE 0 END)   AS atrial_fibrillation,
    MAX(CASE WHEN d.icd_code LIKE 'I10%'
             OR d.icd_code LIKE 'I11%'
             OR d.icd_code LIKE 'I12%'
             OR d.icd_code LIKE 'I13%' THEN 1 ELSE 0 END)     AS hypertension,
    -- Pulmonary
    MAX(CASE WHEN d.icd_code LIKE 'J44%'
             OR d.icd_code LIKE 'J43%' THEN 1 ELSE 0 END)     AS copd,
    MAX(CASE WHEN d.icd_code LIKE 'J45%' THEN 1 ELSE 0 END)   AS asthma,
    -- Metabolic
    MAX(CASE WHEN d.icd_code LIKE 'E11%'
             OR d.icd_code LIKE 'E10%'
             OR d.icd_code LIKE 'E13%' THEN 1 ELSE 0 END)     AS diabetes,
    MAX(CASE WHEN d.icd_code LIKE 'E78%' THEN 1 ELSE 0 END)   AS hyperlipidemia,
    MAX(CASE WHEN d.icd_code LIKE 'E66%' THEN 1 ELSE 0 END)   AS obesity,
    -- Renal
    MAX(CASE WHEN d.icd_code LIKE 'N18%' THEN 1 ELSE 0 END)   AS ckd,
    MAX(CASE WHEN d.icd_code LIKE 'N17%' THEN 1 ELSE 0 END)   AS aki,
    -- Hepatic
    MAX(CASE WHEN d.icd_code LIKE 'K70%'
             OR d.icd_code LIKE 'K74%' THEN 1 ELSE 0 END)     AS liver_disease,
    -- Neurologic
    MAX(CASE WHEN d.icd_code LIKE 'I63%'
             OR d.icd_code LIKE 'I61%' THEN 1 ELSE 0 END)     AS stroke,
    MAX(CASE WHEN d.icd_code LIKE 'G30%'
             OR d.icd_code LIKE 'F01%'
             OR d.icd_code LIKE 'F03%' THEN 1 ELSE 0 END)     AS dementia,
    -- Infection
    MAX(CASE WHEN d.icd_code LIKE 'A41%'
             OR d.icd_code LIKE 'R65%' THEN 1 ELSE 0 END)     AS sepsis,
    -- Cancer
    MAX(CASE WHEN d.icd_code BETWEEN 'C00' AND 'C97'
             THEN 1 ELSE 0 END)                                 AS cancer,
    -- Psychiatric
    MAX(CASE WHEN d.icd_code LIKE 'F10%'
             OR d.icd_code LIKE 'F11%'
             OR d.icd_code LIKE 'F12%'
             OR d.icd_code LIKE 'F13%'
             OR d.icd_code LIKE 'F14%'
             OR d.icd_code LIKE 'F19%' THEN 1 ELSE 0 END)     AS substance_abuse,
    MAX(CASE WHEN d.icd_code LIKE 'F32%'
             OR d.icd_code LIKE 'F33%' THEN 1 ELSE 0 END)     AS depression,
    -- Total comorbidity count
    COUNT(DISTINCT LEFT(d.icd_code, 3))                         AS n_unique_diagnoses
FROM mimiciv_derived.cohort co
LEFT JOIN mimiciv_hosp.diagnoses_icd d
    ON co.subject_id = d.subject_id
    AND co.hadm_id = d.hadm_id
    AND d.icd_version = 10
GROUP BY co.subject_id, co.hadm_id, co.stay_id;


-- ── Step 3: SOFA score (first 24h) ─────────────────────────
-- Uses the pre-computed SOFA table if available in
-- mimiciv_derived (from the MIMIC-IV code repository).

-- If mimiciv_derived.sofa exists:
-- DROP TABLE IF EXISTS mimiciv_derived.cohort_sofa;
-- CREATE TABLE mimiciv_derived.cohort_sofa AS
-- SELECT
--     co.subject_id,
--     co.stay_id,
--     s.sofa_24hours AS sofa_score,
--     s.respiration_24hours AS sofa_resp,
--     s.coagulation_24hours AS sofa_coag,
--     s.liver_24hours AS sofa_liver,
--     s.cardiovascular_24hours AS sofa_cardio,
--     s.cns_24hours AS sofa_cns,
--     s.renal_24hours AS sofa_renal
-- FROM mimiciv_derived.cohort co
-- LEFT JOIN mimiciv_derived.sofa s
--     ON co.stay_id = s.stay_id;


-- ── Step 4: Combine all static features ─────────────────────

DROP TABLE IF EXISTS mimiciv_derived.static_features;
CREATE TABLE mimiciv_derived.static_features AS

SELECT
    co.subject_id,
    co.hadm_id,
    co.stay_id,
    co.age,
    co.gender,
    co.race_group,
    co.age_group,
    co.admission_type,
    co.insurance,
    co.los_icu_hours,
    co.mortality,
    cm.chf, cm.atrial_fibrillation, cm.hypertension,
    cm.copd, cm.asthma,
    cm.diabetes, cm.hyperlipidemia, cm.obesity,
    cm.ckd, cm.aki,
    cm.liver_disease, cm.stroke, cm.dementia,
    cm.sepsis, cm.cancer,
    cm.substance_abuse, cm.depression,
    cm.n_unique_diagnoses
FROM mimiciv_derived.cohort co
LEFT JOIN mimiciv_derived.comorbidities cm
    ON co.subject_id = cm.subject_id
    AND co.stay_id = cm.stay_id;

-- Verify
SELECT
    COUNT(*)                    AS n_patients,
    ROUND(AVG(mortality), 3)    AS mortality_rate,
    ROUND(AVG(chf::NUMERIC), 3)      AS pct_chf,
    ROUND(AVG(diabetes::NUMERIC), 3)  AS pct_diabetes,
    ROUND(AVG(sepsis::NUMERIC), 3)    AS pct_sepsis,
    ROUND(AVG(ckd::NUMERIC), 3)       AS pct_ckd,
    ROUND(AVG(n_unique_diagnoses), 1) AS avg_diagnoses
FROM mimiciv_derived.static_features;
