# %% [markdown]
# # 04 — Exploratory Data Analysis (Clinical)
# Visualize the ICU cohort: demographics, mortality distribution,
# vital sign trajectories, feature correlations, and missingness patterns.

# %% Imports
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

plt.rcParams.update({"font.size": 11, "figure.dpi": 150})

# %% Load data
PROCESSED_DIR = os.path.join("..", "data", "processed")
FIGURES_DIR = os.path.join("..", "results", "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

ts_data = np.load(os.path.join(PROCESSED_DIR, "ts_normalized.npy"))
labels = np.load(os.path.join(PROCESSED_DIR, "labels.npy"))
cohort = pd.read_csv(os.path.join(PROCESSED_DIR, "cohort.csv"))
static = pd.read_csv(os.path.join(PROCESSED_DIR, "static_features.csv"))
feature_params = pd.read_csv(os.path.join(PROCESSED_DIR, "feature_params.csv"))
feature_names = feature_params["feature"].tolist()

cohort["mortality_label"] = cohort["mortality"].map({0: "Survived", 1: "Died"})
print(f"Cohort: {len(cohort)} patients | Features: {len(feature_names)} | Seq len: {ts_data.shape[1]}")

# %% [markdown]
# ## 1. Cohort Demographics

# %%
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Age distribution by outcome
sns.histplot(data=cohort, x="age", hue="mortality_label", bins=30,
             kde=True, ax=axes[0, 0], palette=["#3498DB", "#E74C3C"], alpha=0.6)
axes[0, 0].set_title("Age Distribution by Outcome")
axes[0, 0].set_xlabel("Age (years)")

# Gender distribution
gender_mort = cohort.groupby(["gender", "mortality_label"]).size().unstack(fill_value=0)
gender_mort.plot(kind="bar", ax=axes[0, 1], color=["#3498DB", "#E74C3C"], edgecolor="black")
axes[0, 1].set_title("Gender × Mortality")
axes[0, 1].set_ylabel("Count")
axes[0, 1].tick_params(axis="x", rotation=0)

# Length of stay
sns.boxplot(data=cohort, x="mortality_label", y="los_hours",
            ax=axes[1, 0], palette=["#3498DB", "#E74C3C"])
axes[1, 0].set_title("Length of Stay by Outcome")
axes[1, 0].set_ylabel("Hours")
axes[1, 0].set_ylim(0, cohort["los_hours"].quantile(0.95))

# Mortality rate pie chart
mort_counts = cohort["mortality_label"].value_counts()
axes[1, 1].pie(mort_counts, labels=mort_counts.index, autopct="%1.1f%%",
               colors=["#3498DB", "#E74C3C"], startangle=90,
               textprops={"fontsize": 12})
axes[1, 1].set_title("Mortality Distribution")

plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "01_cohort_demographics.png"), dpi=200)
plt.show()

# %% [markdown]
# ## 2. Vital Sign Trajectories: Survivors vs Non-Survivors

# %%
key_vitals = ["heart_rate", "systolic_bp", "respiratory_rate",
              "spo2", "temperature", "glucose"]
available_vitals = [v for v in key_vitals if v in feature_names]

n_plots = len(available_vitals)
n_cols = min(3, n_plots)
n_rows = max(1, (n_plots + n_cols - 1) // n_cols)

fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 4 * n_rows))
if n_plots == 1:
    axes = np.array([axes])
axes = axes.flatten()

survived_mask = labels == 0
died_mask = labels == 1
hours = np.arange(ts_data.shape[1])

