# %% [markdown]
# # 07 — Multimodal Fusion Model
# Combine structured time-series with clinical text via cross-modal attention.
# This is the advanced model that should outperform single-modality approaches.

# %% Imports
import os, sys
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score
from sklearn.feature_extraction.text import TfidfVectorizer

sys.path.insert(0, os.path.join(".."))
from models.fusion_model import MultimodalFusionModel
from models.text_encoder import SimpleTextEncoder

# %% Device
device = torch.device("cuda" if torch.cuda.is_available()
                       else "mps" if hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
                       else "cpu")
print(f"Device: {device}")

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
cohort = pd.read_csv(os.path.join(PROCESSED_DIR, "cohort.csv"))

INPUT_DIM = ts_data.shape[2]

# %% [markdown]
# ## Prepare Clinical Notes
# For Synthea: build synthetic notes from conditions, medications, and observations.
# For MIMIC-IV: load discharge summaries directly.

# %%
def build_synthea_notes(cohort, synthea_dir):
    """Create synthetic clinical notes from Synthea structured data."""
    csv_dir = synthea_dir
    for subdir in ["csv", "."]:
        check = os.path.join(synthea_dir, subdir)
        if os.path.exists(check) and any(f.endswith(".csv") for f in os.listdir(check)):
            csv_dir = check
            break

    conditions = pd.read_csv(os.path.join(csv_dir, "conditions.csv"))
    medications = pd.read_csv(os.path.join(csv_dir, "medications.csv"))

    notes = []
    for _, row in cohort.iterrows():
        pid = row["patient_id"]
        # Collect conditions
        pat_conds = conditions[conditions["PATIENT"] == pid]["DESCRIPTION"].tolist()
        pat_meds = medications[medications["PATIENT"] == pid]["DESCRIPTION"].tolist()

        note = f"Patient age {row['age']}, {row['gender']}. "
        if pat_conds:
            note += f"Active conditions: {', '.join(set(pat_conds[:15]))}. "
        if pat_meds:
            note += f"Current medications: {', '.join(set(pat_meds[:10]))}. "
        note += f"Length of stay: {row['los_hours']:.0f} hours."
        notes.append(note)

    return notes


def load_mimic_notes(cohort, mimic_dir):
    """Load discharge summaries from MIMIC-IV-Note."""
    notes_path = os.path.join(mimic_dir, "discharge.csv.gz")
    if not os.path.exists(notes_path):
        print("MIMIC-IV notes not found. Using placeholder notes.")
        return ["No clinical note available."] * len(cohort)

    discharge = pd.read_csv(notes_path)
    notes = []
    for _, row in cohort.iterrows():
        pat_notes = discharge[discharge["subject_id"] == row["patient_id"]]["text"]
        if len(pat_notes) > 0:
            # Use first 2000 chars of most recent note
            notes.append(str(pat_notes.iloc[-1])[:2000])
        else:
            notes.append("No clinical note available.")
    return notes


# Build notes
import yaml
with open(os.path.join("..", "configs", "config.yaml")) as f:
    config = yaml.safe_load(f)

if config["data"]["source"] == "synthea":
    clinical_notes = build_synthea_notes(cohort, os.path.join("..", "data", "synthea"))
else:
    clinical_notes = load_mimic_notes(cohort, os.path.join("..", "data", "raw", "mimic-iv"))

print(f"Clinical notes: {len(clinical_notes)}")
print(f"Sample note (truncated): {clinical_notes[0][:200]}...")

# %% Vectorize notes with TF-IDF
tfidf = TfidfVectorizer(max_features=1000, stop_words="english",
                        ngram_range=(1, 2), min_df=2)
tfidf_matrix = tfidf.fit_transform(clinical_notes).toarray().astype(np.float32)
print(f"TF-IDF matrix: {tfidf_matrix.shape}")

# %% [markdown]
# ## Multimodal Dataset

# %%
class MultimodalICUDataset(Dataset):
    def __init__(self, ts, mask, tfidf, labels, indices):
        self.ts = torch.FloatTensor(ts[indices])
        self.mask = torch.FloatTensor(mask[indices])
        self.tfidf = torch.FloatTensor(tfidf[indices])
        self.labels = torch.FloatTensor(labels[indices])

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.ts[idx], self.mask[idx], self.tfidf[idx], self.labels[idx]


BATCH_SIZE = 64
mm_train = MultimodalICUDataset(ts_data, ts_mask, tfidf_matrix, labels, train_idx)
mm_val = MultimodalICUDataset(ts_data, ts_mask, tfidf_matrix, labels, val_idx)
mm_test = MultimodalICUDataset(ts_data, ts_mask, tfidf_matrix, labels, test_idx)

train_loader = DataLoader(mm_train, batch_size=BATCH_SIZE, shuffle=True, drop_last=False)
val_loader = DataLoader(mm_val, batch_size=BATCH_SIZE, shuffle=False)
test_loader = DataLoader(mm_test, batch_size=BATCH_SIZE, shuffle=False)

pos_weight = torch.tensor([(1 - labels[train_idx].mean()) / max(labels[train_idx].mean(), 0.01)])

# %% [markdown]
# ## Build Multimodal Model (with SimpleTextEncoder for Synthea)

