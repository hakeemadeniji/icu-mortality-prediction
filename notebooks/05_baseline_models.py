# %% [markdown]
# # 05 — Baseline Models
# Train traditional ML models on static aggregated features.
# These serve as the performance floor for deep learning models.

# %% Imports
import os, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (roc_auc_score, average_precision_score, f1_score,
                             roc_curve, precision_recall_curve, confusion_matrix,
                             classification_report)

sys.path.insert(0, os.path.join("..", "models"))
from baselines import BaselineModels

# %% Load data
PROCESSED_DIR = os.path.join("..", "data", "processed")
FIGURES_DIR = os.path.join("..", "results", "figures")
RESULTS_DIR = os.path.join("..", "results", "tables")
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

ts_data = np.load(os.path.join(PROCESSED_DIR, "ts_normalized.npy"))
labels = np.load(os.path.join(PROCESSED_DIR, "labels.npy"))
train_idx = np.load(os.path.join(PROCESSED_DIR, "train_idx.npy"))
val_idx = np.load(os.path.join(PROCESSED_DIR, "val_idx.npy"))
test_idx = np.load(os.path.join(PROCESSED_DIR, "test_idx.npy"))
feature_params = pd.read_csv(os.path.join(PROCESSED_DIR, "feature_params.csv"))
static = pd.read_csv(os.path.join(PROCESSED_DIR, "static_features.csv"))

feature_names = feature_params["feature"].tolist()
print(f"Time-series shape: {ts_data.shape}")
print(f"Train/Val/Test: {len(train_idx)}/{len(val_idx)}/{len(test_idx)}")

# %% Aggregate time-series to static features
baselines = BaselineModels(random_state=42)
agg_features = baselines.aggregate_time_series(ts_data, feature_names)

# Add demographic features
agg_features["age"] = static["age"].values
agg_features["gender"] = static["gender"].values
agg_features["los_hours"] = static["los_hours"].values

print(f"Aggregated feature matrix: {agg_features.shape}")
print(f"Features: {list(agg_features.columns[:10])}... ({len(agg_features.columns)} total)")

# %% Split
X_train = agg_features.iloc[train_idx].values
X_val = agg_features.iloc[val_idx].values
X_test = agg_features.iloc[test_idx].values
y_train = labels[train_idx]
y_val = labels[val_idx]
y_test = labels[test_idx]

# Combine train + val for final baseline training
X_train_full = np.vstack([X_train, X_val])
y_train_full = np.concatenate([y_train, y_val])

# %% Train and evaluate baselines
results = baselines.train_and_evaluate(X_train_full, y_train_full, X_test, y_test)

# %% Plot ROC and PR curves
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for name, model in baselines.models.items():
    X_test_scaled = baselines.scaler.transform(X_test)
    y_proba = model.predict_proba(X_test_scaled)[:, 1]

    # ROC
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    auroc = roc_auc_score(y_test, y_proba)
    axes[0].plot(fpr, tpr, label=f"{name} (AUROC={auroc:.3f})")

    # PR
    prec, rec, _ = precision_recall_curve(y_test, y_proba)
    auprc = average_precision_score(y_test, y_proba)
    axes[1].plot(rec, prec, label=f"{name} (AUPRC={auprc:.3f})")

axes[0].plot([0, 1], [0, 1], "k--", alpha=0.3)
axes[0].set_xlabel("False Positive Rate")
axes[0].set_ylabel("True Positive Rate")
axes[0].set_title("ROC Curves — Baseline Models")
axes[0].legend(fontsize=9)

baseline_prev = y_test.mean()
axes[1].axhline(baseline_prev, color="k", ls="--", alpha=0.3, label=f"Baseline ({baseline_prev:.3f})")
axes[1].set_xlabel("Recall")
axes[1].set_ylabel("Precision")
axes[1].set_title("Precision-Recall Curves — Baseline Models")
axes[1].legend(fontsize=9)

plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "05_baseline_curves.png"), dpi=200)
plt.show()

# %% Feature importance (XGBoost)
if "XGBoost" in baselines.models:
    model = baselines.models["XGBoost"]
    importances = model.feature_importances_
    feat_names = list(agg_features.columns)
    top_n = 20

    top_idx = np.argsort(importances)[-top_n:]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(range(top_n), importances[top_idx], color="steelblue")
    ax.set_yticks(range(top_n))
    ax.set_yticklabels([feat_names[i] for i in top_idx], fontsize=8)
    ax.set_xlabel("Feature Importance")
    ax.set_title("Top 20 Features — XGBoost")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "06_xgboost_importance.png"), dpi=200)
    plt.show()

# %% Save baseline results
results_df = pd.DataFrame({
    name: {k: v for k, v in metrics.items() if k != "report"}
    for name, metrics in results.items()
}).T
results_df.to_csv(os.path.join(RESULTS_DIR, "baseline_results.csv"))
print(f"\n[OK] Baseline results saved")
print(results_df)
