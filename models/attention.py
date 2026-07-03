"""
Attention mechanisms for temporal and cross-modal fusion.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class TemporalAttention(nn.Module):
    """
    Additive attention over time steps.
    Given a sequence of hidden states, produces a weighted summary vector.
    """

    def __init__(self, hidden_dim: int):
        super().__init__()
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.Tanh(),
            nn.Linear(hidden_dim // 2, 1, bias=False),
        )

    def forward(self, hidden_states: torch.Tensor, mask: torch.Tensor = None):
        """
        Args:
            hidden_states: (batch, seq_len, hidden_dim)
            mask: (batch, seq_len) — 1 for valid, 0 for padding

        Returns:
            context: (batch, hidden_dim) — attention-weighted summary
            weights: (batch, seq_len) — attention weights
        """
        scores = self.attention(hidden_states).squeeze(-1)  # (batch, seq_len)

        if mask is not None:
            scores = scores.masked_fill(mask == 0, float("-inf"))

        weights = F.softmax(scores, dim=-1)  # (batch, seq_len)
        context = torch.bmm(weights.unsqueeze(1), hidden_states).squeeze(1)

        return context, weights


class CrossModalAttention(nn.Module):
    """
    Cross-modal attention: one modality attends to the other.
    Uses scaled dot-product attention where queries come from one modality
    and keys/values come from the other.
    """

    def __init__(self, dim_q: int, dim_kv: int, hidden_dim: int, num_heads: int = 4):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads
        assert hidden_dim % num_heads == 0

        self.W_q = nn.Linear(dim_q, hidden_dim)
        self.W_k = nn.Linear(dim_kv, hidden_dim)
        self.W_v = nn.Linear(dim_kv, hidden_dim)
        self.W_out = nn.Linear(hidden_dim, hidden_dim)

        self.layer_norm = nn.LayerNorm(hidden_dim)
        self.dropout = nn.Dropout(0.1)

    def forward(self, query: torch.Tensor, key_value: torch.Tensor):
        """
        Args:
            query: (batch, hidden_dim) — from modality A
            key_value: (batch, hidden_dim) — from modality B

        Returns:
            fused: (batch, hidden_dim)
        """
        batch_size = query.size(0)

        # Add sequence dim if needed (single vector -> length-1 sequence)
        if query.dim() == 2:
            query = query.unsqueeze(1)
        if key_value.dim() == 2:
            key_value = key_value.unsqueeze(1)

        Q = self.W_q(query)
        K = self.W_k(key_value)
        V = self.W_v(key_value)

        # Multi-head reshape
        Q = Q.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        K = K.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        V = V.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)

        # Scaled dot-product attention
        scale = math.sqrt(self.head_dim)
        attn_scores = torch.matmul(Q, K.transpose(-2, -1)) / scale
        attn_weights = F.softmax(attn_scores, dim=-1)
        attn_weights = self.dropout(attn_weights)

        attn_output = torch.matmul(attn_weights, V)
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, -1,
                                                                     self.num_heads * self.head_dim)
        output = self.W_out(attn_output).squeeze(1)
        output = self.layer_norm(output)

        return output


class GatedFusion(nn.Module):
    """
    Gated fusion: learns to weight contributions from two modalities.
    gate = σ(W_g · [h_ts; h_text] + b)
    fused = gate * h_ts + (1 - gate) * h_text
    """

    def __init__(self, dim_a: int, dim_b: int, output_dim: int):
        super().__init__()
        self.projection_a = nn.Linear(dim_a, output_dim)
        self.projection_b = nn.Linear(dim_b, output_dim)
        self.gate = nn.Sequential(
            nn.Linear(dim_a + dim_b, output_dim),
            nn.Sigmoid(),
        )

    def forward(self, h_a: torch.Tensor, h_b: torch.Tensor):
        """
        Args:
            h_a: (batch, dim_a) — structured modality
            h_b: (batch, dim_b) — text modality

        Returns:
            fused: (batch, output_dim)
        """
        proj_a = self.projection_a(h_a)
        proj_b = self.projection_b(h_b)
        g = self.gate(torch.cat([h_a, h_b], dim=-1))
        fused = g * proj_a + (1 - g) * proj_b
        return fused
