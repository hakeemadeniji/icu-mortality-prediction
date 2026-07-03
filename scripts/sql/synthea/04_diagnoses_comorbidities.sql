-- ============================================================
-- Synthea Diagnoses & Comorbidities
-- ============================================================
-- Extracts SNOMED-coded conditions and creates binary
-- comorbidity flags. Synthea uses SNOMED-CT instead of ICD,
-- so we map by SNOMED concept codes.
-- ============================================================

-- ── Step 1: All conditions for cohort patients ──────────────

DROP TABLE IF EXISTS synthea_derived_diagnoses;
CREATE TABLE synthea_derived_diagnoses AS
SELECT
    co.patient_id,
    co.encounter_id,
    c.CODE                          AS snomed_code,
    c.DESCRIPTION                   AS diagnosis_description,
    c.START                         AS onset_date,
    c.STOP                          AS resolved_date,
    -- Active at time of admission?
    CASE
        WHEN c.START <= co.admit_time
         AND (c.STOP IS NULL OR c.STOP >= co.admit_time)
        THEN 1
        ELSE 0
    END AS active_at_admission
FROM conditions c
INNER JOIN synthea_derived_cohort co
    ON c.PATIENT = co.patient_id
ORDER BY co.patient_id, c.START;


-- ── Step 2: Comorbidity flags ───────────────────────────────
-- Uses SNOMED codes and description text matching.

DROP TABLE IF EXISTS synthea_derived_comorbidities;
CREATE TABLE synthea_derived_comorbidities AS
SELECT
    co.patient_id,
    co.encounter_id,
    -- Cardiovascular
    MAX(CASE WHEN d.diagnosis_description LIKE '%heart failure%'
             OR d.snomed_code = '88805009' THEN 1 ELSE 0 END)                  AS chf,
    MAX(CASE WHEN d.diagnosis_description LIKE '%atrial fibrillation%'
             OR d.snomed_code = '49436004' THEN 1 ELSE 0 END)                  AS atrial_fibrillation,
    MAX(CASE WHEN d.diagnosis_description LIKE '%hypertension%'
             OR d.snomed_code = '59621000' THEN 1 ELSE 0 END)                  AS hypertension,
    MAX(CASE WHEN d.diagnosis_description LIKE '%coronary%'
             OR d.diagnosis_description LIKE '%myocardial infarction%'
             OR d.snomed_code = '22298006' THEN 1 ELSE 0 END)                  AS coronary_artery_disease,
    -- Pulmonary
    MAX(CASE WHEN d.diagnosis_description LIKE '%chronic obstructive%'
             OR d.diagnosis_description LIKE '%COPD%'
             OR d.snomed_code = '13645005' THEN 1 ELSE 0 END)                  AS copd,
    MAX(CASE WHEN d.diagnosis_description LIKE '%asthma%'
             OR d.snomed_code = '195967001' THEN 1 ELSE 0 END)                 AS asthma,
    -- Metabolic
    MAX(CASE WHEN d.diagnosis_description LIKE '%diabetes%'
             OR d.snomed_code IN ('44054006', '73211009') THEN 1 ELSE 0 END)   AS diabetes,
    MAX(CASE WHEN d.diagnosis_description LIKE '%obesity%'
             OR d.snomed_code = '162864005' THEN 1 ELSE 0 END)                 AS obesity,
    MAX(CASE WHEN d.diagnosis_description LIKE '%hyperlipidemia%'
             OR d.diagnosis_description LIKE '%dyslipidemia%' THEN 1 ELSE 0 END) AS hyperlipidemia,
    -- Renal
    MAX(CASE WHEN d.diagnosis_description LIKE '%chronic kidney%'
             OR d.snomed_code = '431855005' THEN 1 ELSE 0 END)                 AS ckd,
    MAX(CASE WHEN d.diagnosis_description LIKE '%acute kidney%'
             OR d.diagnosis_description LIKE '%acute renal%' THEN 1 ELSE 0 END) AS aki,
    -- Hepatic
    MAX(CASE WHEN d.diagnosis_description LIKE '%liver%'
             OR d.diagnosis_description LIKE '%cirrhosis%'
             OR d.diagnosis_description LIKE '%hepat%' THEN 1 ELSE 0 END)       AS liver_disease,
    -- Neurologic
    MAX(CASE WHEN d.diagnosis_description LIKE '%stroke%'
             OR d.diagnosis_description LIKE '%cerebrovascular%'
             OR d.snomed_code = '230690007' THEN 1 ELSE 0 END)                 AS stroke,
    MAX(CASE WHEN d.diagnosis_description LIKE '%dementia%'
             OR d.diagnosis_description LIKE '%alzheimer%' THEN 1 ELSE 0 END)   AS dementia,
    -- Infection
    MAX(CASE WHEN d.diagnosis_description LIKE '%sepsis%'
             OR d.diagnosis_description LIKE '%septic%' THEN 1 ELSE 0 END)      AS sepsis,
    MAX(CASE WHEN d.diagnosis_description LIKE '%pneumonia%' THEN 1 ELSE 0 END) AS pneumonia,
    -- Cancer
    MAX(CASE WHEN d.diagnosis_description LIKE '%cancer%'
             OR d.diagnosis_description LIKE '%carcinoma%'
             OR d.diagnosis_description LIKE '%malignant%'
             OR d.diagnosis_description LIKE '%lymphoma%'
             OR d.diagnosis_description LIKE '%leukemia%' THEN 1 ELSE 0 END)    AS cancer,
    -- Psychiatric
    MAX(CASE WHEN d.diagnosis_description LIKE '%depression%'
             OR d.diagnosis_description LIKE '%depressive%' THEN 1 ELSE 0 END)  AS depression,
    MAX(CASE WHEN d.diagnosis_description LIKE '%substance%'
             OR d.diagnosis_description LIKE '%alcohol%dependence%'
             OR d.diagnosis_description LIKE '%opioid%' THEN 1 ELSE 0 END)      AS substance_abuse,
    -- Total unique conditions
    COUNT(DISTINCT d.snomed_code) AS n_unique_diagnoses
