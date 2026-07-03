"""
End-to-end training script for ICU Mortality Prediction.
Runs all models sequentially and saves results.

Usage:
    python scripts/train.py --config configs/config.yaml
    python scripts/train.py --model lstm --epochs 30
    python scripts/train.py --model all
"""

import argparse
import os
import sys
import numpy as np
import pandas as pd
import yaml
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score

# Add project root to path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from models.baselines import BaselineModels
from models.lstm_encoder import LSTMEncoder, TransformerEncoder
from models.fusion_model import SingleModalityModel


class ICUDataset(Dataset):
    def __init__(self, ts, mask, labels, indices):
        self.ts = torch.FloatTensor(ts[indices])
        self.mask = torch.FloatTensor(mask[indices])
        self.labels = torch.FloatTensor(labels[indices])

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.ts[idx], self.mask[idx], self.labels[idx]


def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def train_dl_model(model, train_loader, val_loader, device, epochs=50,
                   lr=1e-3, patience=7, pos_weight=1.0, model_name="model",
                   save_dir="results/tables"):
    """Train a deep learning model with early stopping."""
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)
    criterion = nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor([pos_weight]).to(device)
    )

    best_val_auprc = 0
    patience_counter = 0

    for epoch in range(epochs):
        model.train()
        for ts, mask, y in train_loader:
            ts, mask, y = ts.to(device), mask.to(device), y.to(device)
            optimizer.zero_grad()
            logits, _ = model(ts, mask)
            loss = criterion(logits.squeeze(), y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

        # Validate
        model.eval()
        val_preds, val_labels = [], []
        val_loss_sum = 0
        with torch.no_grad():
            for ts, mask, y in val_loader:
                ts, mask, y = ts.to(device), mask.to(device), y.to(device)
                logits, _ = model(ts, mask)
                val_loss_sum += criterion(logits.squeeze(), y).item()
                val_preds.extend(torch.sigmoid(logits.squeeze()).cpu().numpy())
                val_labels.extend(y.cpu().numpy())

        vp, vl = np.array(val_preds), np.array(val_labels)
        try:
            val_auroc = roc_auc_score(vl, vp)
            val_auprc = average_precision_score(vl, vp)
        except ValueError:
            val_auroc = val_auprc = 0.0

        scheduler.step(val_loss_sum)

        if (epoch + 1) % 10 == 0:
            print(f"  [{model_name}] Epoch {epoch+1}: AUROC={val_auroc:.4f} AUPRC={val_auprc:.4f}")

        if val_auprc > best_val_auprc:
            best_val_auprc = val_auprc
            patience_counter = 0
            torch.save(model.state_dict(),
                       os.path.join(save_dir, f"best_{model_name}.pt"))
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"  [{model_name}] Early stopping at epoch {epoch+1}")
                break

    model.load_state_dict(
        torch.load(os.path.join(save_dir, f"best_{model_name}.pt"), weights_only=True)
    )
    return model


