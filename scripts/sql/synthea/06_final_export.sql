-- ============================================================
-- Synthea Final Data Export & Quality Check
-- ============================================================
-- Combines vitals + labs into a single time-series table,
-- runs data quality checks, and prepares final export views.
-- Run this after scripts 01–05 have been executed.
-- ============================================================

-- ── Step 1: Generate full hour grid per patient ─────────────
-- Ensures every patient has rows for hours 0-47 even
-- if no observations exist for some hours.

DROP TABLE IF EXISTS synthea_derived_hour_grid;
CREATE TABLE synthea_derived_hour_grid AS
WITH RECURSIVE hours(hour_offset) AS (
    SELECT 0
    UNION ALL
    SELECT hour_offset + 1 FROM hours WHERE hour_offset < 47
)
SELECT
    co.patient_id,
    co.encounter_id,
    h.hour_offset
FROM synthea_derived_cohort co
CROSS JOIN hours h;


-- ── Step 2: Combined time-series (vitals + labs) ────────────

DROP TABLE IF EXISTS synthea_derived_timeseries;
CREATE TABLE synthea_derived_timeseries AS
SELECT
    g.patient_id,
    g.encounter_id,
    g.hour_offset,
    -- Vitals
    v.heart_rate,
    v.systolic_bp,
    v.diastolic_bp,
    v.respiratory_rate,
    v.temperature,
    v.spo2,
    -- Labs
    l.glucose,
    l.potassium,
    l.sodium,
    l.chloride,
    l.creatinine,
    l.bun,
    l.hemoglobin,
    l.hematocrit,
    l.wbc,
    l.platelets,
    l.bicarbonate,
    l.lactate,
    l.bilirubin_total,
    l.calcium
FROM synthea_derived_hour_grid g
LEFT JOIN synthea_derived_vitals_hourly v
    ON g.patient_id = v.patient_id
    AND g.encounter_id = v.encounter_id
    AND g.hour_offset = v.hour_offset
LEFT JOIN synthea_derived_labs_hourly l
    ON g.patient_id = l.patient_id
    AND g.encounter_id = l.encounter_id
    AND g.hour_offset = l.hour_offset
ORDER BY g.patient_id, g.hour_offset;


-- ── Step 3: Data quality summary ────────────────────────────

SELECT '=== COHORT SUMMARY ===' AS section;
SELECT
    COUNT(*)                                      AS n_patients,
    SUM(mortality)                                AS n_deaths,
    ROUND(100.0 * AVG(mortality), 2)               AS mortality_pct,
    ROUND(AVG(age), 1)                             AS mean_age,
    ROUND(AVG(los_hours), 1)                       AS mean_los_h
FROM synthea_derived_cohort;

SELECT '=== GENDER BREAKDOWN ===' AS section;
SELECT
    gender,
    COUNT(*) AS n,
    ROUND(100.0 * AVG(mortality), 2) AS mortality_pct
FROM synthea_derived_cohort
GROUP BY gender;

SELECT '=== RACE BREAKDOWN ===' AS section;
SELECT
    race,
    COUNT(*) AS n,
    ROUND(100.0 * AVG(mortality), 2) AS mortality_pct
FROM synthea_derived_cohort
GROUP BY race
ORDER BY n DESC;

SELECT '=== AGE GROUP BREAKDOWN ===' AS section;
SELECT
    age_group,
    COUNT(*) AS n,
    ROUND(100.0 * AVG(mortality), 2) AS mortality_pct
FROM synthea_derived_cohort
GROUP BY age_group
ORDER BY age_group;

SELECT '=== TIMESERIES FEATURE COVERAGE ===' AS section;
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT patient_id) AS n_patients,
    ROUND(100.0 * COUNT(heart_rate)       / COUNT(*), 1) AS pct_hr,
    ROUND(100.0 * COUNT(systolic_bp)      / COUNT(*), 1) AS pct_sbp,
    ROUND(100.0 * COUNT(spo2)             / COUNT(*), 1) AS pct_spo2,
    ROUND(100.0 * COUNT(glucose)          / COUNT(*), 1) AS pct_glucose,
    ROUND(100.0 * COUNT(creatinine)       / COUNT(*), 1) AS pct_creatinine,
    ROUND(100.0 * COUNT(hemoglobin)       / COUNT(*), 1) AS pct_hgb,
    ROUND(100.0 * COUNT(lactate)          / COUNT(*), 1) AS pct_lactate
FROM synthea_derived_timeseries;

SELECT '=== COMORBIDITY PREVALENCE ===' AS section;
SELECT
    ROUND(AVG(chf), 3)           AS chf,
    ROUND(AVG(hypertension), 3)  AS hypertension,
    ROUND(AVG(diabetes), 3)      AS diabetes,
    ROUND(AVG(copd), 3)          AS copd,
    ROUND(AVG(ckd), 3)           AS ckd,
    ROUND(AVG(sepsis), 3)        AS sepsis,
    ROUND(AVG(cancer), 3)        AS cancer,
    ROUND(AVG(depression), 3)    AS depression,
    ROUND(AVG(n_unique_diagnoses), 1) AS avg_dx_count
FROM synthea_derived_static_features;

SELECT '=== CLINICAL NOTES COVERAGE ===' AS section;
SELECT
    COUNT(*) AS total_patients,
    SUM(CASE WHEN n_conditions > 0 THEN 1 ELSE 0 END) AS has_conditions,
    SUM(CASE WHEN n_medications > 0 THEN 1 ELSE 0 END) AS has_medications,
    ROUND(AVG(LENGTH(clinical_note)), 0) AS avg_note_length
FROM synthea_derived_clinical_notes;


-- ── Step 4: Top admission reasons ───────────────────────────

SELECT '=== TOP 10 ADMISSION REASONS ===' AS section;
SELECT
    admit_reason,
    COUNT(*) AS n,
    ROUND(100.0 * AVG(mortality), 2) AS mortality_pct
FROM synthea_derived_cohort
WHERE admit_reason IS NOT NULL AND admit_reason != ''
GROUP BY admit_reason
ORDER BY n DESC
LIMIT 10;