FROM synthea_derived_cohort co
LEFT JOIN synthea_derived_diagnoses d
    ON co.patient_id = d.patient_id
GROUP BY co.patient_id, co.encounter_id;


-- ── Step 3: Combined static features table ──────────────────

DROP TABLE IF EXISTS synthea_derived_static_features;
CREATE TABLE synthea_derived_static_features AS
SELECT
    co.patient_id,
    co.encounter_id,
    co.age,
    co.gender,
    co.race,
    co.ethnicity,
    co.age_group,
    co.los_hours,
    co.mortality,
    co.admit_reason,
    cm.chf, cm.atrial_fibrillation, cm.hypertension, cm.coronary_artery_disease,
    cm.copd, cm.asthma,
    cm.diabetes, cm.obesity, cm.hyperlipidemia,
    cm.ckd, cm.aki,
    cm.liver_disease, cm.stroke, cm.dementia,
    cm.sepsis, cm.pneumonia, cm.cancer,
    cm.depression, cm.substance_abuse,
    cm.n_unique_diagnoses
FROM synthea_derived_cohort co
LEFT JOIN synthea_derived_comorbidities cm
    ON co.patient_id = cm.patient_id
    AND co.encounter_id = cm.encounter_id;


-- ── Verify ──────────────────────────────────────────────────

SELECT
    COUNT(*)                                     AS n_patients,
    ROUND(AVG(mortality), 3)                     AS mortality_rate,
    ROUND(AVG(chf), 3)                           AS pct_chf,
    ROUND(AVG(diabetes), 3)                      AS pct_diabetes,
    ROUND(AVG(hypertension), 3)                  AS pct_hypertension,
    ROUND(AVG(copd), 3)                          AS pct_copd,
    ROUND(AVG(sepsis), 3)                        AS pct_sepsis,
    ROUND(AVG(ckd), 3)                           AS pct_ckd,
    ROUND(AVG(cancer), 3)                        AS pct_cancer,
    ROUND(AVG(n_unique_diagnoses), 1)            AS avg_diagnoses
FROM synthea_derived_static_features;
