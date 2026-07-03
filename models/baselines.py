"""
Traditional ML baseline models for ICU mortality prediction.
Logistic Regression, XGBoost, and LightGBM on static features.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (roc_auc_score, average_precision_score,
                             f1_score, classification_report)
from sklearn.calibration import calibration_curve
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold

try:
    import xgboost as xgb
except ImportError:
    xgb = None

try:
    import lightgbm as lgb
except ImportError:
    lgb = None


class BaselineModels:
    """
    Train and evaluate traditional ML baselines on static feature summaries.
    Time-series data is aggregated into statistical features (mean, std, min, max,
    trend) before feeding to these models.
    """

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.models = {}

    @staticmethod
    def aggregate_time_series(ts_data: np.ndarray, feature_names: list) -> pd.DataFrame:
        """
        Convert time-series to static features via statistical aggregation.

        Args:
            ts_data: (n_patients, seq_len, n_features)
            feature_names: list of feature names

        Returns:
            DataFrame with aggregated features
        """
        records = []
        for i in range(ts_data.shape[0]):
            patient = ts_data[i]  # (seq_len, n_features)
            row = {}
            for j, name in enumerate(feature_names):
                vals = patient[:, j]
                valid = vals[~np.isnan(vals)] if np.any(np.isnan(vals)) else vals
                if len(valid) == 0:
                    valid = np.array([0.0])
                row[f"{name}_mean"] = np.mean(valid)
                row[f"{name}_std"] = np.std(valid)
                row[f"{name}_min"] = np.min(valid)
                row[f"{name}_max"] = np.max(valid)
                row[f"{name}_last"] = valid[-1]
                # Trend: slope of linear fit
                if len(valid) > 1:
                    row[f"{name}_trend"] = np.polyfit(range(len(valid)), valid, 1)[0]
                else:
                    row[f"{name}_trend"] = 0.0
            records.append(row)
        return pd.DataFrame(records)

    def build_models(self):
        """Initialize all baseline models."""
        self.models = {
            "Logistic Regression": LogisticRegression(
                max_iter=1000, class_weight="balanced",
                random_state=self.random_state, C=0.1
            ),
            "Random Forest": RandomForestClassifier(
                n_estimators=200, max_depth=10,
                class_weight="balanced",
                random_state=self.random_state, n_jobs=-1
            ),
        }

        if xgb is not None:
            self.models["XGBoost"] = xgb.XGBClassifier(
                n_estimators=300, max_depth=6, learning_rate=0.05,
                scale_pos_weight=10,  # Adjust for class imbalance
                random_state=self.random_state, n_jobs=-1,
                eval_metric="aucpr",
            )

        if lgb is not None:
            self.models["LightGBM"] = lgb.LGBMClassifier(
                n_estimators=300, max_depth=6, learning_rate=0.05,
                is_unbalance=True,
                random_state=self.random_state, n_jobs=-1, verbose=-1,
            )

    def train_and_evaluate(self, X_train, y_train, X_test, y_test):
        """
        Train all baselines and return evaluation metrics.

        Returns:
            Dict of {model_name: {metric: value}}
        """
        self.build_models()

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        results = {}

        for name, model in self.models.items():
            print(f"\nTraining {name}...")
            model.fit(X_train_scaled, y_train)

            y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
            y_pred = (y_pred_proba >= 0.5).astype(int)

            metrics = {
                "auroc": roc_auc_score(y_test, y_pred_proba),
                "auprc": average_precision_score(y_test, y_pred_proba),
                "f1": f1_score(y_test, y_pred, zero_division=0),
                "report": classification_report(y_test, y_pred, zero_division=0),
            }

            results[name] = metrics
            print(f"  AUROC: {metrics['auroc']:.4f}  |  AUPRC: {metrics['auprc']:.4f}  |  F1: {metrics['f1']:.4f}")

        return results
