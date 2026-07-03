# %% [markdown]
# # 09 — Model Interpretability
# Explain predictions using SHAP values, temporal attention weights,
# and cross-modal attribution. Essential for clinical trust.

# %% Imports
import os, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import torch

sys.path.insert(0, os.path.join(".."))

PROCESSED_DIR = os.path.join("..", "data", "processed")
FIGURES_DIR = os.path.join("..", "results", "figures")
RESULTS_DIR = os.path.join("..", "results", "tables")

# Load data
ts_data = np.load(os.path.join(PROCESSED_DIR, "ts_normalized.npy"))
labels = np.load(os.path.join(PROCESSED_DIR, "labels.npy"))
test_idx = np.load(os.path.join(PROCESSED_DIR, "test_idx.npy"))
feature_params = pd.read_csv(os.path.join(PROCESSED_DIR, "feature_params.csv"))
feature_names = feature_params["feature"].tolist()

# %% [markdown]
# ## 1. SHAP Analysis for Baseline Models
# Global and local feature importance using SHAP TreeExplainer.

# %%
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("SHAP not installed. Run: pip install shap")


def run_shap_analysis(model, X_test, feature_names, model_name="XGBoost"):
    """Compute SHAP values and generate plots."""
    if not SHAP_AVAILABLE:
        print("SHAP not available. Skipping.")
        return None

    print(f"Computing SHAP values for {model_name}...")

    # Use TreeExplainer for tree models, KernelExplainer otherwise
    try:
        explainer = shap.TreeExplainer(model)
    except Exception:
        # Sample background for KernelExplainer
        background = shap.sample(X_test, min(100, len(X_test)))
        explainer = shap.KernelExplainer(model.predict_proba, background)

    shap_values = explainer.shap_values(X_test[:500])

    # Handle multi-output (take positive class)
    if isinstance(shap_values, list):
        shap_values = shap_values[1]

    # Summary plot (beeswarm)
    fig, ax = plt.subplots(figsize=(10, 8))
    shap.summary_plot(shap_values, X_test[:500],
                      feature_names=feature_names,
                      show=False, max_display=20)
    plt.title(f"SHAP Feature Importance — {model_name}")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, f"11_shap_summary_{model_name.lower()}.png"),
                dpi=200, bbox_inches="tight")
    plt.show()

    # Bar plot (mean absolute SHAP)
    fig, ax = plt.subplots(figsize=(8, 6))
    shap.summary_plot(shap_values, X_test[:500],
                      feature_names=feature_names,
                      plot_type="bar", show=False, max_display=15)
    plt.title(f"Mean |SHAP| — {model_name}")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, f"12_shap_bar_{model_name.lower()}.png"),
                dpi=200, bbox_inches="tight")
    plt.show()

    return shap_values


# Usage (after training baseline in notebook 05):
# from models.baselines import BaselineModels
# baselines = BaselineModels()
# ... train ...
# X_test_agg = baselines.aggregate_time_series(ts_data[test_idx], feature_names)
# shap_vals = run_shap_analysis(baselines.models["XGBoost"],
#                                baselines.scaler.transform(X_test_agg.values),
#                                list(X_test_agg.columns), "XGBoost")

print("SHAP: Load trained baseline model and call run_shap_analysis()")

# %% [markdown]
# ## 2. Temporal Attention Visualization
# Visualize which hours the LSTM/Transformer focuses on for each prediction.
# Highlights critical time points in the ICU trajectory.

