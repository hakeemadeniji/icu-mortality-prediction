# Validating on MIMIC-IV — end-to-end

This is the path from **credentialed MIMIC-IV access** to a **real clinical-validation
report** (discrimination + calibration) for the scoring engine. The adapter and
harness are already built and tested; you supply the data.

```
PhysioNet access ──▶ build derived concepts ──▶ run SQL ──▶ CSV ──▶ harness ──▶ report
```

## 1. Get access (required — do not skip)
MIMIC-IV is credentialed data. You must:
1. Create a [PhysioNet](https://physionet.org/) account.
2. Complete the required human-subjects/CITI "Data or Specimens Only Research" training.
3. Sign the MIMIC-IV Data Use Agreement and be approved.

Do **not** commit any MIMIC data to this repo. `data/` is git-ignored; keep extracts
outside version control and handle per your DUA.

## 2. Load MIMIC-IV + build the "derived" concepts
Load MIMIC-IV (PostgreSQL or BigQuery) and build the official derived/concept tables
from the [MIT-LCP mimic-code](https://github.com/MIT-LCP/mimic-code) repository
(`mimic-iv/concepts`). The extraction uses these first-day concepts:
`icustay_detail`, `first_day_vitalsign`, `first_day_gcs`, `first_day_lab`,
`first_day_bg_art`, `first_day_urine_output`, and `ventilation`.

## 3. Extract the cohort CSV
Run [`scripts/sql/mimic/first_day_cohort.sql`](../scripts/sql/mimic/first_day_cohort.sql)
and export the result to CSV, e.g. in `psql`:

```sql
\copy ( <paste the query> ) TO 'mimic_cohort.csv' WITH CSV HEADER
```

The query selects **first adult ICU stays**, reduces first-24h physiology to the
risk-relevant extreme, and includes `hospital_expire_flag` as the outcome. The
SELECT **aliases are the adapter's contract** — if your derived-schema column names
differ, change the *source* columns, not the aliases.

## 4. Run the validation harness
```bash
cd backend
MIMIC_COHORT_CSV=/path/to/mimic_cohort.csv venv/Scripts/python.exe validate_scores.py
```
This writes a **real-cohort** `docs/VALIDATION_RESULTS.md` and
`results/tables/score_validation.csv` with AUROC per score and SAPS II calibration.
(With no env var it falls back to the reproducible synthetic benchmark.)

## 5. Variable mapping (MIMIC first-day concept → snapshot → risk direction)

| Snapshot field | CSV column (SQL alias) | MIMIC source (first-day) | Reduction |
|---|---|---|---|
| heart_rate | heart_rate_max | vitalsign | max |
| sbp / dbp / map | sbp_min / dbp_min / mbp_min | vitalsign | min |
| resp_rate | resp_rate_max | vitalsign | max |
| temperature | temperature_min/max | vitalsign | worst deviation from 37 °C |
| spo2 | spo2_min | vitalsign | min |
| gcs | gcs_min | first_day_gcs | min |
| wbc | wbc_max | lab | max |
| platelets | platelets_min | lab | min |
| bilirubin | bilirubin_total_max | lab | max |
| creatinine / bun | creatinine_max / bun_max | lab | max |
| sodium / potassium | *_min + *_max | lab | worst deviation |
| bicarbonate | bicarbonate_min | lab | min |
| hematocrit | hematocrit_min | lab | min |
| pao2 / paco2 / pH | po2_min / pco2_max / ph_min | first_day_bg_art | extreme |
| lactate | lactate_max | first_day_bg_art | max |
| fio2 | fio2_max | first_day_bg_art | max (percent → fraction) |
| urine_output_ml | urineoutput | first_day_urine_output | 24h total |
| mechanical_ventilation | vent_flag | ventilation | any invasive day 1 |
| outcome | mortality | icustay_detail.hospital_expire_flag | — |

Derived in the adapter: `on_supplemental_o2 = FiO2 > 0.24`, `confusion = GCS < 14`.

## 6. Caveats (read before interpreting)
- **Time window / leakage.** First-24h values mean the scores use data from within the
  stay; for a genuine *early-warning* evaluation, restrict to the first few hours.
- **Worst-value convention.** Matches APACHE/SAPS practice; HR/WBC/temperature also
  have low-end abnormality — the extract uses the common single-extreme choice.
- **Admission type / chronic disease.** `admission_type` defaults to *medical* and
  the SAPS II chronic-disease flags are not populated from MIMIC by default; add them
  from `diagnoses_icd` / surgical service if you need the full SAPS II.
- **Recalibration.** Expect published mortality coefficients (SAPS II, APACHE II) to
  need recalibration to MIMIC; report both original and recalibrated performance.
- **Fairness.** The runner **automatically reports AUROC + event rate by sex and age
  band** for the headline scores (see the "Fairness / subgroup analysis" section of the
  report). To add ethnicity, carry `race` from `mimiciv_hosp.admissions` into the
  extract and add it as a subgroup dimension in `validate_scores._dimension`.
- **FiO2 units** vary by source; the adapter normalizes >1 as a percent.

See [VALIDATION.md](VALIDATION.md) for the overall device-readiness posture.
