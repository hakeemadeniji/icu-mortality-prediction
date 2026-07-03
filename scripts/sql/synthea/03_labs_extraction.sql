-- ============================================================
-- Synthea Laboratory Values Extraction (First 48 Hours)
-- ============================================================
-- Extracts lab measurements from observations table using
-- LOINC codes and pivots to hourly wide format.
-- ============================================================

-- ── Step 1: Extract raw lab values ──────────────────────────

DROP TABLE IF EXISTS synthea_derived_labs_raw;
CREATE TABLE synthea_derived_labs_raw AS
SELECT
    o.PATIENT                       AS patient_id,
    o.ENCOUNTER                     AS encounter_id,
    co.admit_time,
    o.DATE                          AS obs_time,
    CAST(
        (JULIANDAY(o.DATE) - JULIANDAY(co.admit_time)) * 24
    AS INTEGER) AS hour_offset,
    -- Map LOINC codes to lab names
    CASE
        WHEN o.CODE = '2345-7'  THEN 'glucose'
        WHEN o.CODE = '2823-3'  THEN 'potassium'
        WHEN o.CODE = '2951-2'  THEN 'sodium'
        WHEN o.CODE = '2075-0'  THEN 'chloride'
        WHEN o.CODE = '2160-0'  THEN 'creatinine'
        WHEN o.CODE = '3094-0'  THEN 'bun'
        WHEN o.CODE = '6690-2'  THEN 'wbc'
        WHEN o.CODE = '718-7'   THEN 'hemoglobin'
        WHEN o.CODE = '4544-3'  THEN 'hematocrit'
        WHEN o.CODE = '777-3'   THEN 'platelets'
        WHEN o.CODE = '1963-8'  THEN 'bicarbonate'
        WHEN o.CODE = '2524-7'  THEN 'lactate'
        WHEN o.CODE = '1742-6'  THEN 'alt'
        WHEN o.CODE = '1920-8'  THEN 'ast'
        WHEN o.CODE = '1975-2'  THEN 'bilirubin_total'
        WHEN o.CODE = '17861-6' THEN 'calcium'
        WHEN o.CODE = '2947-0'  THEN 'magnesium'
        WHEN o.CODE = '2085-9'  THEN 'phosphate'
        WHEN o.CODE = '6768-6'  THEN 'alkaline_phosphatase'
        WHEN o.CODE = '2571-8'  THEN 'triglycerides'
        WHEN o.CODE = '2093-3'  THEN 'cholesterol_total'
        WHEN o.CODE = '33914-3' THEN 'egfr'
        WHEN o.CODE = '4548-4'  THEN 'hba1c'
        WHEN o.CODE = '2339-0'  THEN 'glucose_random'
    END AS lab_name,
    CAST(o.VALUE AS REAL) AS valuenum,
    o.UNITS
FROM observations o
INNER JOIN synthea_derived_cohort co
    ON o.PATIENT = co.patient_id
    AND o.ENCOUNTER = co.encounter_id
WHERE o.CODE IN (
    '2345-7',       -- Glucose
    '2823-3',       -- Potassium
    '2951-2',       -- Sodium
    '2075-0',       -- Chloride
    '2160-0',       -- Creatinine
    '3094-0',       -- BUN
    '6690-2',       -- WBC
    '718-7',        -- Hemoglobin
    '4544-3',       -- Hematocrit
    '777-3',        -- Platelets
    '1963-8',       -- Bicarbonate
    '2524-7',       -- Lactate
    '1742-6',       -- ALT
    '1920-8',       -- AST
    '1975-2',       -- Bilirubin Total
    '17861-6',      -- Calcium
    '2947-0',       -- Magnesium
    '2085-9',       -- Phosphate
    '6768-6',       -- Alkaline Phosphatase
    '2571-8',       -- Triglycerides
    '2093-3',       -- Total Cholesterol
    '33914-3',      -- eGFR
    '4548-4',       -- HbA1c
    '2339-0'        -- Glucose (random)
)
AND o.VALUE IS NOT NULL
AND o.TYPE = 'numeric'
AND CAST((JULIANDAY(o.DATE) - JULIANDAY(co.admit_time)) * 24 AS INTEGER) >= 0
AND CAST((JULIANDAY(o.DATE) - JULIANDAY(co.admit_time)) * 24 AS INTEGER) < 48
AND CAST(o.VALUE AS REAL) > 0;


-- ── Step 2: Pivot to hourly wide format ─────────────────────

DROP TABLE IF EXISTS synthea_derived_labs_hourly;
CREATE TABLE synthea_derived_labs_hourly AS
SELECT
    patient_id,
    encounter_id,
    hour_offset,
    AVG(CASE WHEN lab_name = 'glucose'          THEN valuenum END) AS glucose,
    AVG(CASE WHEN lab_name = 'potassium'        THEN valuenum END) AS potassium,
    AVG(CASE WHEN lab_name = 'sodium'           THEN valuenum END) AS sodium,
    AVG(CASE WHEN lab_name = 'chloride'         THEN valuenum END) AS chloride,
    AVG(CASE WHEN lab_name = 'creatinine'       THEN valuenum END) AS creatinine,
    AVG(CASE WHEN lab_name = 'bun'              THEN valuenum END) AS bun,
    AVG(CASE WHEN lab_name = 'hemoglobin'       THEN valuenum END) AS hemoglobin,
    AVG(CASE WHEN lab_name = 'hematocrit'       THEN valuenum END) AS hematocrit,
    AVG(CASE WHEN lab_name = 'wbc'              THEN valuenum END) AS wbc,
    AVG(CASE WHEN lab_name = 'platelets'        THEN valuenum END) AS platelets,
    AVG(CASE WHEN lab_name = 'bicarbonate'      THEN valuenum END) AS bicarbonate,
    AVG(CASE WHEN lab_name = 'lactate'          THEN valuenum END) AS lactate,
    AVG(CASE WHEN lab_name = 'bilirubin_total'  THEN valuenum END) AS bilirubin_total,
    AVG(CASE WHEN lab_name = 'calcium'          THEN valuenum END) AS calcium,
    AVG(CASE WHEN lab_name = 'alt'              THEN valuenum END) AS alt,
    AVG(CASE WHEN lab_name = 'ast'              THEN valuenum END) AS ast,
    AVG(CASE WHEN lab_name = 'egfr'             THEN valuenum END) AS egfr
FROM synthea_derived_labs_raw
WHERE hour_offset BETWEEN 0 AND 47
GROUP BY patient_id, encounter_id, hour_offset
ORDER BY patient_id, hour_offset;


-- ── Verify coverage ─────────────────────────────────────────

SELECT
    COUNT(DISTINCT patient_id)                              AS n_patients,
    COUNT(*)                                                AS n_rows,
    ROUND(100.0 * COUNT(glucose)    / COUNT(*), 1)          AS pct_glucose,
    ROUND(100.0 * COUNT(creatinine) / COUNT(*), 1)          AS pct_creatinine,
    ROUND(100.0 * COUNT(hemoglobin) / COUNT(*), 1)          AS pct_hemoglobin,
    ROUND(100.0 * COUNT(wbc)        / COUNT(*), 1)          AS pct_wbc,
    ROUND(100.0 * COUNT(potassium)  / COUNT(*), 1)          AS pct_potassium,
    ROUND(100.0 * COUNT(lactate)    / COUNT(*), 1)          AS pct_lactate
FROM synthea_derived_labs_hourly;