# %%
def visualize_temporal_attention(ts_patient, attn_weights, feature_names,
                                 patient_id="Patient", prediction=None,
                                 true_label=None):
    """
    Visualize attention over time for a single patient.

    Args:
        ts_patient: (seq_len, n_features) — raw time-series
        attn_weights: (seq_len,) — attention weights from model
        feature_names: list of feature names
        patient_id: identifier string
        prediction: predicted probability
        true_label: actual outcome
    """
    hours = np.arange(len(attn_weights))

    fig, axes = plt.subplots(2, 1, figsize=(14, 8),
                              gridspec_kw={"height_ratios": [1, 3]})

    # Top: Attention weights as heatmap bar
    axes[0].bar(hours, attn_weights, color="orangered", alpha=0.8, width=1.0)
    axes[0].set_ylabel("Attention\nWeight")
    axes[0].set_xlim(-0.5, len(hours) - 0.5)
    title = f"Temporal Attention — {patient_id}"
    if prediction is not None:
        label = "Died" if true_label == 1 else "Survived"
        title += f"  |  Pred: {prediction:.3f}  |  Actual: {label}"
    axes[0].set_title(title)

    # Bottom: Feature trajectories with attention overlay
    # Select top 4 most variable features for this patient
    feat_vars = np.nanvar(ts_patient, axis=0)
    top_feat_idx = np.argsort(feat_vars)[-4:]

    for idx in top_feat_idx:
        axes[1].plot(hours, ts_patient[:, idx], label=feature_names[idx],
                     linewidth=1.5, alpha=0.8)

    # Overlay attention as background shading
    attn_norm = attn_weights / (attn_weights.max() + 1e-8)
    for h in range(len(hours)):
        if attn_norm[h] > 0.5:
            axes[1].axvspan(h - 0.5, h + 0.5, alpha=attn_norm[h] * 0.2,
                            color="orangered")

    axes[1].set_xlabel("Hour since ICU Admission")
    axes[1].set_ylabel("Feature Value (normalized)")
    axes[1].legend(fontsize=8, loc="upper right")
    axes[1].set_xlim(-0.5, len(hours) - 0.5)

    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, f"13_attention_{patient_id}.png"),
                dpi=200, bbox_inches="tight")
    plt.show()


# Example: visualize attention for a test patient
# Load saved attention weights from notebook 06/07 and call:
# visualize_temporal_attention(
#     ts_data[test_idx[0]],
#     lstm_attns[0],
#     feature_names,
#     patient_id="Test_0",
#     prediction=lstm_preds[0],
#     true_label=labels[test_idx[0]]
# )

print("Temporal attention: Load saved attention weights and call visualize_temporal_attention()")

# %% [markdown]
# ## 3. Aggregate Attention Patterns
# Average attention across all test patients to identify
# systematically important time windows.

# %%
def plot_aggregate_attention(attn_weights_all, labels_test):
    """
    Plot mean attention by group (survived vs died).

    Args:
        attn_weights_all: (n_patients, seq_len)
        labels_test: (n_patients,)
    """
    hours = np.arange(attn_weights_all.shape[1])

    fig, ax = plt.subplots(figsize=(12, 5))

    for label_val, label_name, color in [(0, "Survived", "#3498DB"),
                                          (1, "Died", "#E74C3C")]:
        mask = labels_test == label_val
        if mask.sum() == 0:
            continue
        mean_attn = attn_weights_all[mask].mean(axis=0)
        sem_attn = attn_weights_all[mask].std(axis=0) / np.sqrt(mask.sum())

        ax.plot(hours, mean_attn, label=label_name, color=color, linewidth=2)
        ax.fill_between(hours, mean_attn - sem_attn, mean_attn + sem_attn,
                        alpha=0.15, color=color)

    ax.set_xlabel("Hour since ICU Admission")
    ax.set_ylabel("Mean Attention Weight")
    ax.set_title("Aggregate Temporal Attention: When Does the Model Look?")
    ax.legend()
    ax.set_xlim(0, 47)

    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "14_aggregate_attention.png"), dpi=200)
    plt.show()


# Usage:
# plot_aggregate_attention(lstm_attns, labels[test_idx])

print("Aggregate attention: Load saved attention arrays and call plot_aggregate_attention()")

# %% [markdown]
# ## 4. Cross-Modal Attribution (Multimodal Model)
# Quantify how much the time-series vs text modality contributes
# to each prediction — a key advantage of our fusion architecture.

