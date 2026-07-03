# %% [markdown]
# # 06 — Deep Learning Models (LSTM & Transformer)
# Train single-modality deep learning models on time-series ICU data.

# %% Imports
import os, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score
from tqdm import tqdm

sys.path.insert(0, os.path.join(".."))
from models.lstm_encoder import LSTMEncoder, TransformerEncoder
from models.fusion_model import SingleModalityModel

# %% Device setup
if torch.cuda.is_available():
    device = torch.device("cuda")
elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")
print(f"Using device: {device}")

# %% Load data
PROCESSED_DIR = os.path.join("..", "data", "processed")
FIGURES_DIR = os.path.join("..", "results", "figures")
RESULTS_DIR = os.path.join("..", "results", "tables")

ts_data = np.load(os.path.join(PROCESSED_DIR, "ts_normalized.npy"))
ts_mask = np.load(os.path.join(PROCESSED_DIR, "ts_mask.npy"))
labels = np.load(os.path.join(PROCESSED_DIR, "labels.npy"))
train_idx = np.load(os.path.join(PROCESSED_DIR, "train_idx.npy"))
val_idx = np.load(os.path.join(PROCESSED_DIR, "val_idx.npy"))
test_idx = np.load(os.path.join(PROCESSED_DIR, "test_idx.npy"))

INPUT_DIM = ts_data.shape[2]
SEQ_LEN = ts_data.shape[1]
print(f"Input dim: {INPUT_DIM}, Seq len: {SEQ_LEN}")


# %% [markdown]
# ## PyTorch Dataset & DataLoader

# %%
class ICUDataset(Dataset):
    def __init__(self, ts, mask, labels, indices):
        self.ts = torch.FloatTensor(ts[indices])
        self.mask = torch.FloatTensor(mask[indices])
        self.labels = torch.FloatTensor(labels[indices])

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.ts[idx], self.mask[idx], self.labels[idx]


BATCH_SIZE = 64
train_ds = ICUDataset(ts_data, ts_mask, labels, train_idx)
val_ds = ICUDataset(ts_data, ts_mask, labels, val_idx)
test_ds = ICUDataset(ts_data, ts_mask, labels, test_idx)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, drop_last=False)
val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)
test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False)

# Handle class imbalance
pos_weight = torch.tensor([(1 - labels[train_idx].mean()) / max(labels[train_idx].mean(), 0.01)])
print(f"Positive weight: {pos_weight.item():.2f}")


# %% [markdown]
# ## Training Loop

# %%
def train_model(model, train_loader, val_loader, epochs=50, lr=1e-3,
                patience=7, model_name="model"):
    """Train a model with early stopping."""
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight.to(device))

    best_val_auprc = 0
    patience_counter = 0
    history = {"train_loss": [], "val_loss": [], "val_auroc": [], "val_auprc": []}
    # Save initial weights so checkpoint always exists even if AUPRC never improves
    torch.save(model.state_dict(), os.path.join(RESULTS_DIR, f"best_{model_name}.pt"))

    for epoch in range(epochs):
        # ── Train ──
        model.train()
        train_losses = []
        for ts, mask, y in train_loader:
            ts, mask, y = ts.to(device), mask.to(device), y.to(device)
            optimizer.zero_grad()
            logits, _ = model(ts, mask)
            loss = criterion(logits.squeeze(), y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_losses.append(loss.item())

        # ── Validate ──
        model.eval()
        val_losses, val_preds, val_labels = [], [], []
        with torch.no_grad():
            for ts, mask, y in val_loader:
                ts, mask, y = ts.to(device), mask.to(device), y.to(device)
                logits, _ = model(ts, mask)
                loss = criterion(logits.squeeze(), y)
                val_losses.append(loss.item())
                val_preds.extend(torch.sigmoid(logits.squeeze()).cpu().numpy())
                val_labels.extend(y.cpu().numpy())

        val_preds = np.array(val_preds)
        val_labels = np.array(val_labels)

        try:
            val_auroc = roc_auc_score(val_labels, val_preds)
            val_auprc = average_precision_score(val_labels, val_preds)
        except ValueError:
            val_auroc = val_auprc = 0.0

        history["train_loss"].append(np.mean(train_losses))
        history["val_loss"].append(np.mean(val_losses))
        history["val_auroc"].append(val_auroc)
        history["val_auprc"].append(val_auprc)

        scheduler.step(np.mean(val_losses))

        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"  Epoch {epoch+1:3d} | Train Loss: {np.mean(train_losses):.4f} | "
                  f"Val Loss: {np.mean(val_losses):.4f} | AUROC: {val_auroc:.4f} | AUPRC: {val_auprc:.4f}")

        # Early stopping
        if val_auprc > best_val_auprc:
            best_val_auprc = val_auprc
            patience_counter = 0
            torch.save(model.state_dict(), os.path.join(RESULTS_DIR, f"best_{model_name}.pt"))
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"  Early stopping at epoch {epoch+1}")
                break

    # Load best model
    model.load_state_dict(torch.load(os.path.join(RESULTS_DIR, f"best_{model_name}.pt"),
                                      weights_only=True))
    return model, history