def evaluate(model, test_loader, device):
    model.eval()
    preds, labels_list = [], []
    with torch.no_grad():
        for ts, mask, y in test_loader:
            ts, mask, y = ts.to(device), mask.to(device), y.to(device)
            logits, _ = model(ts, mask)
            preds.extend(torch.sigmoid(logits.squeeze()).cpu().numpy())
            labels_list.extend(y.cpu().numpy())
    p, l = np.array(preds), np.array(labels_list)
    return {
        "auroc": roc_auc_score(l, p),
        "auprc": average_precision_score(l, p),
        "f1": f1_score(l, (p >= 0.5).astype(int), zero_division=0),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--model", default="all", choices=["baseline", "lstm", "transformer", "all"])
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()

    # Load config
    with open(os.path.join(ROOT, args.config)) as f:
        config = yaml.safe_load(f)

    proc_dir = os.path.join(ROOT, "data", "processed")
    save_dir = os.path.join(ROOT, "results", "tables")
    os.makedirs(save_dir, exist_ok=True)

    # Load data
    print("Loading data...")
    ts_data = np.load(os.path.join(proc_dir, "ts_normalized.npy"))
    ts_mask = np.load(os.path.join(proc_dir, "ts_mask.npy"))
    labels = np.load(os.path.join(proc_dir, "labels.npy"))
    train_idx = np.load(os.path.join(proc_dir, "train_idx.npy"))
    val_idx = np.load(os.path.join(proc_dir, "val_idx.npy"))
    test_idx = np.load(os.path.join(proc_dir, "test_idx.npy"))
    feature_params = pd.read_csv(os.path.join(proc_dir, "feature_params.csv"))

    input_dim = ts_data.shape[2]
    pos_weight = (1 - labels[train_idx].mean()) / max(labels[train_idx].mean(), 0.01)
    device = get_device()

    print(f"Device: {device}")
    print(f"Shape: {ts_data.shape} | Mortality: {labels.mean():.3f}")

    all_results = {}

    # ── Baselines ──
    if args.model in ["baseline", "all"]:
        print("\n=== Training Baselines ===")
        baselines = BaselineModels()
        feature_names = feature_params["feature"].tolist()
        agg = baselines.aggregate_time_series(ts_data, feature_names)
        static = pd.read_csv(os.path.join(proc_dir, "static_features.csv"))
        agg["age"] = static["age"].values
        agg["gender"] = static["gender"].values

        X_train = np.vstack([agg.iloc[train_idx].values, agg.iloc[val_idx].values])
        y_train = np.concatenate([labels[train_idx], labels[val_idx]])
        results = baselines.train_and_evaluate(X_train, y_train,
                                                agg.iloc[test_idx].values, labels[test_idx])
        all_results.update(results)

    # ── LSTM ──
    if args.model in ["lstm", "all"]:
        print("\n=== Training BiLSTM ===")
        train_ds = ICUDataset(ts_data, ts_mask, labels, train_idx)
        val_ds = ICUDataset(ts_data, ts_mask, labels, val_idx)
        test_ds = ICUDataset(ts_data, ts_mask, labels, test_idx)
        train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, drop_last=True)
        val_loader = DataLoader(val_ds, batch_size=args.batch_size)
        test_loader = DataLoader(test_ds, batch_size=args.batch_size)

        encoder = LSTMEncoder(input_dim=input_dim, hidden_dim=128, num_layers=2,
                               dropout=0.3, bidirectional=True)
        model = SingleModalityModel(encoder, encoder_output_dim=128, hidden_dim=64)
        model = train_dl_model(model, train_loader, val_loader, device,
                               epochs=args.epochs, pos_weight=pos_weight,
                               model_name="lstm", save_dir=save_dir)
        all_results["BiLSTM"] = evaluate(model, test_loader, device)

    # ── Transformer ──
    if args.model in ["transformer", "all"]:
        print("\n=== Training Transformer ===")
        if "train_loader" not in dir():
            train_ds = ICUDataset(ts_data, ts_mask, labels, train_idx)
            val_ds = ICUDataset(ts_data, ts_mask, labels, val_idx)
            test_ds = ICUDataset(ts_data, ts_mask, labels, test_idx)
            train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, drop_last=True)
            val_loader = DataLoader(val_ds, batch_size=args.batch_size)
            test_loader = DataLoader(test_ds, batch_size=args.batch_size)

        encoder = TransformerEncoder(input_dim=input_dim, d_model=128, nhead=8,
                                      num_layers=3, dropout=0.2)
        model = SingleModalityModel(encoder, encoder_output_dim=128, hidden_dim=64)
        model = train_dl_model(model, train_loader, val_loader, device,
                               epochs=args.epochs, lr=5e-4, pos_weight=pos_weight,
                               model_name="transformer", save_dir=save_dir)
        all_results["Transformer"] = evaluate(model, test_loader, device)

    # ── Save all results ──
    if all_results:
        # Remove non-numeric entries
        clean = {}
        for name, metrics in all_results.items():
            clean[name] = {k: v for k, v in metrics.items() if isinstance(v, (int, float))}
        results_df = pd.DataFrame(clean).T
        results_df.to_csv(os.path.join(save_dir, "all_model_results.csv"))
        print(f"\n{'='*60}")
        print("FINAL RESULTS")
        print(f"{'='*60}")
        print(results_df.round(4))


if __name__ == "__main__":
    main()
