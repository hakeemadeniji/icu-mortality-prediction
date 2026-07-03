# %% [markdown]
# # 01 — Data Acquisition
# Download Synthea data for immediate pipeline development,
# and instructions for MIMIC-IV integration.

# %% Imports
import os
import pandas as pd
import numpy as np

# %% Configuration
SYNTHEA_DIR = os.path.join("..", "data", "synthea")
RAW_DIR = os.path.join("..", "data", "raw")
os.makedirs(SYNTHEA_DIR, exist_ok=True)

# %% [markdown]
# ## Option A: Synthea Synthetic Data (Immediate)
# Run this to download pre-generated synthetic EHR data.

# %%
# Download Synthea sample data
# Uncomment and run:
# !python ../scripts/generate_synthea.py

# If download fails, manually download from:
# https://synthetichealth.github.io/synthea-sample-data/downloads/
# and extract CSVs to data/synthea/csv/

# %% Check available files
csv_dir = SYNTHEA_DIR
for subdir in ["csv", "."]:
    check = os.path.join(SYNTHEA_DIR, subdir)
    if os.path.exists(check):
        csvs = [f for f in os.listdir(check) if f.endswith(".csv")]
        if csvs:
            csv_dir = check
            break

if os.path.exists(csv_dir):
    print("Available Synthea CSV files:")
    for f in sorted(os.listdir(csv_dir)):
        if f.endswith(".csv"):
            print(f"  {f}")
else:
    print("No data found yet. Run the download script first.")

# %% [markdown]
# ## Option B: MIMIC-IV (Gold Standard)
#
# ### Access Steps:
# 1. Create account at [PhysioNet](https://physionet.org/)
# 2. Complete [CITI Training](https://physionet.org/settings/training/) (takes ~4 hours)
# 3. Sign the MIMIC-IV Data Use Agreement
# 4. Download from: https://physionet.org/content/mimiciv/3.1/
#
# ### Required Tables:
# **From mimic-iv-hosp:**
# - `patients.csv.gz` — demographics
# - `admissions.csv.gz` — hospital admissions
# - `diagnoses_icd.csv.gz` — ICD codes
# - `labevents.csv.gz` — lab results
# - `prescriptions.csv.gz` — medications
#
# **From mimic-iv-icu:**
# - `icustays.csv.gz` — ICU stay info
# - `chartevents.csv.gz` — vitals and charted observations
#
# **From mimic-iv-note:**
# - `discharge.csv.gz` — discharge summaries (clinical notes)
#
# Place files in: `data/raw/mimic-iv/`

# %% Load Synthea data (if available)
key_tables = ["patients", "encounters", "observations", "conditions",
              "medications", "procedures"]

synthea_data = {}
for table in key_tables:
    filepath = os.path.join(csv_dir, f"{table}.csv")
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        synthea_data[table] = df
        print(f"  {table}: {df.shape[0]:,} rows × {df.shape[1]} columns")
    else:
        print(f"  {table}: NOT FOUND")

# %% Inspect patients table
if "patients" in synthea_data:
    patients = synthea_data["patients"]
    print(f"\nPatients table columns: {list(patients.columns)}")
    print(f"\nSample rows:")
    patients.head()

# %% Inspect encounters
if "encounters" in synthea_data:
    enc = synthea_data["encounters"]
    print(f"\nEncounter types:")
    print(enc["ENCOUNTERCLASS"].value_counts())
    print(f"\nTotal encounters: {len(enc):,}")

# %% [markdown]
# ## Next Steps
# Proceed to notebook 02 to extract the ICU cohort and define the outcome variable.
