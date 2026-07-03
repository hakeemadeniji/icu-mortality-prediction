# %% [markdown]
# # 03 — Feature Engineering
# Build time-series feature matrices (vitals/labs per hour) and static features
# from the extracted cohort. Handle missing values and create train/val/test splits.

# %% Imports
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import yaml
import warnings
warnings.filterwarnings("ignore")

with open(os.path.join("..", "configs", "config.yaml")) as f:
    config = yaml.safe_load(f)

PROCESSED_DIR = os.path.join("..", "data", "processed")
DATA_SOURCE = config["data"]["source"]
OBS_WINDOW = config["data"]["observation_window_hours"]

# %% Load cohort
cohort = pd.read_csv(os.path.join(PROCESSED_DIR, "cohort.csv"))
cohort["admit_time"] = pd.to_datetime(cohort["admit_time"])
cohort["discharge_time"] = pd.to_datetime(cohort["discharge_time"])
print(f"Cohort: {len(cohort)} patients")

# %% [markdown]
# ## Build Time-Series Feature Matrix
# For each patient, extract hourly measurements for the first 48 hours.

# %%
def build_synthea_timeseries(cohort, synthea_dir):
    """
    Build hourly time-series from Synthea observations table.
    Maps Synthea LOINC codes to clinical features.
    """
    csv_dir = synthea_dir
    for subdir in ["csv", "."]:
        check = os.path.join(synthea_dir, subdir)
        if os.path.exists(check) and any(f.endswith(".csv") for f in os.listdir(check)):
            csv_dir = check
            break

    obs = pd.read_csv(os.path.join(csv_dir, "observations.csv"))
    obs["DATE"] = pd.to_datetime(obs["DATE"], utc=True, errors="coerce").dt.tz_convert(None)

    # Map LOINC codes to feature names
    loinc_map = {
        "8867-4": "heart_rate",
        "8480-6": "systolic_bp",
        "8462-4": "diastolic_bp",
        "8310-5": "temperature",
        "9279-1": "respiratory_rate",
        "2708-6": "spo2", "59408-5": "spo2",
        "2345-7": "glucose",
        "2823-3": "potassium",
        "2951-2": "sodium",
        "2075-0": "chloride",
        "2160-0": "creatinine",
        "3094-0": "bun",
        "718-7": "hemoglobin",
        "4544-3": "hematocrit",
        "6690-2": "wbc",
        "777-3": "platelets",
        "1963-8": "bicarbonate",
        "2524-7": "lactate",
    }

    feature_names = sorted(set(loinc_map.values()))
    n_features = len(feature_names)
    feat_idx = {name: i for i, name in enumerate(feature_names)}

    # Initialize 3D array: (n_patients, OBS_WINDOW, n_features)
    ts_array = np.full((len(cohort), OBS_WINDOW, n_features), np.nan)

    for pat_idx, (_, row) in enumerate(cohort.iterrows()):
        pat_obs = obs[obs["PATIENT"] == row["patient_id"]]
        admit = row["admit_time"]

        for _, o in pat_obs.iterrows():
            code = str(o.get("CODE", ""))
            if code not in loinc_map:
                continue

            feat_name = loinc_map[code]
            if feat_name not in feat_idx:
                continue

            try:
                value = float(o["VALUE"])
            except (ValueError, TypeError):
                continue

            obs_time = o["DATE"]
            if pd.isna(obs_time):
                continue

            hour = int((obs_time - admit).total_seconds() / 3600)
            if 0 <= hour < OBS_WINDOW:
                ts_array[pat_idx, hour, feat_idx[feat_name]] = value

        if pat_idx % 500 == 0:
            print(f"  Processed {pat_idx}/{len(cohort)} patients...")

    return ts_array, feature_names


