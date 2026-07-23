-- ============================================================================
-- MIMIC-IV validation cohort: one row per (first) adult ICU stay, with first-24h
-- physiology reduced to the risk-relevant extreme, plus the mortality outcome.
--
-- Consumed by backend/services/mimic_adapter.py → backend/validate_scores.py.
-- The SELECT *aliases* are the adapter's stable contract; if your derived-schema
-- column names differ, change the SOURCE columns, not the aliases.
--
-- Requires the official MIMIC-IV "derived" concepts (mimic-code repo). Written for
-- PostgreSQL (schema `mimiciv_derived` / `mimiciv_icu`). For BigQuery, prefix
-- tables with `physionet-data.` and replace INTERVAL syntax.
--
-- Export to CSV, e.g. (psql):
--   \copy ( <this query> ) TO 'mimic_cohort.csv' WITH CSV HEADER
-- then:  MIMIC_COHORT_CSV=mimic_cohort.csv  venv/Scripts/python.exe validate_scores.py
-- ============================================================================

SELECT
    icd.stay_id,
    icd.admission_age                                   AS age,
    icd.gender                                          AS gender,
    icd.hospital_expire_flag                            AS mortality,   -- 1 = died in hospital

    -- Vital signs (first day) — risk-relevant extreme
    v.heart_rate_max                                    AS heart_rate_max,
    v.sbp_min                                           AS sbp_min,
    v.dbp_min                                           AS dbp_min,
    v.mbp_min                                           AS mbp_min,
    v.resp_rate_max                                     AS resp_rate_max,
    v.temperature_min                                   AS temperature_min,
    v.temperature_max                                   AS temperature_max,
    v.spo2_min                                          AS spo2_min,

    -- Neuro
    g.gcs_min                                           AS gcs_min,

    -- Labs (first day)
    l.wbc_max                                           AS wbc_max,
    l.platelets_min                                     AS platelets_min,
    l.bilirubin_total_max                               AS bilirubin_max,
    l.creatinine_max                                    AS creatinine_max,
    l.bun_max                                           AS bun_max,
    l.sodium_min                                        AS sodium_min,
    l.sodium_max                                        AS sodium_max,
    l.potassium_min                                     AS potassium_min,
    l.potassium_max                                     AS potassium_max,
    l.bicarbonate_min                                   AS bicarbonate_min,
    l.hematocrit_min                                    AS hematocrit_min,

    -- Arterial blood gas (first day)
    bg.po2_min                                          AS po2_min,
    bg.pco2_max                                         AS pco2_max,
    bg.ph_min                                           AS ph_min,
    bg.lactate_max                                      AS lactate_max,
    bg.fio2_max                                         AS fio2_max,      -- percent (adapter normalizes)

    -- Urine output (first day, mL)
    uo.urineoutput                                      AS urineoutput,

    -- Mechanical ventilation on day 1 (invasive / tracheostomy)
    COALESCE(vent.vent_flag, 0)                         AS vent_flag

FROM mimiciv_derived.icustay_detail icd
LEFT JOIN mimiciv_derived.first_day_vitalsign     v  ON v.stay_id  = icd.stay_id
LEFT JOIN mimiciv_derived.first_day_gcs           g  ON g.stay_id  = icd.stay_id
LEFT JOIN mimiciv_derived.first_day_lab           l  ON l.stay_id  = icd.stay_id
LEFT JOIN mimiciv_derived.first_day_bg_art        bg ON bg.stay_id = icd.stay_id
LEFT JOIN mimiciv_derived.first_day_urine_output  uo ON uo.stay_id = icd.stay_id
LEFT JOIN (
    SELECT vd.stay_id,
           MAX(CASE WHEN vd.ventilation_status IN ('InvasiveVent', 'Tracheostomy')
                    THEN 1 ELSE 0 END) AS vent_flag
    FROM mimiciv_derived.ventilation vd
    JOIN mimiciv_icu.icustays icu ON icu.stay_id = vd.stay_id
    WHERE vd.starttime <= icu.intime + INTERVAL '1 day'
    GROUP BY vd.stay_id
) vent ON vent.stay_id = icd.stay_id

WHERE icd.first_icu_stay          -- first ICU stay of the hospitalization
  AND icd.admission_age >= 18     -- adults only (intended population)
;
