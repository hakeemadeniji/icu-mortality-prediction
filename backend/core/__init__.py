"""
Core module for ICU Mortality Prediction System
"""

from .config import settings
from .logging import setup_logging

__all__ = ["settings", "setup_logging"]