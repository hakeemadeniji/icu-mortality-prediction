-- ============================================================
-- Synthea Vital Signs Extraction (First 48 Hours)
-- ============================================================
-- Extracts hourly vital sign measurements from the observations
-- table using LOINC codes. Pivots to wide format.
-- ============================================================

-- ── Step 1: Extract raw vital signs ─────────────────────────
-- Synthea observations use LOINC codes in the CODE column.

DROP TABLE IF EXISTS synthea_derived_vitals_raw;
CREATE TABLE synthea_derived_vitals_raw AS
SELECT
    o.PATIENT                       AS patient_id,
    o.ENCOUNTER                     AS encounter_id,
    co.admit_time,
    o.DATE                          AS obs_time,
    -- Hour offset from admission
    CAST(
        (JULIANDAY(o.DATE) - JULIANDAY(co.admit_time)) * 24
    AS INTEGER) AS hour_offset,
    -- Map LOINC codes to feature names
    CASE
        WHEN o.CODE = '8867-4'              THEN 'heart_rate'
        WHEN o.CODE = '8480-6'              THEN 'systolic_bp'
        WHEN o.CODE = '8462-4'              THEN 'diastolic_bp'
        WHEN o.CODE = '8310-5'              THEN 'temperature'
        WHEN o.CODE = '9279-1'              THEN 'respiratory_rate'
        WHEN o.CODE IN ('2708-6', '59408-5') THEN 'spo2'
        WHEN o.CODE = '29463-7'             THEN 'body_weight'
        WHEN o.CODE = '8302-2'              THEN 'body_height'
        WHEN o.CODE = '39156-5'             THEN 'bmi'
    END AS vital_name,
    CAST(o.VALUE AS REAL) AS valuenum,
    o.UNITS
FROM observations o
INNER JOIN synthea_derived_cohort co
    ON o.PATIENT = co.patient_id
    AND o.ENCOUNTER = co.encounter_id
WHERE o.CODE IN (
    '8867-4',           -- Heart Rate
    '8480-6',           -- Systolic BP
    '8462-4',           -- Diastolic BP
    '8310-5',           -- Body Temperature
    '9279-1',           -- Respiratory Rate
    '2708-6',           -- SpO2 (Oxygen saturation in Arterial blood)
    '59408-5',          -- SpO2 (Pulse oximetry)
    '29463-7',          -- Body Weight
    '8302-2',           -- Body Height
    '39156-5'           -- BMI
)
AND o.VALUE IS NOT NULL
AND o.TYPE = 'numeric'
-- First 48 hours only
AND CAST((JULIANDAY(o.DATE) - JULIANDAY(co.admit_time)) * 24 AS INTEGER) >= 0
AND CAST((JULIANDAY(o.DATE) - JULIANDAY(co.admit_time)) * 24 AS INTEGER) < 48;


-- ── Step 2: Apply physiologic range filters ─────────────────

DELETE FROM synthea_derived_vitals_raw
WHERE (vital_name = 'heart_rate'       AND (valuenum < 20 OR valuenum > 300))
   OR (vital_name = 'systolic_bp'      AND (valuenum < 40 OR valuenum > 300))
   OR (vital_name = 'diastolic_bp'     AND (valuenum < 20 OR valuenum > 200))
   OR (vital_name = 'respiratory_rate'  AND (valuenum < 4  OR valuenum > 70))
   OR (vital_name = 'temperature'       AND (valuenum < 30 OR valuenum > 45))
   OR (vital_name = 'spo2'             AND (valuenum < 50 OR valuenum > 100));


-- ── Step 3: Pivot to hourly wide format ─────────────────────

DROP TABLE IF EXISTS synthea_derived_vitals_hourly;
CREATE TABLE synthea_derived_vitals_hourly AS
SELECT
    patient_id,
    encounter_id,
    hour_offset,
    AVG(CASE WHEN vital_name = 'heart_rate'       THEN valuenum END) AS heart_rate,
    AVG(CASE WHEN vital_name = 'systolic_bp'      THEN valuenum END) AS systolic_bp,
    AVG(CASE WHEN vital_name = 'diastolic_bp'     THEN valuenum END) AS diastolic_bp,
    AVG(CASE WHEN vital_name = 'respiratory_rate'  THEN valuenum END) AS respiratory_rate,
    AVG(CASE WHEN vital_name = 'temperature'       THEN valuenum END) AS temperature,
    AVG(CASE WHEN vital_name = 'spo2'              THEN valuenum END) AS spo2,
    AVG(CASE WHEN vital_name = 'bmi'               THEN valuenum END) AS bmi
FROM synthea_derived_vitals_raw
WHERE hour_offset BETWEEN 0 AND 47
GROUP BY patient_id, encounter_id, hour_offset
ORDER BY patient_id, hour_offset;


-- ── Verify ──────────────────────────────────────────────────

SELECT
    COUNT(DISTINCT patient_id) AS n_patients,
    COUNT(*)                   AS n_rows,
    ROUND(AVG(heart_rate), 1)  AS mean_hr,
    ROUND(AVG(spo2), 1)       AS mean_spo2,
    ROUND(AVG(systolic_bp), 1) AS mean_sbp
FROM synthea_derived_vitals_hourly;

-- Coverage: what percentage of rows have each vital
SELECT
    COUNT(*) AS total_rows,
    ROUND(100.0 * COUNT(heart_rate)       / COUNT(*), 1) AS pct_hr,
    ROUND(100.0 * COUNT(systolic_bp)      / COUNT(*), 1) AS pct_sbp,
    ROUND(100.0 * COUNT(respiratory_rate)  / COUNT(*), 1) AS pct_rr,
    ROUND(100.0 * COUNT(spo2)             / COUNT(*), 1) AS pct_spo2,
    ROUND(100.0 * COUNT(temperature)       / COUNT(*), 1) AS pct_temp
FROM synthea_derived_vitals_hourly;
