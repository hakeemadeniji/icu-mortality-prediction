-- ============================================================
-- Synthea Clinical Notes Construction
-- ============================================================
-- Synthea does not generate free-text notes like MIMIC-IV.
-- Instead, we construct structured clinical narratives from
-- conditions, medications, and observations — demonstrating
-- the same SQL joins and text aggregation skills.
-- ============================================================

-- ── Step 1: Gather active conditions per patient ────────────

DROP TABLE IF EXISTS synthea_derived_condition_summary;
CREATE TABLE synthea_derived_condition_summary AS
SELECT
    co.patient_id,
    co.encounter_id,
    GROUP_CONCAT(DISTINCT c.DESCRIPTION) AS active_conditions,
    COUNT(DISTINCT c.CODE) AS n_conditions
FROM synthea_derived_cohort co
INNER JOIN conditions c
    ON c.PATIENT = co.patient_id
    AND c.START <= co.discharge_time
    AND (c.STOP IS NULL OR c.STOP >= co.admit_time)
GROUP BY co.patient_id, co.encounter_id;


-- ── Step 2: Gather medications during encounter ─────────────

DROP TABLE IF EXISTS synthea_derived_medication_summary;
CREATE TABLE synthea_derived_medication_summary AS
SELECT
    co.patient_id,
    co.encounter_id,
    GROUP_CONCAT(DISTINCT m.DESCRIPTION) AS medications,
    COUNT(DISTINCT m.CODE) AS n_medications
FROM synthea_derived_cohort co
INNER JOIN medications m
    ON m.PATIENT = co.patient_id
    AND m.ENCOUNTER = co.encounter_id
GROUP BY co.patient_id, co.encounter_id;


-- ── Step 3: Gather procedures during encounter ──────────────

DROP TABLE IF EXISTS synthea_derived_procedure_summary;
CREATE TABLE synthea_derived_procedure_summary AS
SELECT
    co.patient_id,
    co.encounter_id,
    GROUP_CONCAT(DISTINCT p.DESCRIPTION) AS procedures_performed,
    COUNT(DISTINCT p.CODE) AS n_procedures
FROM synthea_derived_cohort co
INNER JOIN procedures p
    ON p.PATIENT = co.patient_id
    AND p.ENCOUNTER = co.encounter_id
GROUP BY co.patient_id, co.encounter_id;


-- ── Step 4: Construct clinical note per patient ─────────────

DROP TABLE IF EXISTS synthea_derived_clinical_notes;
CREATE TABLE synthea_derived_clinical_notes AS
SELECT
    co.patient_id,
    co.encounter_id,
    -- Build structured clinical narrative
    'Patient: ' || co.age || ' year old ' || co.gender
    || ', ' || co.race || '. '
    || 'Admitted: ' || co.admit_time || '. '
    || 'Encounter type: ' || co.encounter_class || '. '
    || COALESCE('Reason for admission: ' || co.admit_reason || '. ', '')
    || 'Length of stay: ' || CAST(ROUND(co.los_hours, 0) AS INTEGER) || ' hours. '
    || COALESCE('Active conditions: ' || cs.active_conditions || '. ', 'No documented conditions. ')
    || COALESCE('Medications: ' || ms.medications || '. ', 'No medications documented. ')
    || COALESCE('Procedures: ' || ps.procedures_performed || '. ', '')
    || 'Total diagnoses: ' || COALESCE(cs.n_conditions, 0)
    || ', medications: ' || COALESCE(ms.n_medications, 0)
    || ', procedures: ' || COALESCE(ps.n_procedures, 0) || '.'
    AS clinical_note,

    -- Also store components separately for the text encoder
    cs.active_conditions,
    ms.medications,
    ps.procedures_performed,
    COALESCE(cs.n_conditions, 0)  AS n_conditions,
    COALESCE(ms.n_medications, 0) AS n_medications,
    COALESCE(ps.n_procedures, 0)  AS n_procedures
FROM synthea_derived_cohort co
LEFT JOIN synthea_derived_condition_summary cs
    ON co.patient_id = cs.patient_id AND co.encounter_id = cs.encounter_id
LEFT JOIN synthea_derived_medication_summary ms
    ON co.patient_id = ms.patient_id AND co.encounter_id = ms.encounter_id
LEFT JOIN synthea_derived_procedure_summary ps
    ON co.patient_id = ps.patient_id AND co.encounter_id = ps.encounter_id;


-- ── Verify ──────────────────────────────────────────────────

SELECT
    COUNT(*) AS total_patients,
    SUM(CASE WHEN active_conditions IS NOT NULL THEN 1 ELSE 0 END) AS has_conditions,
    SUM(CASE WHEN medications IS NOT NULL THEN 1 ELSE 0 END)       AS has_medications,
    ROUND(AVG(n_conditions), 1)  AS avg_conditions,
    ROUND(AVG(n_medications), 1) AS avg_medications,
    ROUND(AVG(n_procedures), 1)  AS avg_procedures
FROM synthea_derived_clinical_notes;

-- Sample note
SELECT patient_id, SUBSTR(clinical_note, 1, 300) AS note_preview
FROM synthea_derived_clinical_notes
LIMIT 3;
