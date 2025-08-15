"""
Attacks package: generators, jailbreak patterns, novel ideas, and multi-turn chains.
"""

from .attack_generator import load_templates, generate_single_turn_attacks, generate_multi_turn_attacks  # noqa: F401
from .jailbreak_patterns import JAILBREAK_PATTERNS, apply_pattern  # noqa: F401
from .novel_attacks import NOVEL_ATTACKS, synthesize_variants  # noqa: F401
from .multi_turn_attacks import MULTI_TURN_CHAINS, iter_conversation  # noqa: F401

__all__ = [
    "load_templates",
    "generate_single_turn_attacks",
    "generate_multi_turn_attacks",
    "JAILBREAK_PATTERNS",
    "apply_pattern",
    "NOVEL_ATTACKS",
    "synthesize_variants",
    "MULTI_TURN_CHAINS",
    "iter_conversation",
]
