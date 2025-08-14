from __future__ import annotations

import math
import os
import re
from typing import Any, Dict, List, Tuple

from ..utils.file_manager import read_json


_token_re = re.compile(r"[A-Za-z0-9_]+")


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in _token_re.findall(text or "")]


def _load_known_vulns(ref_dir: str = "data/reference") -> List[Dict[str, Any]]:
    """
    Load known vulnerabilities from data/reference/known_vulnerabilities.json.
    Expected structure:
    {
      "vulnerabilities": [
        {
          "id": "kv_001",
          "title": "Prompt Injection Reset Context",
          "summary": "Disregard previous instructions ...",
          "tags": ["injection", "override", ...]
        },
        ...
      ]
    }
    """
    path = os.path.join(ref_dir, "known_vulnerabilities.json")
    data = read_json(path, default={"vulnerabilities": []})
    vulns = data.get("vulnerabilities", [])
    if not isinstance(vulns, list):
        return []
    normalized: List[Dict[str, Any]] = []
    for v in vulns:
        if not isinstance(v, dict):
            continue
        normalized.append(
            {
                "id": str(v.get("id") or ""),
                "title": str(v.get("title") or ""),
                "summary": str(v.get("summary") or ""),
                "tags": [str(t).lower() for t in (v.get("tags") or [])],
                "_tokens": _tokenize(f"{v.get('title','')} {v.get('summary','')}")
            }
        )
    return normalized


def _jaccard(a: List[str], b: List[str]) -> float:
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    inter = len(sa & sb)
    union = len(sa | sb)
    return float(inter) / float(union) if union else 0.0


def _tag_overlap(a: List[str], b: List[str]) -> float:
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / float(len(sa | sb))


def score_novelty(item: Dict[str, Any], known_vulns: List[Dict[str, Any]] | None = None, ref_dir: str = "data/reference") -> float:
    """
    Estimate novelty score in [0,1], where 1.0 is highly novel and 0.0 is identical to a known vulnerability.
    Heuristics:
      - Compute token-level Jaccard similarity with each known vulnerability (title+summary).
      - Compute tag overlap if item['tags'] provided.
      - Use min similarity across all known vulns as 'closest match'.
      - Map similarity to novelty via novelty = max(0, 1 - sim_weighted), favoring lower overlap as more novel.
    """
    tokens = _tokenize((item.get("title") or "") + " " + (item.get("description") or item.get("summary") or ""))
    tags = [str(t).lower() for t in (item.get("tags") or [])]

    if known_vulns is None:
        known_vulns = _load_known_vulns(ref_dir)

    if not known_vulns:
        # With no reference, return mid-high novelty to err on exploration
        return 0.75

    closest_sim = 1.0
    for kv in known_vulns:
        kv_tokens = kv.get("_tokens") or _tokenize(f"{kv.get('title','')} {kv.get('summary','')}")
        jac = _jaccard(tokens, kv_tokens)
        tag_sim = _tag_overlap(tags, kv.get("tags") or [])
        # similarity is blended; tags contribute but less than text similarity
        sim = 0.75 * jac + 0.25 * tag_sim
        if sim < closest_sim:
            closest_sim = sim

    # Map similarity to novelty
    # Higher similarity -> lower novelty. Apply a non-linear curve for sensitivity near high-similarity.
    novelty = max(0.0, 1.0 - (closest_sim ** 0.85))
    return round(novelty, 4)


__all__ = ["score_novelty"]