# %%
class MultimodalModel(nn.Module):
    """Multimodal model combining LSTM + TF-IDF text encoder."""

    def __init__(self, ts_input_dim, tfidf_dim, hidden_dim=128, dropout=0.3):
        super().__init__()
        from models.lstm_encoder import LSTMEncoder
        from models.attention import CrossModalAttention

        self.ts_encoder = LSTMEncoder(
            input_dim=ts_input_dim, hidden_dim=hidden_dim,
            num_layers=2, dropout=dropout, bidirectional=True
        )
        self.text_encoder = nn.Sequential(
            nn.Linear(tfidf_dim, hidden_dim * 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.LayerNorm(hidden_dim),
        )
        self.cross_attention = CrossModalAttention(
            dim_q=hidden_dim, dim_kv=hidden_dim,
            hidden_dim=hidden_dim, num_heads=4
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1),
        )

    def forward(self, ts, mask, tfidf):
        ts_repr, ts_attn = self.ts_encoder(ts, mask)
        text_repr = self.text_encoder(tfidf)
        cross_out = self.cross_attention(ts_repr, text_repr)
        fused = torch.cat([ts_repr, cross_out], dim=-1)
        logits = self.classifier(fused)
        return logits, ts_attn


model = MultimodalModel(
    ts_input_dim=INPUT_DIM,
    tfidf_dim=tfidf_matrix.shape[1],
    hidden_dim=128,
    dropout=0.3,
)
print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

# %% Train multimodal model
import matplotlib.pyplot as plt

model = model.to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)
criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight.to(device))

best_val_auprc = 0
patience_counter = 0
PATIENCE = 7
history = {"train_loss": [], "val_loss": [], "val_auroc": [], "val_auprc": []}
# Save initial weights so checkpoint always exists even if AUPRC never improves
torch.save(model.state_dict(), os.path.join(RESULTS_DIR, "best_fusion.pt"))

print("Training Multimodal Fusion Model...")
for epoch in range(50):
    model.train()
    train_losses = []
    for ts, mask, tfidf_feat, y in train_loader:
        ts = ts.to(device); mask = mask.to(device)
        tfidf_feat = tfidf_feat.to(device); y = y.to(device)

        optimizer.zero_grad()
        logits, _ = model(ts, mask, tfidf_feat)
        loss = criterion(logits.squeeze(), y)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        train_losses.append(loss.item())

    model.eval()
    val_losses, val_preds, val_labels_list = [], [], []
    with torch.no_grad():
        for ts, mask, tfidf_feat, y in val_loader:
            ts = ts.to(device); mask = mask.to(device)
            tfidf_feat = tfidf_feat.to(device); y = y.to(device)
            logits, _ = model(ts, mask, tfidf_feat)
            val_losses.append(criterion(logits.squeeze(), y).item())
            val_preds.extend(torch.sigmoid(logits.squeeze()).cpu().numpy())
            val_labels_list.extend(y.cpu().numpy())

    vp, vl = np.array(val_preds), np.array(val_labels_list)
    try:
        val_auroc = roc_auc_score(vl, vp)
        val_auprc = average_precision_score(vl, vp)
    except ValueError:
        val_auroc = val_auprc = 0.0

    history["train_loss"].append(np.mean(train_losses))
    history["val_loss"].append(np.mean(val_losses))
    history["val_auroc"].append(val_auroc)
    history["val_auprc"].append(val_auprc)
    scheduler.step(np.mean(val_losses))

    if (epoch + 1) % 5 == 0 or epoch == 0:
        print(f"  Epoch {epoch+1:3d} | Loss: {np.mean(train_losses):.4f} | "
              f"Val AUROC: {val_auroc:.4f} | Val AUPRC: {val_auprc:.4f}")

    if val_auprc > best_val_auprc:
        best_val_auprc = val_auprc
        patience_counter = 0
        torch.save(model.state_dict(), os.path.join(RESULTS_DIR, "best_fusion.pt"))
    else:
        patience_counter += 1
        if patience_counter >= PATIENCE:
            print(f"  Early stopping at epoch {epoch+1}")
            break

model.load_state_dict(torch.load(os.path.join(RESULTS_DIR, "best_fusion.pt"), weights_only=True))

# %% Evaluate on test set
model.eval()
test_preds, test_labels_list = [], []
with torch.no_grad():
    for ts, mask, tfidf_feat, y in test_loader:
        ts = ts.to(device); mask = mask.to(device); tfidf_feat = tfidf_feat.to(device)
        logits, _ = model(ts, mask, tfidf_feat)
        test_preds.extend(torch.sigmoid(logits.squeeze()).cpu().numpy())
        test_labels_list.extend(y.cpu().numpy())

tp, tl = np.array(test_preds), np.array(test_labels_list)
try:
    fusion_metrics = {
        "auroc": roc_auc_score(tl, tp),
        "auprc": average_precision_score(tl, tp),
        "f1": f1_score(tl, (tp >= 0.5).astype(int), zero_division=0),
    }
except ValueError:
    fusion_metrics = {"auroc": 0.0, "auprc": float(tl.mean()), "f1": 0.0}

print(f"\nMultimodal Fusion Test Results:")
for k, v in fusion_metrics.items():
    print(f"  {k}: {v:.4f}")

# %% Save
pd.DataFrame([fusion_metrics], index=["Multimodal Fusion"]).to_csv(
    os.path.join(RESULTS_DIR, "fusion_results.csv"))
print("[OK] Fusion results saved")