def evaluate_model(model, test_loader):
    """Evaluate model on test set."""
    model.eval()
    all_preds, all_labels, all_attns = [], [], []

    with torch.no_grad():
        for ts, mask, y in test_loader:
            ts, mask, y = ts.to(device), mask.to(device), y.to(device)
            logits, attn = model(ts, mask)
            all_preds.extend(torch.sigmoid(logits.squeeze()).cpu().numpy())
            all_labels.extend(y.cpu().numpy())
            if attn is not None:
                all_attns.extend(attn.cpu().numpy())

    preds = np.array(all_preds)
    labels_arr = np.array(all_labels)

    try:
        metrics = {
            "auroc": roc_auc_score(labels_arr, preds),
            "auprc": average_precision_score(labels_arr, preds),
            "f1": f1_score(labels_arr, (preds >= 0.5).astype(int), zero_division=0),
        }
    except ValueError:
        metrics = {"auroc": 0.0, "auprc": float(labels_arr.mean()), "f1": 0.0}
    return metrics, preds, labels_arr, np.array(all_attns) if all_attns else None


# %% [markdown]
# ## Train BiLSTM Model

# %%
print("=" * 50)
print("Training BiLSTM Model")
print("=" * 50)

lstm_encoder = LSTMEncoder(input_dim=INPUT_DIM, hidden_dim=128,
                           num_layers=2, dropout=0.3, bidirectional=True)
lstm_model = SingleModalityModel(lstm_encoder, encoder_output_dim=128, hidden_dim=64)

lstm_model, lstm_history = train_model(lstm_model, train_loader, val_loader,
                                        epochs=50, lr=1e-3, model_name="lstm")
lstm_metrics, lstm_preds, lstm_labels, lstm_attns = evaluate_model(lstm_model, test_loader)

print(f"\nLSTM Test Results:")
for k, v in lstm_metrics.items():
    print(f"  {k}: {v:.4f}")

# %% [markdown]
# ## Train Transformer Model

# %%
print("\n" + "=" * 50)
print("Training Transformer Model")
print("=" * 50)

transformer_encoder = TransformerEncoder(input_dim=INPUT_DIM, d_model=128,
                                          nhead=8, num_layers=3, dropout=0.2)
transformer_model = SingleModalityModel(transformer_encoder, encoder_output_dim=128, hidden_dim=64)

transformer_model, transformer_history = train_model(
    transformer_model, train_loader, val_loader,
    epochs=50, lr=5e-4, model_name="transformer"
)
transformer_metrics, trans_preds, trans_labels, trans_attns = evaluate_model(
    transformer_model, test_loader
)

print(f"\nTransformer Test Results:")
for k, v in transformer_metrics.items():
    print(f"  {k}: {v:.4f}")

# %% Plot training curves
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

for name, history in [("LSTM", lstm_history), ("Transformer", transformer_history)]:
    axes[0].plot(history["train_loss"], label=f"{name} Train", alpha=0.8)
    axes[0].plot(history["val_loss"], label=f"{name} Val", ls="--", alpha=0.8)
    axes[1].plot(history["val_auroc"], label=f"{name} AUROC", alpha=0.8)
    axes[1].plot(history["val_auprc"], label=f"{name} AUPRC", ls="--", alpha=0.8)

axes[0].set_xlabel("Epoch")
axes[0].set_ylabel("Loss")
axes[0].set_title("Training & Validation Loss")
axes[0].legend()

axes[1].set_xlabel("Epoch")
axes[1].set_ylabel("Score")
axes[1].set_title("Validation Metrics")
axes[1].legend()

plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "07_dl_training_curves.png"), dpi=200)
plt.show()

# %% Save results
dl_results = pd.DataFrame({
    "BiLSTM": lstm_metrics,
    "Transformer": transformer_metrics,
}).T
dl_results.to_csv(os.path.join(RESULTS_DIR, "dl_results.csv"))
print(f"\n[OK] Deep learning results saved")
print(dl_results)
