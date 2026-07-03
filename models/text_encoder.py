"""
Text encoder for clinical notes using pre-trained ClinicalBERT / BioBERT.
Extracts dense representations from discharge summaries and nursing notes.
"""

import torch
import torch.nn as nn


class TextEncoder(nn.Module):
    """
    Encodes clinical notes using a pre-trained BERT variant.
    Uses frozen BERT weights with a trainable projection head.

    Input: tokenized text (input_ids, attention_mask)
    Output: (batch, projection_dim) fixed-size text representation
    """

    def __init__(self, pretrained_model: str = "emilyalsentzer/Bio_ClinicalBERT",
                 projection_dim: int = 128, freeze_bert: bool = True,
                 dropout: float = 0.2):
        super().__init__()

        from transformers import AutoModel

        self.bert = AutoModel.from_pretrained(pretrained_model)
        self.bert_hidden_dim = self.bert.config.hidden_size  # Typically 768

        # Freeze BERT weights to save compute
        if freeze_bert:
            for param in self.bert.parameters():
                param.requires_grad = False

        # Projection from BERT space to shared representation space
        self.projection = nn.Sequential(
            nn.Linear(self.bert_hidden_dim, projection_dim * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(projection_dim * 2, projection_dim),
            nn.LayerNorm(projection_dim),
        )

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor):
        """
        Args:
            input_ids: (batch, max_tokens) — tokenized text
            attention_mask: (batch, max_tokens) — 1 for real tokens, 0 for padding

        Returns:
            representation: (batch, projection_dim)
        """
        # Get BERT outputs
        with torch.set_grad_enabled(self.training and any(p.requires_grad for p in self.bert.parameters())):
            outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)

        # Use [CLS] token embedding as sentence representation
        cls_embedding = outputs.last_hidden_state[:, 0, :]  # (batch, 768)

        # Project to shared dimension
        representation = self.projection(cls_embedding)

        return representation


class SimpleTextEncoder(nn.Module):
    """
    Lightweight text encoder using TF-IDF + MLP.
    Use this when ClinicalBERT is too heavy or for Synthea data
    where clinical notes are simpler.
    """

    def __init__(self, vocab_size: int, embedding_dim: int = 128,
                 output_dim: int = 128, dropout: float = 0.3):
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Linear(vocab_size, embedding_dim * 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(embedding_dim * 2, embedding_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(embedding_dim, output_dim),
            nn.LayerNorm(output_dim),
        )

    def forward(self, tfidf_features: torch.Tensor):
        """
        Args:
            tfidf_features: (batch, vocab_size) — TF-IDF vector

        Returns:
            representation: (batch, output_dim)
        """
        return self.encoder(tfidf_features)