for i, feat in enumerate(available_vitals):
    feat_idx = feature_names.index(feat)
    ax = axes[i]

    for mask, label, color in [(survived_mask, "Survived", "#3498DB"),
                                (died_mask, "Died", "#E74C3C")]:
        data = ts_data[mask, :, feat_idx]
        mean = np.nanmean(data, axis=0)
        sem = np.nanstd(data, axis=0) / np.sqrt(max(mask.sum(), 1))

        ax.plot(hours, mean, label=label, color=color, linewidth=1.5)
        ax.fill_between(hours, mean - sem, mean + sem, alpha=0.15, color=color)

    ax.set_xlabel("Hour")
    ax.set_ylabel(f"{feat} (normalized)")
    ax.set_title(feat.replace("_", " ").title())
    ax.legend(fontsize=8)

for j in range(len(available_vitals), len(axes)):
    axes[j].set_visible(False)

plt.suptitle("Vital Sign Trajectories: Survivors vs Non-Survivors (Mean ± SEM)", y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "02_vital_trajectories.png"), dpi=200, bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 3. Feature Correlation with Mortality

# %%
mean_features = np.nanmean(ts_data, axis=1)
feat_df = pd.DataFrame(mean_features, columns=feature_names)
feat_df["mortality"] = labels

corr = feat_df.corr()
mort_corr = corr["mortality"].drop("mortality").sort_values()

fig, ax = plt.subplots(figsize=(8, max(5, len(mort_corr) * 0.3)))
colors = ["#E74C3C" if v > 0 else "#3498DB" for v in mort_corr]
ax.barh(range(len(mort_corr)), mort_corr.values, color=colors, edgecolor="black", linewidth=0.3)
ax.set_yticks(range(len(mort_corr)))
ax.set_yticklabels(mort_corr.index, fontsize=8)
ax.set_xlabel("Pearson Correlation with Mortality")
ax.set_title("Feature Correlation with In-Hospital Mortality")
ax.axvline(0, color="black", linewidth=0.5)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "03_mortality_correlation.png"), dpi=200)
plt.show()

# %% [markdown]
# ## 4. PCA of Patient Population

# %%
X_flat = mean_features.copy()
X_flat = np.nan_to_num(X_flat, nan=0)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_flat)

pca = PCA(n_components=5)
pcs = pca.fit_transform(X_scaled)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for label_val, label_name, color in [(0, "Survived", "#3498DB"), (1, "Died", "#E74C3C")]:
    mask = labels == label_val
    axes[0].scatter(pcs[mask, 0], pcs[mask, 1], c=color, label=label_name,
                    alpha=0.4, s=15, edgecolors="none")
axes[0].set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)")
axes[0].set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)")
axes[0].set_title("PCA: PC1 vs PC2 by Outcome")
axes[0].legend()

axes[1].bar(range(1, 6), pca.explained_variance_ratio_[:5] * 100, color="steelblue")
axes[1].set_xlabel("Component")
axes[1].set_ylabel("Variance Explained (%)")
axes[1].set_title("PCA Scree Plot")

plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "04_pca_population.png"), dpi=200)
plt.show()

# %% [markdown]
# ## 5. Feature-Feature Correlation Heatmap

# %%
fig, ax = plt.subplots(figsize=(12, 10))
feat_corr = feat_df[feature_names].corr()
mask_tri = np.triu(np.ones_like(feat_corr, dtype=bool), k=1)
sns.heatmap(feat_corr, mask=mask_tri, cmap="RdBu_r", center=0,
            vmin=-1, vmax=1, ax=ax, square=True,
            xticklabels=True, yticklabels=True,
            cbar_kws={"shrink": 0.7, "label": "Pearson r"})
ax.set_title("Feature-Feature Correlation (Mean Values)")
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "04b_feature_correlation.png"), dpi=200)
plt.show()

# %% [markdown]
# ## Summary
# Key observations to note:
# - Do survivors and non-survivors separate in PCA space?
# - Which vital signs diverge most between groups?
# - Any features highly correlated with mortality that confirm clinical intuition?
# - Class imbalance ratio — will inform loss weighting in deep learning models.
print(f"\nClass balance: {labels.mean()*100:.1f}% mortality ({labels.sum():.0f}/{len(labels)})")
