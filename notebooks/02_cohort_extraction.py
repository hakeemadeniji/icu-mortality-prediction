# %% [markdown]
# # 02 — Cohort Extraction & Outcome Definition
# Extract the ICU cohort, define mortality outcome, and create the analysis dataset.
# Supports both Synthea and MIMIC-IV data sources.

# %% Imports
import os
import pandas as pd
import numpy as np
from datetime import timedelta

# %% Configuration
import yaml
with open(os.path.join("..", "configs", "config.yaml")) as f:
    config = yaml.safe_load(f)

DATA_SOURCE = config["data"]["source"]
PROCESSED_DIR = os.path.join("..", "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

OBSERVATION_WINDOW = config["data"]["observation_window_hours"]
print(f"Data source: {DATA_SOURCE}")
print(f"Observation window: {OBSERVATION_WINDOW} hours")


# %% [markdown]
# ## Cohort Extraction Functions

# %%
def extract_synthea_cohort(synthea_dir: str):
    """Extract ICU-like cohort from Synthea data."""
    csv_dir = synthea_dir
    for subdir in ["csv", "."]:
        check = os.path.join(synthea_dir, subdir)
        if os.path.exists(check) and any(f.endswith(".csv") for f in os.listdir(check)):
            csv_dir = check
            break

    # Load tables
    patients = pd.read_csv(os.path.join(csv_dir, "patients.csv"))
    encounters = pd.read_csv(os.path.join(csv_dir, "encounters.csv"))
    observations = pd.read_csv(os.path.join(csv_dir, "observations.csv"))
    conditions = pd.read_csv(os.path.join(csv_dir, "conditions.csv"))

    # Filter to inpatient/emergency encounters (ICU proxy)
    icu_encounters = encounters[
        encounters["ENCOUNTERCLASS"].isin(["inpatient", "emergency", "urgentcare"])
    ].copy()
    print(f"ICU-like encounters: {len(icu_encounters):,}")

    # Parse dates; strip timezone so comparisons with tz-naive BIRTHDATE/DEATHDATE work
    icu_encounters["START"] = pd.to_datetime(icu_encounters["START"], utc=True).dt.tz_convert(None)
    icu_encounters["STOP"] = pd.to_datetime(icu_encounters["STOP"], utc=True).dt.tz_convert(None)

    # Calculate length of stay
    icu_encounters["los_hours"] = (
        icu_encounters["STOP"] - icu_encounters["START"]
    ).dt.total_seconds() / 3600

    # Filter: stays >= observation window
    icu_encounters = icu_encounters[icu_encounters["los_hours"] >= OBSERVATION_WINDOW]
    print(f"Stays >= {OBSERVATION_WINDOW}h: {len(icu_encounters):,}")

    # Define mortality outcome
    # In Synthea, check if patient died during encounter
    patients["DEATHDATE"] = pd.to_datetime(patients["DEATHDATE"], errors="coerce")
    icu_encounters = icu_encounters.merge(
        patients[["Id", "DEATHDATE", "BIRTHDATE", "GENDER", "RACE", "ETHNICITY"]],
        left_on="PATIENT", right_on="Id", how="left"
    )

    icu_encounters["mortality"] = (
        icu_encounters["DEATHDATE"].notna() &
        (icu_encounters["DEATHDATE"] <= icu_encounters["STOP"] + timedelta(days=30))
    ).astype(int)

    # Demographics
    icu_encounters["BIRTHDATE"] = pd.to_datetime(icu_encounters["BIRTHDATE"])
    icu_encounters["age"] = (
        (icu_encounters["START"] - icu_encounters["BIRTHDATE"]).dt.days / 365.25
    ).astype(int)

    # Filter adults only
    icu_encounters = icu_encounters[icu_encounters["age"] >= 18]
    print(f"Adult encounters: {len(icu_encounters):,}")
    print(f"Mortality rate: {icu_encounters['mortality'].mean():.3f}")

    return icu_encounters, observations, conditions


def extract_mimic_cohort(mimic_dir: str):
    """Extract ICU cohort from MIMIC-IV tables."""
    # Load core tables
    patients = pd.read_csv(os.path.join(mimic_dir, "patients.csv.gz"))
    admissions = pd.read_csv(os.path.join(mimic_dir, "admissions.csv.gz"))
    icustays = pd.read_csv(os.path.join(mimic_dir, "icustays.csv.gz"))

    # Merge
    cohort = icustays.merge(admissions, on=["subject_id", "hadm_id"], how="inner")
    cohort = cohort.merge(patients, on="subject_id", how="inner")

    # Parse dates
    cohort["intime"] = pd.to_datetime(cohort["intime"])
    cohort["outtime"] = pd.to_datetime(cohort["outtime"])
    cohort["admittime"] = pd.to_datetime(cohort["admittime"])
    cohort["dischtime"] = pd.to_datetime(cohort["dischtime"])
    cohort["deathtime"] = pd.to_datetime(cohort["deathtime"], errors="coerce")

    # Length of stay in hours
    cohort["los_hours"] = (cohort["outtime"] - cohort["intime"]).dt.total_seconds() / 3600

    # Filter: stays >= observation window
    cohort = cohort[cohort["los_hours"] >= OBSERVATION_WINDOW]

    # First ICU stay only
    cohort = cohort.sort_values("intime").groupby("subject_id").first().reset_index()

    # Define mortality: in-hospital death
    cohort["mortality"] = cohort["hospital_expire_flag"].astype(int)

    # Age
    cohort["age"] = cohort["anchor_age"]
    cohort = cohort[cohort["age"] >= 18]

    print(f"MIMIC-IV ICU cohort: {len(cohort):,}")
    print(f"Mortality rate: {cohort['mortality'].mean():.3f}")

    return cohort


# %% Extract cohort based on data source
if DATA_SOURCE == "synthea":
    synthea_dir = os.path.join("..", "data", "synthea")
    cohort, observations, conditions = extract_synthea_cohort(synthea_dir)
    cohort_save = cohort[["PATIENT", "Id_x", "START", "STOP", "los_hours",
                          "mortality", "age", "GENDER", "RACE"]].copy()
    cohort_save.columns = ["patient_id", "encounter_id", "admit_time", "discharge_time",
                           "los_hours", "mortality", "age", "gender", "race"]
else:
    mimic_dir = os.path.join("..", "data", "raw", "mimic-iv")
    cohort = extract_mimic_cohort(mimic_dir)
    cohort_save = cohort[["subject_id", "hadm_id", "intime", "outtime", "los_hours",
                          "mortality", "age", "gender"]].copy()
    cohort_save.columns = ["patient_id", "encounter_id", "admit_time", "discharge_time",
                           "los_hours", "mortality", "age", "gender"]

# %% Summary statistics
print(f"\n{'='*50}")
print(f"COHORT SUMMARY")
print(f"{'='*50}")
print(f"Total patients:   {len(cohort_save):,}")
print(f"Mortality:        {cohort_save['mortality'].sum():,} ({cohort_save['mortality'].mean()*100:.1f}%)")
print(f"Survived:         {(1-cohort_save['mortality']).sum():.0f} ({(1-cohort_save['mortality'].mean())*100:.1f}%)")
print(f"Age (median):     {cohort_save['age'].median():.0f}")
print(f"LOS hours (mean): {cohort_save['los_hours'].mean():.1f}")

print(f"\nGender distribution:")
print(cohort_save["gender"].value_counts())

# %% Save cohort
cohort_save.to_csv(os.path.join(PROCESSED_DIR, "cohort.csv"), index=False)
print(f"\n[OK] Cohort saved: {len(cohort_save)} patients")