def build_mimic_timeseries(cohort, mimic_dir):
    """Build hourly time-series from MIMIC-IV chartevents and labevents."""
    # MIMIC itemid mappings (common vital signs)
    vital_itemids = {
        220045: "heart_rate",
        220050: "systolic_bp", 220179: "systolic_bp",
        220051: "diastolic_bp", 220180: "diastolic_bp",
        220052: "mean_bp", 220181: "mean_bp",
        220210: "respiratory_rate", 224690: "respiratory_rate",
        223761: "temperature", 223762: "temperature",
        220277: "spo2",
    }

    lab_itemids = {
        50931: "glucose", 50809: "glucose",
        50971: "potassium", 50822: "potassium",
        50983: "sodium", 50824: "sodium",
        50902: "chloride",
        50912: "creatinine",
        51006: "bun",
        51222: "hemoglobin",
        51221: "hematocrit",
        51301: "wbc",
        51265: "platelets",
        50882: "bicarbonate",
        50813: "lactate",
    }

    feature_names = sorted(set(list(vital_itemids.values()) + list(lab_itemids.values())))
    n_features = len(feature_names)
    feat_idx = {name: i for i, name in enumerate(feature_names)}

    ts_array = np.full((len(cohort), OBS_WINDOW, n_features), np.nan)

    # Load chartevents (vitals) — this is large, process in chunks
    print("  Loading chartevents...")
    chart_path = os.path.join(mimic_dir, "chartevents.csv.gz")
    if os.path.exists(chart_path):
        for chunk in pd.read_csv(chart_path, chunksize=1_000_000,
                                 usecols=["subject_id", "charttime", "itemid", "valuenum"]):
            chunk = chunk[chunk["itemid"].isin(vital_itemids)]
            chunk["charttime"] = pd.to_datetime(chunk["charttime"])

            for _, row in chunk.iterrows():
                pat_mask = cohort["patient_id"] == row["subject_id"]
                if not pat_mask.any():
                    continue
                pat_idx = pat_mask.idxmax()
                admit = cohort.loc[pat_idx, "admit_time"]
                hour = int((row["charttime"] - admit).total_seconds() / 3600)
                if 0 <= hour < OBS_WINDOW and not np.isnan(row["valuenum"]):
                    feat_name = vital_itemids[row["itemid"]]
                    ts_array[pat_idx, hour, feat_idx[feat_name]] = row["valuenum"]

    # Load labevents
    print("  Loading labevents...")
    lab_path = os.path.join(mimic_dir, "labevents.csv.gz")
    if os.path.exists(lab_path):
        for chunk in pd.read_csv(lab_path, chunksize=1_000_000,
                                 usecols=["subject_id", "charttime", "itemid", "valuenum"]):
            chunk = chunk[chunk["itemid"].isin(lab_itemids)]
            chunk["charttime"] = pd.to_datetime(chunk["charttime"])

            for _, row in chunk.iterrows():
                pat_mask = cohort["patient_id"] == row["subject_id"]
                if not pat_mask.any():
                    continue
                pat_idx = pat_mask.idxmax()
                admit = cohort.loc[pat_idx, "admit_time"]
                hour = int((row["charttime"] - admit).total_seconds() / 3600)
                if 0 <= hour < OBS_WINDOW and not np.isnan(row["valuenum"]):
                    feat_name = lab_itemids[row["itemid"]]
                    ts_array[pat_idx, hour, feat_idx[feat_name]] = row["valuenum"]

    return ts_array, feature_names


# %% Build time-series
print("Building time-series feature matrix...")
if DATA_SOURCE == "synthea":
    synthea_dir = os.path.join("..", "data", "synthea")
    ts_array, feature_names = build_synthea_timeseries(cohort, synthea_dir)
else:
    mimic_dir = os.path.join("..", "data", "raw", "mimic-iv")
    ts_array, feature_names = build_mimic_timeseries(cohort, mimic_dir)

print(f"\nTime-series shape: {ts_array.shape}")
print(f"Features ({len(feature_names)}): {feature_names}")

# %% Handle missing values — forward fill then median impute
print("\nImputing missing values...")
missing_before = np.isnan(ts_array).mean() * 100
print(f"  Missing before: {missing_before:.1f}%")

