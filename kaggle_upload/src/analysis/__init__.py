"""
Analysis package: regex/heuristic detection, semantic signals, harm classification, novelty scoring.
"""

from .pattern_detector import detect_patterns  # noqa: F401
from .semantic_analyzer import semantic_signals  # noqa: F401
from .harm_classifier import classify_harm  # noqa: F401
from .novelty_scorer import score_novelty  # noqa: F401

__all__ = [
    "detect_patterns",
    "semantic_signals",
    "classify_harm",
    "score_novelty",
]