# %%
def modality_attribution(model, test_loader, device="cpu"):
    """
    Compute per-patient modality contributions by comparing
    full model vs single-modality ablations.

    Returns DataFrame with columns:
      ts_only_prob, text_only_prob, fusion_prob, ts_contribution, text_contribution
    """
    model.eval()
    results = []

    with torch.no_grad():
        for ts, mask, tfidf, y in test_loader:
            ts_dev = ts.to(device)
            mask_dev = mask.to(device)
            tfidf_dev = tfidf.to(device)

            # Full model prediction
            logits_full, _ = model(ts_dev, mask_dev, tfidf_dev)
            prob_full = torch.sigmoid(logits_full.squeeze()).cpu().numpy()

            # Time-series only (zero out text)
            zeros_text = torch.zeros_like(tfidf_dev)
            logits_ts, _ = model(ts_dev, mask_dev, zeros_text)
            prob_ts = torch.sigmoid(logits_ts.squeeze()).cpu().numpy()

            # Text only (zero out time-series)
            zeros_ts = torch.zeros_like(ts_dev)
            logits_text, _ = model(zeros_ts, mask_dev, tfidf_dev)
            prob_text = torch.sigmoid(logits_text.squeeze()).cpu().numpy()

            for i in range(len(prob_full)):
                results.append({
                    "fusion_prob": float(prob_full[i]) if prob_full.ndim > 0 else float(prob_full),
                    "ts_only_prob": float(prob_ts[i]) if prob_ts.ndim > 0 else float(prob_ts),
                    "text_only_prob": float(prob_text[i]) if prob_text.ndim > 0 else float(prob_text),
                    "true_label": float(y[i]),
                })

    df = pd.DataFrame(results)
    df["ts_contribution"] = (df["fusion_prob"] - df["text_only_prob"]).abs()
    df["text_contribution"] = (df["fusion_prob"] - df["ts_only_prob"]).abs()
    df["ts_pct"] = df["ts_contribution"] / (df["ts_contribution"] + df["text_contribution"] + 1e-8)

    return df


# Usage:
# attr_df = modality_attribution(fusion_model, mm_test_loader, device)
# print(f"Mean time-series contribution: {attr_df['ts_pct'].mean():.1%}")
# print(f"Mean text contribution: {1 - attr_df['ts_pct'].mean():.1%}")

print("Modality attribution: Load fusion model and call modality_attribution()")

# %% [markdown]
# ## 5. Clinical Case Studies
# Pick individual patients and walk through the model's reasoning.

# %%
def clinical_case_study(patient_idx, ts_data, labels, feature_names,
                         attn_weights=None, prediction=None):
    """Generate a clinical narrative for a single patient's prediction."""
    patient = ts_data[patient_idx]
    label = "Died" if labels[patient_idx] == 1 else "Survived"

    print(f"\n{'='*60}")
    print(f"CLINICAL CASE STUDY — Patient Index {patient_idx}")
    print(f"{'='*60}")
    print(f"Outcome: {label}")
    if prediction is not None:
        risk_level = "High" if prediction > 0.5 else "Low"
        print(f"Predicted mortality risk: {prediction:.3f} ({risk_level})")

    # Summarize key features
    print(f"\nFeature Summary (48h averages):")
    for i, feat in enumerate(feature_names):
        mean_val = np.nanmean(patient[:, i])
        std_val = np.nanstd(patient[:, i])
        trend = np.nan
        valid = patient[:, i][~np.isnan(patient[:, i])]
        if len(valid) > 1:
            trend = np.polyfit(range(len(valid)), valid, 1)[0]
        direction = "[up]" if trend > 0.01 else ("[dn]" if trend < -0.01 else "[-]")
        print(f"  {feat:20s}: mean={mean_val:+.2f}  std={std_val:.2f}  trend={direction}")

    # Attention peaks
    if attn_weights is not None:
        top_hours = np.argsort(attn_weights)[-3:][::-1]
        print(f"\nMost attended hours: {top_hours}")
        for h in top_hours:
            print(f"  Hour {h}: attention={attn_weights[h]:.4f}")

    print(f"{'='*60}\n")


# Example:
# clinical_case_study(test_idx[0], ts_data, labels, feature_names,
#                      attn_weights=lstm_attns[0], prediction=lstm_preds[0])

# Demonstrate with raw data
if len(test_idx) > 0:
    clinical_case_study(test_idx[0], ts_data, labels, feature_names)

# %% [markdown]
# ## Summary
# The interpretability analysis should reveal:
# 1. **Feature importance**: Which vitals/labs matter most (SHAP)
# 2. **Temporal patterns**: When in the ICU stay critical changes occur (attention)
# 3. **Modality balance**: How much text vs structured data contributes (attribution)
# 4. **Clinical validity**: Do model explanations align with clinical knowledge?
#
# These are essential for building trust with clinicians and demonstrating
# the model's reasoning in a portfolio presentation.
