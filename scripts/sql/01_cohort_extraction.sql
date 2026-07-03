-- ============================================================
-- MIMIC-IV ICU Mortality Cohort Extraction
-- ============================================================
-- Target: First ICU stay for adult patients (≥18)
-- with at least 48 hours of data.
-- Outcome: In-hospital mortality
--
-- Compatible with: PostgreSQL (local MIMIC), Google BigQuery
-- For BigQuery, replace schema with: physionet-data.mimiciv_3_1_hosp
-- ============================================================

-- ── Step 1: First ICU stays for adult patients ──────────────

DROP TABLE IF EXISTS mimiciv_derived.cohort;
CREATE TABLE mimiciv_derived.cohort AS

WITH first_icu AS (
    SELECT
        ie.subject_id,
        ie.hadm_id,
        ie.stay_id,
        ie.intime,
        ie.outtime,
        EXTRACT(EPOCH FROM (ie.outtime - ie.intime)) / 3600.0 AS los_icu_hours,
        ROW_NUMBER() OVER (
            PARTITION BY ie.subject_id
            ORDER BY ie.intime
        ) AS icu_stay_rank
    FROM mimiciv_icu.icustays ie
),

-- ── Step 2: Merge with admissions and patients ──────────────

cohort_base AS (
    SELECT
        fi.subject_id,
        fi.hadm_id,
        fi.stay_id,
        fi.intime          AS icu_intime,
        fi.outtime         AS icu_outtime,
        fi.los_icu_hours,
        adm.admittime,
        adm.dischtime,
        adm.deathtime,
        adm.hospital_expire_flag,
        adm.admission_type,
        adm.insurance,
        adm.race,
        pat.gender,
        pat.anchor_age     AS age,
        pat.dod            AS date_of_death
    FROM first_icu fi
    INNER JOIN mimiciv_hosp.admissions adm
        ON fi.subject_id = adm.subject_id
        AND fi.hadm_id = adm.hadm_id
    INNER JOIN mimiciv_hosp.patients pat
        ON fi.subject_id = pat.subject_id
    WHERE fi.icu_stay_rank = 1          -- First ICU stay only
      AND pat.anchor_age >= 18          -- Adults only
      AND fi.los_icu_hours >= 48        -- At least 48h observation window
)

SELECT
    subject_id,
    hadm_id,
    stay_id,
    icu_intime,
    icu_outtime,
    los_icu_hours,
    admittime,
    dischtime,
    deathtime,
    hospital_expire_flag AS mortality,
    admission_type,
    insurance,
    race,
    gender,
    age,
    date_of_death,
    -- Age groups for fairness analysis
    CASE
        WHEN age < 40 THEN '18-39'
        WHEN age < 60 THEN '40-59'
        WHEN age < 80 THEN '60-79'
        ELSE '80+'
    END AS age_group,
    -- Simplified race categories for fairness analysis
    CASE
        WHEN race ILIKE '%white%' THEN 'White'
        WHEN race ILIKE '%black%' THEN 'Black'
        WHEN race ILIKE '%asian%' THEN 'Asian'
        WHEN race ILIKE '%hispanic%' OR race ILIKE '%latino%' THEN 'Hispanic'
        ELSE 'Other'
    END AS race_group
FROM cohort_base
ORDER BY subject_id;

-- Verify cohort
SELECT
    COUNT(*)                                    AS total_patients,
    SUM(mortality)                              AS deaths,
    ROUND(AVG(mortality::NUMERIC), 4)           AS mortality_rate,
    ROUND(AVG(age), 1)                          AS mean_age,
    ROUND(AVG(los_icu_hours), 1)                AS mean_los_hours
FROM mimiciv_derived.cohort;
