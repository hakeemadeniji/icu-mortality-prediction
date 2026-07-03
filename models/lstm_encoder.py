"""
Bidirectional LSTM encoder for structured time-series ICU data.
Encodes sequences of vitals/labs over 48 hours into a fixed representation.
"""

import torch
import torch.nn as nn
from .attention import TemporalAttention


class LSTMEncoder(nn.Module):
    """
    Bidirectional LSTM with temporal attention for ICU time-series.

    Input: (batch, seq_len, input_dim) — hourly vitals/labs
    Output: (batch, hidden_dim) — patient-level representation
    """

    def __init__(self, input_dim: int, hidden_dim: int = 128,
                 num_layers: int = 2, dropout: float = 0.3,
                 bidirectional: bool = True):
        super().__init__()

        self.hidden_dim = hidden_dim
        self.bidirectional = bidirectional

        # Input normalization
        self.input_norm = nn.LayerNorm(input_dim)

        # Feature projection — map raw features to model dimension
        self.input_projection = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

        # Bidirectional LSTM
        self.lstm = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional,
        )

        # Temporal attention over LSTM outputs
        lstm_output_dim = hidden_dim * 2 if bidirectional else hidden_dim
        self.temporal_attention = TemporalAttention(lstm_output_dim)

        # Final projection
        self.output_projection = nn.Sequential(
            nn.Linear(lstm_output_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor, mask: torch.Tensor = None):
        """
        Args:
            x: (batch, seq_len, input_dim) — raw time-series features
            mask: (batch, seq_len) — 1 for valid time steps, 0 for padding

        Returns:
            representation: (batch, hidden_dim) — patient-level vector
            attention_weights: (batch, seq_len) — temporal attention weights
        """
        # Normalize and project input
        x = self.input_norm(x)
        x = self.input_projection(x)  # (batch, seq_len, hidden_dim)

        # Pack if mask provided (optional, for variable-length sequences)
        lstm_out, _ = self.lstm(x)  # (batch, seq_len, hidden_dim * 2)

        # Apply temporal attention
        context, attn_weights = self.temporal_attention(lstm_out, mask)

        # Project to output dimension
        representation = self.output_projection(context)

        return representation, attn_weights


class TransformerEncoder(nn.Module):
    """
    Transformer encoder for ICU time-series as an alternative to LSTM.

    Uses positional encoding and self-attention to capture temporal patterns.
    """

    def __init__(self, input_dim: int, d_model: int = 128,
                 nhead: int = 8, num_layers: int = 3,
                 dim_feedforward: int = 256, dropout: float = 0.2,
                 max_seq_len: int = 48):
        super().__init__()

        self.d_model = d_model

        # Input projection
        self.input_projection = nn.Linear(input_dim, d_model)

        # Positional encoding
        self.pos_encoding = nn.Parameter(torch.randn(1, max_seq_len, d_model) * 0.02)

        # Transformer encoder layers
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # Temporal attention for pooling
        self.temporal_attention = TemporalAttention(d_model)

        self.output_projection = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.ReLU(),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor, mask: torch.Tensor = None):
        """
        Args:
            x: (batch, seq_len, input_dim)
            mask: (batch, seq_len)

        Returns:
            representation: (batch, d_model)
            attention_weights: (batch, seq_len)
        """
        seq_len = x.size(1)
        x = self.input_projection(x)
        x = x + self.pos_encoding[:, :seq_len, :]

        # Create attention mask for transformer
        src_key_padding_mask = None
        if mask is not None:
            src_key_padding_mask = (mask == 0)  # True = ignore

        x = self.transformer(x, src_key_padding_mask=src_key_padding_mask)

        context, attn_weights = self.temporal_attention(x, mask)
        representation = self.output_projection(context)

        return representation, attn_weights
