-- ============================================================
-- MIMIC-IV Laboratory Values Extraction (First 48 Hours)
-- ============================================================
-- Extracts key lab measurements and pivots to hourly format.
-- Labs are less frequent than vitals, so forward-fill will
-- be applied in Python downstream.
-- ============================================================

-- ── Step 1: Extract raw lab values ──────────────────────────

DROP TABLE IF EXISTS mimiciv_derived.labs_raw;
CREATE TABLE mimiciv_derived.labs_raw AS

SELECT
    le.subject_id,
    co.stay_id,
    co.icu_intime,
    le.charttime,
    FLOOR(
        EXTRACT(EPOCH FROM (le.charttime - co.icu_intime)) / 3600.0
    )::INT AS hour_offset,
    CASE
        WHEN le.itemid IN (50931, 50809)   THEN 'glucose'
        WHEN le.itemid IN (50971, 50822)   THEN 'potassium'
        WHEN le.itemid IN (50983, 50824)   THEN 'sodium'
        WHEN le.itemid IN (50902)          THEN 'chloride'
        WHEN le.itemid IN (50912)          THEN 'creatinine'
        WHEN le.itemid IN (51006)          THEN 'bun'
        WHEN le.itemid IN (51222)          THEN 'hemoglobin'
        WHEN le.itemid IN (51221)          THEN 'hematocrit'
        WHEN le.itemid IN (51301)          THEN 'wbc'
        WHEN le.itemid IN (51265)          THEN 'platelets'
        WHEN le.itemid IN (50882)          THEN 'bicarbonate'
        WHEN le.itemid IN (50813)          THEN 'lactate'
        WHEN le.itemid IN (50820)          THEN 'ph'
        WHEN le.itemid IN (50821)          THEN 'pao2'
        WHEN le.itemid IN (50818)          THEN 'paco2'
        WHEN le.itemid IN (51003)          THEN 'troponin_t'
        WHEN le.itemid IN (51002)          THEN 'troponin_i'
        WHEN le.itemid IN (50863)          THEN 'alkaline_phosphatase'
        WHEN le.itemid IN (50861)          THEN 'alt'
        WHEN le.itemid IN (50878)          THEN 'ast'
        WHEN le.itemid IN (50885)          THEN 'bilirubin_total'
        WHEN le.itemid IN (50893)          THEN 'calcium'
        WHEN le.itemid IN (50960)          THEN 'magnesium'
        WHEN le.itemid IN (50970)          THEN 'phosphate'
        WHEN le.itemid IN (51237)          THEN 'inr'
        WHEN le.itemid IN (51274)          THEN 'pt'
        WHEN le.itemid IN (51275)          THEN 'ptt'
    END AS lab_name,
    le.valuenum
FROM mimiciv_hosp.labevents le
INNER JOIN mimiciv_derived.cohort co
    ON le.subject_id = co.subject_id
    AND le.hadm_id = co.hadm_id
WHERE le.itemid IN (
    50931, 50809,   -- Glucose
    50971, 50822,   -- Potassium
    50983, 50824,   -- Sodium
    50902,          -- Chloride
    50912,          -- Creatinine
    51006,          -- BUN
    51222,          -- Hemoglobin
    51221,          -- Hematocrit
    51301,          -- WBC
    51265,          -- Platelets
    50882,          -- Bicarbonate
    50813,          -- Lactate
    50820,          -- pH
    50821,          -- PaO2
    50818,          -- PaCO2
    51003, 51002,   -- Troponin T/I
    50863,          -- Alkaline Phosphatase
    50861,          -- ALT
    50878,          -- AST
    50885,          -- Bilirubin Total
    50893,          -- Calcium
    50960,          -- Magnesium
    50970,          -- Phosphate
    51237,          -- INR
    51274,          -- PT
    51275           -- PTT
)
AND le.valuenum IS NOT NULL
AND le.charttime >= co.icu_intime
AND le.charttime < co.icu_intime + INTERVAL '48 hours'
-- Physiologic range filters
AND le.valuenum > 0;


-- ── Step 2: Pivot labs to hourly wide format ────────────────

DROP TABLE IF EXISTS mimiciv_derived.labs_hourly;
CREATE TABLE mimiciv_derived.labs_hourly AS

SELECT
    subject_id,
    stay_id,
    hour_offset,
    AVG(CASE WHEN lab_name = 'glucose'       THEN valuenum END) AS glucose,
    AVG(CASE WHEN lab_name = 'potassium'     THEN valuenum END) AS potassium,
    AVG(CASE WHEN lab_name = 'sodium'        THEN valuenum END) AS sodium,
    AVG(CASE WHEN lab_name = 'chloride'      THEN valuenum END) AS chloride,
    AVG(CASE WHEN lab_name = 'creatinine'    THEN valuenum END) AS creatinine,
    AVG(CASE WHEN lab_name = 'bun'           THEN valuenum END) AS bun,
    AVG(CASE WHEN lab_name = 'hemoglobin'    THEN valuenum END) AS hemoglobin,
    AVG(CASE WHEN lab_name = 'hematocrit'    THEN valuenum END) AS hematocrit,
    AVG(CASE WHEN lab_name = 'wbc'           THEN valuenum END) AS wbc,
    AVG(CASE WHEN lab_name = 'platelets'     THEN valuenum END) AS platelets,
    AVG(CASE WHEN lab_name = 'bicarbonate'   THEN valuenum END) AS bicarbonate,
    AVG(CASE WHEN lab_name = 'lactate'       THEN valuenum END) AS lactate,
    AVG(CASE WHEN lab_name = 'ph'            THEN valuenum END) AS ph,
    AVG(CASE WHEN lab_name = 'pao2'          THEN valuenum END) AS pao2,
    AVG(CASE WHEN lab_name = 'paco2'         THEN valuenum END) AS paco2,
    AVG(CASE WHEN lab_name = 'bilirubin_total' THEN valuenum END) AS bilirubin_total,
    AVG(CASE WHEN lab_name = 'calcium'       THEN valuenum END) AS calcium,
    AVG(CASE WHEN lab_name = 'magnesium'     THEN valuenum END) AS magnesium,
    AVG(CASE WHEN lab_name = 'inr'           THEN valuenum END) AS inr
FROM mimiciv_derived.labs_raw
WHERE hour_offset BETWEEN 0 AND 47
GROUP BY subject_id, stay_id, hour_offset
ORDER BY subject_id, hour_offset;

-- ── Step 3: Verify coverage ─────────────────────────────────

SELECT
    COUNT(DISTINCT subject_id)                         AS n_patients,
    COUNT(*)                                           AS n_rows,
    ROUND(100.0 * COUNT(glucose) / COUNT(*), 1)        AS pct_glucose,
    ROUND(100.0 * COUNT(creatinine) / COUNT(*), 1)     AS pct_creatinine,
    ROUND(100.0 * COUNT(lactate) / COUNT(*), 1)        AS pct_lactate,
    ROUND(100.0 * COUNT(hemoglobin) / COUNT(*), 1)     AS pct_hemoglobin
FROM mimiciv_derived.labs_hourly;
