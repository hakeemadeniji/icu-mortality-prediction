-- ============================================================
-- MIMIC-IV Vital Signs Extraction (First 48 Hours)
-- ============================================================
-- Extracts hourly vital sign measurements from chartevents
-- and pivots them into a wide-format time-series table.
-- ============================================================

-- ── Step 1: Extract raw vital signs ─────────────────────────

DROP TABLE IF EXISTS mimiciv_derived.vitals_raw;
CREATE TABLE mimiciv_derived.vitals_raw AS

SELECT
    c.subject_id,
    c.stay_id,
    co.icu_intime,
    ce.charttime,
    -- Calculate hour offset from ICU admission
    FLOOR(
        EXTRACT(EPOCH FROM (ce.charttime - co.icu_intime)) / 3600.0
    )::INT AS hour_offset,
    -- Map itemid to readable feature name
    CASE
        WHEN ce.itemid IN (220045)              THEN 'heart_rate'
        WHEN ce.itemid IN (220050, 220179)      THEN 'systolic_bp'
        WHEN ce.itemid IN (220051, 220180)      THEN 'diastolic_bp'
        WHEN ce.itemid IN (220052, 220181, 225312) THEN 'mean_bp'
        WHEN ce.itemid IN (220210, 224690)      THEN 'respiratory_rate'
        WHEN ce.itemid IN (223761)              THEN 'temperature_f'
        WHEN ce.itemid IN (223762)              THEN 'temperature_c'
        WHEN ce.itemid IN (220277)              THEN 'spo2'
    END AS vital_name,
    ce.valuenum
FROM mimiciv_icu.chartevents ce
INNER JOIN mimiciv_derived.cohort co
    ON ce.subject_id = co.subject_id
    AND ce.stay_id = co.stay_id
WHERE ce.itemid IN (
    220045,                     -- Heart Rate
    220050, 220179,             -- Systolic BP (invasive, non-invasive)
    220051, 220180,             -- Diastolic BP
    220052, 220181, 225312,     -- Mean BP
    220210, 224690,             -- Respiratory Rate
    223761,                     -- Temperature (Fahrenheit)
    223762,                     -- Temperature (Celsius)
    220277                      -- SpO2
)
AND ce.valuenum IS NOT NULL
-- Keep only first 48 hours
AND ce.charttime >= co.icu_intime
AND ce.charttime < co.icu_intime + INTERVAL '48 hours'
-- Basic range filters to remove erroneous entries
AND (
    (ce.itemid = 220045 AND ce.valuenum BETWEEN 20 AND 300)     -- HR
    OR (ce.itemid IN (220050, 220179) AND ce.valuenum BETWEEN 40 AND 300)  -- SBP
    OR (ce.itemid IN (220051, 220180) AND ce.valuenum BETWEEN 20 AND 200)  -- DBP
    OR (ce.itemid IN (220052, 220181, 225312) AND ce.valuenum BETWEEN 20 AND 250) -- MBP
    OR (ce.itemid IN (220210, 224690) AND ce.valuenum BETWEEN 4 AND 70)    -- RR
    OR (ce.itemid = 223761 AND ce.valuenum BETWEEN 90 AND 115)  -- Temp F
    OR (ce.itemid = 223762 AND ce.valuenum BETWEEN 30 AND 45)   -- Temp C
    OR (ce.itemid = 220277 AND ce.valuenum BETWEEN 50 AND 100)  -- SpO2
);


-- ── Step 2: Normalize temperature to Celsius ────────────────

UPDATE mimiciv_derived.vitals_raw
SET
    valuenum = (valuenum - 32) * 5.0 / 9.0,
    vital_name = 'temperature'
WHERE vital_name = 'temperature_f';

UPDATE mimiciv_derived.vitals_raw
SET vital_name = 'temperature'
WHERE vital_name = 'temperature_c';


-- ── Step 3: Pivot to hourly wide format ─────────────────────
-- Average multiple readings within the same hour.

DROP TABLE IF EXISTS mimiciv_derived.vitals_hourly;
CREATE TABLE mimiciv_derived.vitals_hourly AS

SELECT
    subject_id,
    stay_id,
    hour_offset,
    AVG(CASE WHEN vital_name = 'heart_rate'       THEN valuenum END) AS heart_rate,
    AVG(CASE WHEN vital_name = 'systolic_bp'      THEN valuenum END) AS systolic_bp,
    AVG(CASE WHEN vital_name = 'diastolic_bp'     THEN valuenum END) AS diastolic_bp,
    AVG(CASE WHEN vital_name = 'mean_bp'          THEN valuenum END) AS mean_bp,
    AVG(CASE WHEN vital_name = 'respiratory_rate'  THEN valuenum END) AS respiratory_rate,
    AVG(CASE WHEN vital_name = 'temperature'       THEN valuenum END) AS temperature,
    AVG(CASE WHEN vital_name = 'spo2'              THEN valuenum END) AS spo2
FROM mimiciv_derived.vitals_raw
WHERE hour_offset BETWEEN 0 AND 47
GROUP BY subject_id, stay_id, hour_offset
ORDER BY subject_id, hour_offset;

-- Verify
SELECT
    COUNT(DISTINCT subject_id) AS n_patients,
    COUNT(*)                   AS n_rows,
    ROUND(AVG(heart_rate), 1)  AS mean_hr,
    ROUND(AVG(spo2), 1)       AS mean_spo2
FROM mimiciv_derived.vitals_hourly;
