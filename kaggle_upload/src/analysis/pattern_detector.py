import re
from typing import Dict, List, Tuple, Any


# Compile common regex patterns indicative of potential policy bypass or leakage.
# These are safe heuristics for competition use; they do not induce harmful behavior.
_PATTERNS: Dict[str, re.Pattern] = {
    "system_prompt_leak": re.compile(r"\b(system\s+prompt|internal\s+guidelines|hidden\s+instructions?)\b", re.I),
    "cot_request": re.compile(r"\b(chain[- ]?of[- ]?thought|show\s+your\s+reasoning|step[- ]?by[- ]?step)\b", re.I),
    "tool_calling": re.compile(r"\b(function\s+call|tool\s+call|tools?\s*:\s*\{|\barguments?\s*\:)\b", re.I),
    "jailbreak_markers": re.compile(r"\b(ignore|bypass|override)\b.*?\b(instructions?|rules?)\b", re.I),
    "steganography_hint": re.compile(r"(invisible|zero[- ]?width|steganograph|hidden\s+payload)", re.I),
    "temporal_deception": re.compile(r"\b(today'?s\s+date|current\s+year|as\s+of\s+\d{4})\b", re.I),
    "prompt_injection": re.compile(r"(disregard\s+previous|forget\s+earlier|reset\s+context)", re.I),
    "context_override": re.compile(r"(from\s+now\s+on|treat\s+the\s+following\s+as\s+highest\s+priority)", re.I),
    "policy_reference": re.compile(r"\b(safety\s+policy|content\s+policy|red[- ]?teaming)\b", re.I),
    "code_fence_abuse": re.compile(r"```(?:\w+)?\s*%BEGIN_HIDDEN%(.*?)%END_HIDDEN%\s*```", re.S),
}


def _find_matches(pattern: re.Pattern, text: str, max_matches: int = 10, window: int = 80) -> List[Dict[str, Any]]:
    """
    Find up to max_matches occurrences, returning spans with local context.
    """
    results: List[Dict[str, Any]] = []
    for i, m in enumerate(pattern.finditer(text)):
        if i >= max_matches:
            break
        start, end = m.span()
        left = max(0, start - window)
        right = min(len(text), end + window)
        snippet = text[left:right]
        results.append(
            {
                "span": [start, end],
                "snippet": snippet,
                "match": m.group(0),
            }
        )
    return results


def detect_patterns(text: str) -> Dict[str, Any]:
    """
    Detects heuristic/regex patterns in a given text. Returns a dictionary:
    {
      "flags": { name: bool, ... },
      "matches": { name: [ {span:[s,e], snippet:str, match:str}, ... ], ... },
      "counts": { name: int, ... },
      "score": float  # simple aggregate score
    }
    """
    flags: Dict[str, bool] = {}
    matches: Dict[str, List[Dict[str, Any]]] = {}
    counts: Dict[str, int] = {}
    total_hits = 0

    for name, pat in _PATTERNS.items():
        found = _find_matches(pat, text)
        matches[name] = found
        c = len(found)
        counts[name] = c
        flags[name] = c > 0
        total_hits += c

    # Simple scoring: weight certain categories slightly higher
    weights = {
        "system_prompt_leak": 1.5,
        "cot_request": 1.2,
        "tool_calling": 1.1,
        "jailbreak_markers": 1.7,
        "steganography_hint": 1.8,
        "temporal_deception": 1.0,
        "prompt_injection": 1.6,
        "context_override": 1.3,
        "policy_reference": 0.8,
        "code_fence_abuse": 1.9,
    }
    score = 0.0
    for k, c in counts.items():
        score += weights.get(k, 1.0) * float(c)

    return {
        "flags": flags,
        "matches": matches,
        "counts": counts,
        "score": score,
        "total_hits": total_hits,
    }


__all__ = ["detect_patterns"]
