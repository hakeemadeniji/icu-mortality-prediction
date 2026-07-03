"""
Multimodal Fusion Model: combines structured time-series encoder
with clinical text encoder via cross-modal attention.
"""

import torch
import torch.nn as nn
from .lstm_encoder import LSTMEncoder, TransformerEncoder
from .text_encoder import TextEncoder, SimpleTextEncoder
from .attention import CrossModalAttention, GatedFusion


class MultimodalFusionModel(nn.Module):
    """
    End-to-end multimodal model for ICU mortality prediction.

    Fuses structured time-series data with clinical notes using
    cross-modal attention or gated fusion.
    """

    def __init__(self, ts_input_dim: int, ts_hidden_dim: int = 128,
                 text_pretrained: str = "emilyalsentzer/Bio_ClinicalBERT",
                 text_projection_dim: int = 128,
                 fusion_method: str = "cross_attention",
                 fusion_hidden_dim: int = 128,
                 ts_encoder_type: str = "lstm",
                 freeze_bert: bool = True,
                 dropout: float = 0.3,
                 num_classes: int = 1):
        super().__init__()

        self.fusion_method = fusion_method
        self.ts_encoder_type = ts_encoder_type

        # ── Structured time-series encoder ──
        if ts_encoder_type == "lstm":
            self.ts_encoder = LSTMEncoder(
                input_dim=ts_input_dim,
                hidden_dim=ts_hidden_dim,
                num_layers=2,
                dropout=dropout,
                bidirectional=True,
            )
        else:
            self.ts_encoder = TransformerEncoder(
                input_dim=ts_input_dim,
                d_model=ts_hidden_dim,
                nhead=8,
                num_layers=3,
                dropout=dropout,
            )

        # ── Text encoder ──
        try:
            self.text_encoder = TextEncoder(
                pretrained_model=text_pretrained,
                projection_dim=text_projection_dim,
                freeze_bert=freeze_bert,
                dropout=dropout,
            )
            self.use_bert = True
        except Exception:
            print("ClinicalBERT not available. Using SimpleTextEncoder.")
            self.text_encoder = None
            self.use_bert = False

        # ── Fusion layer ──
        ts_out_dim = ts_hidden_dim
        text_out_dim = text_projection_dim

        if fusion_method == "cross_attention":
            self.fusion = CrossModalAttention(
                dim_q=ts_out_dim,
                dim_kv=text_out_dim,
                hidden_dim=fusion_hidden_dim,
                num_heads=4,
            )
            classifier_input_dim = fusion_hidden_dim + ts_out_dim
        elif fusion_method == "gated":
            self.fusion = GatedFusion(ts_out_dim, text_out_dim, fusion_hidden_dim)
            classifier_input_dim = fusion_hidden_dim
        else:  # concat
            self.fusion = None
            classifier_input_dim = ts_out_dim + text_out_dim

        # ── Classification head ──
        self.classifier = nn.Sequential(
            nn.Linear(classifier_input_dim, fusion_hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(fusion_hidden_dim, fusion_hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(fusion_hidden_dim // 2, num_classes),
        )

    def forward(self, ts_data: torch.Tensor, ts_mask: torch.Tensor = None,
                input_ids: torch.Tensor = None, attention_mask: torch.Tensor = None,
                tfidf_features: torch.Tensor = None):
        """
        Args:
            ts_data: (batch, seq_len, ts_input_dim) — time-series features
            ts_mask: (batch, seq_len) — valid time step mask
            input_ids: (batch, max_tokens) — tokenized clinical notes
            attention_mask: (batch, max_tokens) — token mask
            tfidf_features: (batch, vocab_size) — alternative text input

        Returns:
            logits: (batch, 1) — mortality prediction logit
            ts_attn: (batch, seq_len) — temporal attention weights
        """
        # Encode time-series
        ts_repr, ts_attn = self.ts_encoder(ts_data, ts_mask)

        # Encode text
        if self.use_bert and input_ids is not None:
            text_repr = self.text_encoder(input_ids, attention_mask)
        elif tfidf_features is not None and hasattr(self, "simple_text_encoder"):
            text_repr = self.simple_text_encoder(tfidf_features)
        else:
            # Text-free fallback: use only time-series
            logits = self.classifier(
                torch.cat([ts_repr, torch.zeros_like(ts_repr)], dim=-1)
                if self.fusion is None else ts_repr
            )
            return logits, ts_attn

        # Fuse modalities
        if self.fusion_method == "cross_attention":
            cross_attn_out = self.fusion(ts_repr, text_repr)
            fused = torch.cat([ts_repr, cross_attn_out], dim=-1)
        elif self.fusion_method == "gated":
            fused = self.fusion(ts_repr, text_repr)
        else:  # concat
            fused = torch.cat([ts_repr, text_repr], dim=-1)

        logits = self.classifier(fused)
        return logits, ts_attn


class SingleModalityModel(nn.Module):
    """
    Single-modality wrapper for ablation studies.
    Uses either time-series or text encoder alone.
    """

    def __init__(self, encoder: nn.Module, encoder_output_dim: int,
                 hidden_dim: int = 64, dropout: float = 0.3):
        super().__init__()
        self.encoder = encoder
        self.classifier = nn.Sequential(
            nn.Linear(encoder_output_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, *args, **kwargs):
        if hasattr(self.encoder, "temporal_attention"):
            repr_, attn = self.encoder(*args, **kwargs)
            return self.classifier(repr_), attn
        else:
            repr_ = self.encoder(*args, **kwargs)
            return self.classifier(repr_), None
