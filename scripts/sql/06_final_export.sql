-- ============================================================
-- MIMIC-IV Final Data Export & Quality Check
-- ============================================================
-- Combines all derived tables and exports CSV-ready views.
-- Run this after scripts 01–05 have been executed.
-- ============================================================

-- ── Combined time-series (vitals + labs per hour) ───────────

DROP TABLE IF EXISTS mimiciv_derived.timeseries_combined;
CREATE TABLE mimiciv_derived.timeseries_combined AS

WITH hours AS (
    SELECT
        co.subject_id,
        co.stay_id,
        g.hour_offset
    FROM mimiciv_derived.cohort co
    CROSS JOIN generate_series(0, 47) AS g(hour_offset)
)

SELECT
    h.subject_id,
    h.stay_id,
    h.hour_offset,
    -- Vitals
    v.heart_rate,
    v.systolic_bp,
    v.diastolic_bp,
    v.mean_bp,
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
    l.ph,
    l.bilirubin_total,
    l.inr
FROM hours h
LEFT JOIN mimiciv_derived.vitals_hourly v
    ON h.subject_id = v.subject_id
    AND h.stay_id = v.stay_id
    AND h.hour_offset = v.hour_offset
LEFT JOIN mimiciv_derived.labs_hourly l
    ON h.subject_id = l.subject_id
    AND h.stay_id = l.stay_id
    AND h.hour_offset = l.hour_offset
ORDER BY h.subject_id, h.hour_offset;


-- ── Data quality summary ────────────────────────────────────

SELECT '=== COHORT ===' AS section;
SELECT
    COUNT(*)              AS n_patients,
    SUM(mortality)        AS n_deaths,
    ROUND(100.0 * AVG(mortality), 2) AS mortality_pct,
    ROUND(AVG(age), 1)    AS mean_age,
    ROUND(AVG(los_icu_hours), 1) AS mean_los_h
FROM mimiciv_derived.cohort;

SELECT '=== GENDER ===' AS section;
SELECT gender, COUNT(*), ROUND(100.0 * AVG(mortality), 2) AS mort_pct
FROM mimiciv_derived.cohort
GROUP BY gender;

SELECT '=== RACE ===' AS section;
SELECT race_group, COUNT(*), ROUND(100.0 * AVG(mortality), 2) AS mort_pct
FROM mimiciv_derived.cohort
GROUP BY race_group
ORDER BY COUNT(*) DESC;

SELECT '=== AGE GROUP ===' AS section;
SELECT age_group, COUNT(*), ROUND(100.0 * AVG(mortality), 2) AS mort_pct
FROM mimiciv_derived.cohort
GROUP BY age_group
ORDER BY age_group;

SELECT '=== FEATURE COVERAGE (timeseries) ===' AS section;
SELECT
    COUNT(*) AS total_rows,
    ROUND(100.0 * COUNT(heart_rate)       / COUNT(*), 1) AS pct_hr,
    ROUND(100.0 * COUNT(systolic_bp)      / COUNT(*), 1) AS pct_sbp,
    ROUND(100.0 * COUNT(spo2)             / COUNT(*), 1) AS pct_spo2,
    ROUND(100.0 * COUNT(glucose)          / COUNT(*), 1) AS pct_glucose,
    ROUND(100.0 * COUNT(creatinine)       / COUNT(*), 1) AS pct_creatinine,
    ROUND(100.0 * COUNT(lactate)          / COUNT(*), 1) AS pct_lactate,
    ROUND(100.0 * COUNT(hemoglobin)       / COUNT(*), 1) AS pct_hgb
FROM mimiciv_derived.timeseries_combined;

SELECT '=== NOTES COVERAGE ===' AS section;
SELECT
    COUNT(*)                                               AS cohort_total,
    SUM(CASE WHEN nc.primary_note IS NOT NULL THEN 1 ELSE 0 END) AS with_note,
    ROUND(
        100.0 * SUM(CASE WHEN nc.primary_note IS NOT NULL THEN 1 ELSE 0 END)
        / COUNT(*), 1
    ) AS pct_with_note
FROM mimiciv_derived.cohort co
LEFT JOIN mimiciv_derived.notes_combined nc
    ON co.subject_id = nc.subject_id AND co.stay_id = nc.stay_id;


-- ── Export instructions ─────────────────────────────────────
-- Run these COPY commands from psql to export CSV files:
--
-- \COPY mimiciv_derived.cohort TO 'data/processed/cohort_mimic.csv' CSV HEADER;
-- \COPY mimiciv_derived.static_features TO 'data/processed/static_features_mimic.csv' CSV HEADER;
-- \COPY mimiciv_derived.timeseries_combined TO 'data/processed/timeseries_mimic.csv' CSV HEADER;
-- \COPY mimiciv_derived.notes_combined TO 'data/processed/notes_mimic.csv' CSV HEADER;
--
-- Or for BigQuery, export to GCS:
-- EXPORT DATA OPTIONS(
--   uri='gs://your-bucket/timeseries_*.csv',
--   format='CSV',
--   overwrite=true,
--   header=true
-- ) AS
-- SELECT * FROM mimiciv_derived.timeseries_combined;
