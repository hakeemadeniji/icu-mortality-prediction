# %% [markdown]
# # 08 — Model Evaluation & Fairness Analysis
# Compare all models side-by-side, assess calibration,
# and evaluate fairness across demographic groups.

# %% Imports
import os, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (roc_auc_score, average_precision_score, f1_score,
                             roc_curve, precision_recall_curve,
                             confusion_matrix, classification_report)
from sklearn.calibration import calibration_curve

PROCESSED_DIR = os.path.join("..", "data", "processed")
FIGURES_DIR = os.path.join("..", "results", "figures")
RESULTS_DIR = os.path.join("..", "results", "tables")
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# %% Load all model results
# These CSVs are saved by notebooks 05, 06, 07
baseline_results = None
dl_results = None
fusion_results = None

for fname, var_name in [("baseline_results.csv", "baseline"),
                         ("dl_results.csv", "dl"),
                         ("fusion_results.csv", "fusion")]:
    path = os.path.join(RESULTS_DIR, fname)
    if os.path.exists(path):
        df = pd.read_csv(path, index_col=0)
        if var_name == "baseline":
            baseline_results = df
        elif var_name == "dl":
            dl_results = df
        else:
            fusion_results = df
        print(f"Loaded {fname}: {df.shape}")

# Combine all results
all_results = pd.concat([
    r for r in [baseline_results, dl_results, fusion_results] if r is not None
])

if len(all_results) == 0:
    print("No results found. Run notebooks 05-07 first.")
else:
    print(f"\nAll model results:")
    print(all_results.round(4))

# %% [markdown]
# ## 1. Model Comparison Bar Chart

# %%
if len(all_results) > 0:
    metrics_to_plot = [c for c in ["auroc", "auprc", "f1"] if c in all_results.columns]

    fig, axes = plt.subplots(1, len(metrics_to_plot), figsize=(5 * len(metrics_to_plot), 6))
    if len(metrics_to_plot) == 1:
        axes = [axes]

    colors = plt.cm.Set2(np.linspace(0, 1, len(all_results)))

    for i, metric in enumerate(metrics_to_plot):
        values = all_results[metric].values
        model_names = all_results.index.tolist()

        bars = axes[i].bar(range(len(model_names)), values, color=colors,
                           edgecolor="black", linewidth=0.5)

        # Label bars
        for bar, val in zip(bars, values):
            axes[i].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                         f"{val:.3f}", ha="center", fontsize=8)

        axes[i].set_xticks(range(len(model_names)))
        axes[i].set_xticklabels(model_names, rotation=45, ha="right", fontsize=9)
        axes[i].set_ylabel(metric.upper())
        axes[i].set_title(metric.upper())
        axes[i].set_ylim(0, min(1.0, max(values) * 1.2))

    plt.suptitle("Model Performance Comparison", fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "08_model_comparison.png"), dpi=200, bbox_inches="tight")
    plt.show()

# %% [markdown]
# ## 2. Calibration Analysis
# A well-calibrated model should have predicted probabilities that match
# observed frequencies. Critical for clinical decision-making.

# %%
# This section requires saved prediction arrays.
# If you've saved predictions from each model, load and plot here.
# Below is the template:

def plot_calibration(y_true, predictions_dict, n_bins=10):
    """Plot calibration curves for multiple models."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for name, y_pred in predictions_dict.items():
        fraction_of_positives, mean_predicted_value = calibration_curve(
            y_true, y_pred, n_bins=n_bins, strategy="uniform"
        )
        axes[0].plot(mean_predicted_value, fraction_of_positives,
                     marker="o", label=name, linewidth=1.5)

        # Prediction distribution
        axes[1].hist(y_pred, bins=50, alpha=0.4, label=name)

    axes[0].plot([0, 1], [0, 1], "k--", alpha=0.5, label="Perfect")
    axes[0].set_xlabel("Mean Predicted Probability")
    axes[0].set_ylabel("Fraction of Positives")
    axes[0].set_title("Calibration Curves")
    axes[0].legend(fontsize=8)

    axes[1].set_xlabel("Predicted Probability")
    axes[1].set_ylabel("Count")
    axes[1].set_title("Prediction Distribution")
    axes[1].legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "09_calibration.png"), dpi=200)
    plt.show()


# Example usage (uncomment when predictions are available):
# predictions = {
#     "XGBoost": xgb_preds,
#     "BiLSTM": lstm_preds,
#     "Fusion": fusion_preds,
# }
# plot_calibration(y_test, predictions)

print("Calibration plots: load saved predictions from each model and call plot_calibration().")

# %% [markdown]
# ## 3. Fairness Analysis
# Evaluate model performance across demographic subgroups to detect bias.

# %%
cohort = pd.read_csv(os.path.join(PROCESSED_DIR, "cohort.csv"))
labels = np.load(os.path.join(PROCESSED_DIR, "labels.npy"))
test_idx = np.load(os.path.join(PROCESSED_DIR, "test_idx.npy"))

test_cohort = cohort.iloc[test_idx].copy()
test_cohort["mortality"] = labels[test_idx]


def fairness_analysis(y_true, y_pred, group_labels, group_name):
    """Compute metrics per demographic group."""
    results = []
    unique_groups = np.unique(group_labels)

    for group in unique_groups:
        mask = group_labels == group
        if mask.sum() < 10:
            continue

        group_true = y_true[mask]
        group_pred = y_pred[mask]

        try:
            auroc = roc_auc_score(group_true, group_pred)
        except ValueError:
            auroc = np.nan
        try:
            auprc = average_precision_score(group_true, group_pred)
        except ValueError:
            auprc = np.nan

        results.append({
            "group": group,
            "n_patients": mask.sum(),
            "mortality_rate": group_true.mean(),
            "auroc": auroc,
            "auprc": auprc,
        })

    df = pd.DataFrame(results)
    print(f"\nFairness Analysis — {group_name}:")
    print(df.round(4).to_string(index=False))

    # Compute Equalized Odds Difference (EOD)
    if len(df) >= 2 and df["auroc"].notna().sum() >= 2:
        auroc_range = df["auroc"].max() - df["auroc"].min()
        print(f"  AUROC range across groups: {auroc_range:.4f}")
        if auroc_range > 0.10:
            print(f"  ⚠ Potential fairness concern: >10% AUROC gap")

    return df


# Template for fairness analysis (fill in predictions):
# Gender fairness
print("\n--- Fairness analysis templates ---")
print("After running models, call:")
print('  fairness_analysis(y_test, y_pred, test_cohort["gender"].values, "Gender")')

# Age group fairness
cohort["age_group"] = pd.cut(cohort["age"], bins=[18, 40, 60, 80, 120],
                              labels=["18-39", "40-59", "60-79", "80+"])
print('  fairness_analysis(y_test, y_pred, test_cohort["age_group"].values, "Age Group")')

# Race fairness (if available)
if "race" in test_cohort.columns:
    print('  fairness_analysis(y_test, y_pred, test_cohort["race"].values, "Race")')

# %% [markdown]
# ## 4. Confusion Matrix for Best Model

# %%
def plot_confusion_matrix(y_true, y_pred_binary, model_name="Model"):
    """Plot a formatted confusion matrix."""
    cm = confusion_matrix(y_true, y_pred_binary)

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                xticklabels=["Survived", "Died"],
                yticklabels=["Survived", "Died"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(f"Confusion Matrix — {model_name}")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, f"10_confusion_{model_name.lower().replace(' ', '_')}.png"),
                dpi=200)
    plt.show()

    print(classification_report(y_true, y_pred_binary,
                                 target_names=["Survived", "Died"], zero_division=0))


# Usage:
# plot_confusion_matrix(y_test, (fusion_preds >= 0.5).astype(int), "Multimodal Fusion")

# %% Save combined results
all_results.to_csv(os.path.join(RESULTS_DIR, "all_model_results.csv"))
print(f"\n[OK] All results saved: {len(all_results)} models compared")
