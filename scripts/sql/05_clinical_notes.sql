-- ============================================================
-- MIMIC-IV Clinical Notes Extraction
-- ============================================================
-- Extracts discharge summaries and nursing notes from
-- MIMIC-IV-Note for the text modality of the multimodal model.
-- ============================================================

-- ── Step 1: Discharge summaries ─────────────────────────────
-- One per admission — the most comprehensive clinical narrative.

DROP TABLE IF EXISTS mimiciv_derived.clinical_notes;
CREATE TABLE mimiciv_derived.clinical_notes AS

SELECT
    co.subject_id,
    co.hadm_id,
    co.stay_id,
    'discharge' AS note_type,
    ds.charttime AS note_time,
    -- Truncate to first 3000 characters for model input
    LEFT(ds.text, 3000) AS note_text,
    LENGTH(ds.text) AS full_length
FROM mimiciv_note.discharge ds
INNER JOIN mimiciv_derived.cohort co
    ON ds.subject_id = co.subject_id
    AND ds.hadm_id = co.hadm_id;


-- ── Step 2: Radiology reports (supplementary) ───────────────
-- Shorter but often available within the 48h window.

INSERT INTO mimiciv_derived.clinical_notes
SELECT
    co.subject_id,
    co.hadm_id,
    co.stay_id,
    'radiology' AS note_type,
    r.charttime AS note_time,
    LEFT(r.text, 1500) AS note_text,
    LENGTH(r.text) AS full_length
FROM mimiciv_note.radiology r
INNER JOIN mimiciv_derived.cohort co
    ON r.subject_id = co.subject_id
    AND r.hadm_id = co.hadm_id
WHERE r.charttime >= co.icu_intime
  AND r.charttime < co.icu_intime + INTERVAL '48 hours';


-- ── Step 3: Concatenate notes per patient ───────────────────
-- Combine all notes into a single text field per admission,
-- prioritizing discharge summary then radiology.

DROP TABLE IF EXISTS mimiciv_derived.notes_combined;
CREATE TABLE mimiciv_derived.notes_combined AS

WITH ranked_notes AS (
    SELECT
        subject_id,
        hadm_id,
        stay_id,
        note_type,
        note_text,
        ROW_NUMBER() OVER (
            PARTITION BY subject_id, hadm_id
            ORDER BY
                CASE note_type
                    WHEN 'discharge' THEN 1
                    WHEN 'radiology' THEN 2
                    ELSE 3
                END,
                note_time
        ) AS note_rank
    FROM mimiciv_derived.clinical_notes
)

SELECT
    subject_id,
    hadm_id,
    stay_id,
    -- Take the discharge summary as primary note
    MAX(CASE WHEN note_rank = 1 THEN note_text END) AS primary_note,
    -- Concatenate up to 3 supplementary notes
    STRING_AGG(
        CASE WHEN note_rank BETWEEN 2 AND 4 THEN note_text END,
        ' [NOTE_SEP] '
        ORDER BY note_rank
    ) AS supplementary_notes,
    COUNT(*) AS total_notes
FROM ranked_notes
GROUP BY subject_id, hadm_id, stay_id;


-- Verify note coverage
SELECT
    COUNT(*) AS cohort_size,
    SUM(CASE WHEN nc.primary_note IS NOT NULL THEN 1 ELSE 0 END) AS has_note,
    ROUND(
        100.0 * SUM(CASE WHEN nc.primary_note IS NOT NULL THEN 1 ELSE 0 END)
        / COUNT(*), 1
    ) AS pct_coverage
FROM mimiciv_derived.cohort co
LEFT JOIN mimiciv_derived.notes_combined nc
    ON co.subject_id = nc.subject_id
    AND co.stay_id = nc.stay_id;
