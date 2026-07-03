-- ============================================================
-- Synthea ICU Cohort Extraction
-- ============================================================
-- Mirrors MIMIC-IV cohort logic using Synthea schema.
-- Target: First inpatient/emergency stay per adult patient
-- with at least 48 hours of data.
-- Outcome: Death within 30 days of discharge.
-- ============================================================

-- ── Step 1: Identify ICU-like encounters ────────────────────
-- Synthea uses ENCOUNTERCLASS: inpatient, emergency, urgentcare

DROP TABLE IF EXISTS synthea_derived_first_stays;
CREATE TABLE synthea_derived_first_stays AS
SELECT
    e.PATIENT                       AS patient_id,
    e.ID                            AS encounter_id,
    e.ENCOUNTERCLASS                AS encounter_class,
    e.START                         AS admit_time,
    e.STOP                          AS discharge_time,
    e.DESCRIPTION                   AS encounter_description,
    e.REASONDESCRIPTION             AS admit_reason,
    -- Length of stay in hours
    (JULIANDAY(e.STOP) - JULIANDAY(e.START)) * 24.0 AS los_hours,
    -- Rank stays per patient by time
    ROW_NUMBER() OVER (
        PARTITION BY e.PATIENT
        ORDER BY e.START
    ) AS stay_rank
FROM encounters e
WHERE e.ENCOUNTERCLASS IN ('inpatient', 'emergency', 'urgentcare')
  AND e.STOP IS NOT NULL
  AND e.START IS NOT NULL
  -- Stay must be at least 48 hours
  AND (JULIANDAY(e.STOP) - JULIANDAY(e.START)) * 24.0 >= 48;


-- ── Step 2: Build cohort with demographics ──────────────────

DROP TABLE IF EXISTS synthea_derived_cohort;
CREATE TABLE synthea_derived_cohort AS
SELECT
    fs.patient_id,
    fs.encounter_id,
    fs.encounter_class,
    fs.admit_time,
    fs.discharge_time,
    fs.los_hours,
    fs.encounter_description,
    fs.admit_reason,
    -- Demographics
    p.GENDER                        AS gender,
    p.RACE                          AS race,
    p.ETHNICITY                     AS ethnicity,
    p.BIRTHDATE                     AS birth_date,
    p.DEATHDATE                     AS death_date,
    -- Age at admission
    CAST(
        (JULIANDAY(fs.admit_time) - JULIANDAY(p.BIRTHDATE)) / 365.25
    AS INTEGER) AS age,
    -- Mortality outcome: died within 30 days of discharge
    CASE
        WHEN p.DEATHDATE IS NOT NULL
         AND JULIANDAY(p.DEATHDATE) <= JULIANDAY(fs.discharge_time) + 30
        THEN 1
        ELSE 0
    END AS mortality,
    -- Age groups for fairness analysis
    CASE
        WHEN CAST((JULIANDAY(fs.admit_time) - JULIANDAY(p.BIRTHDATE)) / 365.25 AS INTEGER) < 40
            THEN '18-39'
        WHEN CAST((JULIANDAY(fs.admit_time) - JULIANDAY(p.BIRTHDATE)) / 365.25 AS INTEGER) < 60
            THEN '40-59'
        WHEN CAST((JULIANDAY(fs.admit_time) - JULIANDAY(p.BIRTHDATE)) / 365.25 AS INTEGER) < 80
            THEN '60-79'
        ELSE '80+'
    END AS age_group
FROM synthea_derived_first_stays fs
INNER JOIN patients p
    ON fs.patient_id = p.ID
WHERE fs.stay_rank = 1                  -- First qualifying stay only
  AND CAST(
      (JULIANDAY(fs.admit_time) - JULIANDAY(p.BIRTHDATE)) / 365.25
  AS INTEGER) >= 18;                    -- Adults only


-- ── Verify cohort ───────────────────────────────────────────

SELECT
    COUNT(*)                                                AS total_patients,
    SUM(mortality)                                          AS deaths,
    ROUND(AVG(mortality), 4)                                AS mortality_rate,
    ROUND(AVG(age), 1)                                      AS mean_age,
    ROUND(AVG(los_hours), 1)                                AS mean_los_hours
FROM synthea_derived_cohort;

SELECT gender, COUNT(*), ROUND(AVG(mortality), 3) AS mort_rate
FROM synthea_derived_cohort
GROUP BY gender;

SELECT age_group, COUNT(*), ROUND(AVG(mortality), 3) AS mort_rate
FROM synthea_derived_cohort
GROUP BY age_group
ORDER BY age_group;
