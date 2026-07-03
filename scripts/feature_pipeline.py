"""
Feature pipeline for MIMIC-IV data exported via SQL.
Converts the SQL-exported CSVs into the same numpy arrays
used by the deep learning notebooks.

Usage:
    python scripts/feature_pipeline.py --source mimic
"""

import os
import argparse
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
OBS_WINDOW = 48
SEED = 42

# Features in the combined timeseries table
VITAL_FEATURES = [
    "heart_rate", "systolic_bp", "diastolic_bp", "mean_bp",
    "respiratory_rate", "temperature", "spo2"
]

LAB_FEATURES = [
    "glucose", "potassium", "sodium", "chloride", "creatinine",
    "bun", "hemoglobin", "hematocrit", "wbc", "platelets",
    "bicarbonate", "lactate"
]

ALL_FEATURES = VITAL_FEATURES + LAB_FEATURES


def load_mimic_exports():
    """Load SQL-exported CSV files."""
    cohort = pd.read_csv(os.path.join(PROCESSED_DIR, "cohort_mimic.csv"))
    ts = pd.read_csv(os.path.join(PROCESSED_DIR, "timeseries_mimic.csv"))
    static = pd.read_csv(os.path.join(PROCESSED_DIR, "static_features_mimic.csv"))

    notes = None
    notes_path = os.path.join(PROCESSED_DIR, "notes_mimic.csv")
    if os.path.exists(notes_path):
        notes = pd.read_csv(notes_path)

    return cohort, ts, static, notes


def build_3d_array(cohort, ts_df, feature_cols):
    """
    Convert long-format timeseries DataFrame to 3D numpy array.
    Shape: (n_patients, OBS_WINDOW, n_features)
    """
    patient_ids = cohort["subject_id"].values
    stay_ids = cohort["stay_id"].values
    n_patients = len(patient_ids)
    n_features = len(feature_cols)

    arr = np.full((n_patients, OBS_WINDOW, n_features), np.nan, dtype=np.float32)

    # Index the timeseries by stay_id for fast lookup
    ts_indexed = ts_df.set_index(["stay_id", "hour_offset"])

    for i, stay_id in enumerate(stay_ids):
        for h in range(OBS_WINDOW):
            try:
                row = ts_indexed.loc[(stay_id, h)]
                for j, feat in enumerate(feature_cols):
                    if feat in row.index:
                        val = row[feat]
                        if pd.notna(val):
                            arr[i, h, j] = val
            except KeyError:
                continue

        if (i + 1) % 1000 == 0:
            print(f"  Processed {i+1}/{n_patients} patients...")

    return arr


def impute_and_normalize(arr):
    """Forward fill, then median impute, then z-score normalize."""
    # Forward fill per patient per feature
    for i in range(arr.shape[0]):
        for j in range(arr.shape[2]):
            series = arr[i, :, j]
            mask = np.isnan(series)
            if not mask.all():
                idx = np.where(~mask, np.arange(len(series)), 0)
                np.maximum.accumulate(idx, out=idx)
                filled = series[idx]
                filled[mask & (idx == 0) & np.isnan(series[0])] = np.nan
                arr[i, :, j] = filled

    # Global median impute
    for j in range(arr.shape[2]):
        col = arr[:, :, j].flatten()
        median_val = np.nanmedian(col) if not np.all(np.isnan(col)) else 0
        arr[:, :, j] = np.where(np.isnan(arr[:, :, j]), median_val, arr[:, :, j])

    # Z-score normalize
    flat = arr.reshape(-1, arr.shape[2])
    means = np.mean(flat, axis=0)
    stds = np.std(flat, axis=0)
    stds[stds == 0] = 1
    arr = (arr - means) / stds

    return arr, means, stds


def main():
    print("Loading MIMIC-IV exported data...")
    cohort, ts_df, static_df, notes_df = load_mimic_exports()
    print(f"  Cohort: {len(cohort)} patients")
    print(f"  Timeseries: {len(ts_df)} rows")

    # Filter feature columns that exist in the data
    available_features = [f for f in ALL_FEATURES if f in ts_df.columns]
    print(f"  Available features: {len(available_features)}/{len(ALL_FEATURES)}")

    # Build 3D array
    print("\nBuilding time-series array...")
    ts_array = build_3d_array(cohort, ts_df, available_features)
    print(f"  Shape: {ts_array.shape}")
    print(f"  Missing: {np.isnan(ts_array).mean()*100:.1f}%")

    # Impute and normalize
    print("\nImputing and normalizing...")
    ts_norm, means, stds = impute_and_normalize(ts_array)

    # Labels
    labels = cohort["mortality"].values.astype(np.float32)

    # Mask (all ones since we zero-filled)
    ts_mask = np.ones((ts_array.shape[0], ts_array.shape[1]), dtype=np.float32)

    # Static features
    static_out = cohort[["age", "gender", "los_icu_hours"]].copy()
    static_out["gender"] = (static_out["gender"].str.upper().str.startswith("M")).astype(int)
    static_out = static_out.fillna(0)

    # Train/val/test split
    train_idx, test_idx = train_test_split(
        np.arange(len(labels)), test_size=0.15, stratify=labels, random_state=SEED
    )
    train_idx, val_idx = train_test_split(
        train_idx, test_size=0.176, stratify=labels[train_idx], random_state=SEED
    )

    # Save
    print("\nSaving processed data...")
    np.save(os.path.join(PROCESSED_DIR, "ts_normalized.npy"), ts_norm)
    np.save(os.path.join(PROCESSED_DIR, "ts_mask.npy"), ts_mask)
    np.save(os.path.join(PROCESSED_DIR, "labels.npy"), labels)
    np.save(os.path.join(PROCESSED_DIR, "train_idx.npy"), train_idx)
    np.save(os.path.join(PROCESSED_DIR, "val_idx.npy"), val_idx)
    np.save(os.path.join(PROCESSED_DIR, "test_idx.npy"), test_idx)
    static_out.to_csv(os.path.join(PROCESSED_DIR, "static_features.csv"), index=False)
    pd.DataFrame({"feature": available_features, "mean": means, "std": stds}).to_csv(
        os.path.join(PROCESSED_DIR, "feature_params.csv"), index=False
    )

    # Save cohort for downstream use
    cohort.to_csv(os.path.join(PROCESSED_DIR, "cohort.csv"), index=False)

    # Save notes if available
    if notes_df is not None:
        notes_df.to_csv(os.path.join(PROCESSED_DIR, "notes.csv"), index=False)

    print(f"\n[OK] Pipeline complete:")
    print(f"  Train: {len(train_idx)} | Val: {len(val_idx)} | Test: {len(test_idx)}")
    print(f"  Mortality rate: {labels.mean():.3f}")


if __name__ == "__main__":
    main()
