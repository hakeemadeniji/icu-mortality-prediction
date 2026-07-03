"""
Feature pipeline for SQL-exported Synthea data.
Reads the CSVs produced by run_synthea_sql.py and converts
them into the numpy arrays used by notebooks 04-09.

Usage:
    python scripts/feature_pipeline_sql.py
"""

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

PROCESSED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "data", "processed")
OBS_WINDOW = 48
SEED = 42

# Features in the combined timeseries table (must match SQL column names)
ALL_FEATURES = [
    "heart_rate", "systolic_bp", "diastolic_bp", "respiratory_rate",
    "temperature", "spo2",
    "glucose", "potassium", "sodium", "chloride", "creatinine",
    "bun", "hemoglobin", "hematocrit", "wbc", "platelets",
    "bicarbonate", "lactate", "bilirubin_total", "calcium",
]


def main():
    print("Loading SQL-exported CSVs...")

    # ── Load CSVs ────────────────────────────────────────────
    cohort = pd.read_csv(os.path.join(PROCESSED_DIR, "cohort.csv"))
    ts_df = pd.read_csv(os.path.join(PROCESSED_DIR, "timeseries.csv"))
    static_df = pd.read_csv(os.path.join(PROCESSED_DIR, "static_features.csv"))

    notes_path = os.path.join(PROCESSED_DIR, "clinical_notes.csv")
    notes_df = pd.read_csv(notes_path) if os.path.exists(notes_path) else None

    print(f"  Cohort:       {len(cohort):,} patients")
    print(f"  Timeseries:   {len(ts_df):,} rows")
    print(f"  Mortality:    {cohort['mortality'].mean():.3f}")

    # ── Identify available features ──────────────────────────
    available = [f for f in ALL_FEATURES if f in ts_df.columns]
    missing = [f for f in ALL_FEATURES if f not in ts_df.columns]
    print(f"  Features:     {len(available)}/{len(ALL_FEATURES)} available")
    if missing:
        print(f"  Missing:      {missing}")

    # ── Build 3D array ───────────────────────────────────────
    patient_ids = cohort["patient_id"].values
    n_patients = len(patient_ids)
    n_features = len(available)

    print(f"\nBuilding 3D array: ({n_patients}, {OBS_WINDOW}, {n_features})...")
    arr = np.full((n_patients, OBS_WINDOW, n_features), np.nan, dtype=np.float32)

    # Create patient_id → index mapping
    pid_to_idx = {pid: i for i, pid in enumerate(patient_ids)}

    # Group timeseries by patient for fast access
    grouped = ts_df.groupby("patient_id")
    for pid, group in grouped:
        if pid not in pid_to_idx:
            continue
        idx = pid_to_idx[pid]
        for _, row in group.iterrows():
            h = int(row["hour_offset"])
            if 0 <= h < OBS_WINDOW:
                for j, feat in enumerate(available):
                    val = row.get(feat)
                    if pd.notna(val):
                        arr[idx, h, j] = float(val)

    missing_pct = np.isnan(arr).mean() * 100
    print(f"  Missing before imputation: {missing_pct:.1f}%")

    # ── Forward fill → median impute ────────────────────────
    print("Imputing missing values...")
    for i in range(n_patients):
        for j in range(n_features):
            series = arr[i, :, j]
            mask = np.isnan(series)
            if not mask.all():
                idx_arr = np.where(~mask, np.arange(OBS_WINDOW), 0)
                np.maximum.accumulate(idx_arr, out=idx_arr)
                filled = series[idx_arr]
                filled[mask & (idx_arr == 0) & np.isnan(series[0])] = np.nan
                arr[i, :, j] = filled

    # Global median for remaining NaNs
    for j in range(n_features):
        col = arr[:, :, j].flatten()
        med = np.nanmedian(col) if not np.all(np.isnan(col)) else 0
        arr[:, :, j] = np.where(np.isnan(arr[:, :, j]), med, arr[:, :, j])

    print(f"  Missing after imputation:  {np.isnan(arr).mean()*100:.1f}%")

    # ── Z-score normalize ───────────────────────────────────
    print("Normalizing...")
    flat = arr.reshape(-1, n_features)
    means = np.mean(flat, axis=0)
    stds = np.std(flat, axis=0)
    stds[stds == 0] = 1
    arr_norm = (arr - means) / stds

    # ── Labels + mask ────────────────────────────────────────
    labels = cohort["mortality"].values.astype(np.float32)
    ts_mask = np.ones((n_patients, OBS_WINDOW), dtype=np.float32)

    # ── Static features ──────────────────────────────────────
    static_out = cohort[["age", "gender", "los_hours"]].copy()
    static_out["gender"] = static_out["gender"].str.upper().str.startswith("M").astype(int)
    static_out = static_out.fillna(0)

    # ── Train / val / test split ─────────────────────────────
    # Stratify only when each class has >=2 samples in every split.
    # With tiny cohorts (e.g. Synthea sample) stratification may fail.
    min_class = int(np.bincount(labels.astype(int)).min())
    can_stratify_test = min_class >= 2
    train_idx, test_idx = train_test_split(
        np.arange(n_patients), test_size=0.15,
        stratify=labels if can_stratify_test else None,
        random_state=SEED
    )
    min_class_train = int(np.bincount(labels[train_idx].astype(int)).min())
    can_stratify_val = min_class_train >= 2
    train_idx, val_idx = train_test_split(
        train_idx, test_size=0.176,
        stratify=labels[train_idx] if can_stratify_val else None,
        random_state=SEED
    )

    # ── Save everything ─────────────────────────────────────
    print(f"\nSaving to {PROCESSED_DIR}...")
    np.save(os.path.join(PROCESSED_DIR, "ts_normalized.npy"), arr_norm)
    np.save(os.path.join(PROCESSED_DIR, "ts_mask.npy"), ts_mask)
    np.save(os.path.join(PROCESSED_DIR, "labels.npy"), labels)
    np.save(os.path.join(PROCESSED_DIR, "train_idx.npy"), train_idx)
    np.save(os.path.join(PROCESSED_DIR, "val_idx.npy"), val_idx)
    np.save(os.path.join(PROCESSED_DIR, "test_idx.npy"), test_idx)
    static_out.to_csv(os.path.join(PROCESSED_DIR, "static_features.csv"), index=False)
    pd.DataFrame({"feature": available, "mean": means, "std": stds}).to_csv(
        os.path.join(PROCESSED_DIR, "feature_params.csv"), index=False
    )
    cohort.to_csv(os.path.join(PROCESSED_DIR, "cohort.csv"), index=False)
    if notes_df is not None:
        notes_df.to_csv(os.path.join(PROCESSED_DIR, "clinical_notes.csv"), index=False)

    print(f"\n{'='*50}")
    print("DONE")
    print(f"{'='*50}")
    print(f"  Patients:   {n_patients:,}")
    print(f"  Features:   {n_features}")
    print(f"  Train:      {len(train_idx):,} ({labels[train_idx].mean():.3f} mortality)")
    print(f"  Val:        {len(val_idx):,} ({labels[val_idx].mean():.3f} mortality)")
    print(f"  Test:       {len(test_idx):,} ({labels[test_idx].mean():.3f} mortality)")
    print(f"\n  Next step: run notebooks 04 -> 09")


if __name__ == "__main__":
    main()