# Forward fill per patient per feature
for i in range(ts_array.shape[0]):
    for j in range(ts_array.shape[2]):
        series = ts_array[i, :, j]
        # Forward fill
        mask = np.isnan(series)
        if not mask.all():
            idx = np.where(~mask, np.arange(len(series)), 0)
            np.maximum.accumulate(idx, out=idx)
            filled = series[idx]
            filled[mask & (idx == 0) & np.isnan(series[0])] = np.nan
            ts_array[i, :, j] = filled

# Global median impute for remaining NaNs
for j in range(ts_array.shape[2]):
    col = ts_array[:, :, j].flatten()
    median_val = np.nanmedian(col) if not np.all(np.isnan(col)) else 0
    nan_mask = np.isnan(ts_array[:, :, j])
    ts_array[:, :, j][nan_mask] = median_val

missing_after = np.isnan(ts_array).mean() * 100
print(f"  Missing after: {missing_after:.1f}%")

# %% Normalize per feature (z-score)
print("Normalizing features...")
means = np.nanmean(ts_array.reshape(-1, ts_array.shape[2]), axis=0)
stds = np.nanstd(ts_array.reshape(-1, ts_array.shape[2]), axis=0)
stds[stds == 0] = 1  # Avoid division by zero

ts_normalized = (ts_array - means) / stds

# %% Create mask (1 = valid observation existed, 0 = was imputed)
ts_mask = np.ones((ts_array.shape[0], ts_array.shape[1]), dtype=np.float32)

# %% Build static features
static_features = cohort[["age", "gender", "los_hours"]].copy()
static_features["gender"] = (static_features["gender"].str.upper().str.startswith("M")).astype(int)
static_features = static_features.fillna(0)

# %% Train/Val/Test Split
labels = cohort["mortality"].values

min_class = int(np.bincount(labels.astype(int)).min())
can_stratify = min_class >= 2
X_train_idx, X_test_idx, y_train, y_test = train_test_split(
    np.arange(len(labels)), labels,
    test_size=config["data"]["test_size"],
    stratify=labels if can_stratify else None,
    random_state=config["data"]["random_seed"]
)

min_class_train = int(np.bincount(y_train.astype(int)).min())
can_stratify_val = min_class_train >= 2
X_train_idx, X_val_idx, y_train, y_val = train_test_split(
    X_train_idx, y_train,
    test_size=config["data"]["val_size"] / (1 - config["data"]["test_size"]),
    stratify=y_train if can_stratify_val else None,
    random_state=config["data"]["random_seed"]
)

print(f"\nSplit sizes:")
print(f"  Train: {len(X_train_idx)} (mortality: {y_train.mean():.3f})")
print(f"  Val:   {len(X_val_idx)} (mortality: {y_val.mean():.3f})")
print(f"  Test:  {len(X_test_idx)} (mortality: {y_test.mean():.3f})")

# %% Save processed data
np.save(os.path.join(PROCESSED_DIR, "ts_normalized.npy"), ts_normalized.astype(np.float32))
np.save(os.path.join(PROCESSED_DIR, "ts_mask.npy"), ts_mask)
np.save(os.path.join(PROCESSED_DIR, "labels.npy"), labels)
np.save(os.path.join(PROCESSED_DIR, "train_idx.npy"), X_train_idx)
np.save(os.path.join(PROCESSED_DIR, "val_idx.npy"), X_val_idx)
np.save(os.path.join(PROCESSED_DIR, "test_idx.npy"), X_test_idx)
static_features.to_csv(os.path.join(PROCESSED_DIR, "static_features.csv"), index=False)

# Save feature names and normalization params for inference
pd.DataFrame({"feature": feature_names, "mean": means, "std": stds}).to_csv(
    os.path.join(PROCESSED_DIR, "feature_params.csv"), index=False
)

print(f"\n[OK] All processed data saved to {PROCESSED_DIR}")
