from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

from ..utils.file_manager import read_json


def _load_harm_categories(ref_dir: str = "data/reference") -> List[Dict[str, Any]]:
    path = os.path.join(ref_dir, "harm_categories.json")
    data = read_json(path, default={"categories": []})
    cats = data.get("categories", [])
    if not isinstance(cats, list):
        return []
    # Normalize
    normalized = []
    for c in cats:
        if not isinstance(c, dict):
            continue
        normalized.append(
            {
                "id": c.get("id") or "",
                "name": c.get("name") or "",
                "description": c.get("description") or "",
                "keywords": [str(k).lower() for k in (c.get("keywords") or [])],
                "severity_weight": float(c.get("severity_weight") or 0.5),
                "tags": c.get("tags") or [],
            }
        )
    return normalized


def _keyword_hits(text: str, keywords: List[str]) -> int:
    t = text.lower()
    count = 0
    for k in keywords:
        if not k:
            continue
        # Basic substring match; safe competition heuristic
        if k in t:
            count += 1
    return count


def classify_harm(prompt: str, response: str, context: Optional[Dict[str, Any]] = None, ref_dir: str = "data/reference") -> Dict[str, Any]:
    """
    Classify potential harm categories heuristically using keyword-based matching
    against reference definitions in data/reference/harm_categories.json.

    Returns:
    {
      "categories": [
         {"id": str, "name": str, "score": float, "hits": int, "severity_weight": float, "tags": [...]},
         ...
      ],
      "aggregate_risk": float
    }
    """
    categories = _load_harm_categories(ref_dir)
    combined = f"{prompt or ''}\n{response or ''}"
    results: List[Dict[str, Any]] = []

    # For each category, compute a simple score: hits * severity_weight, capped to 1.0
    for cat in categories:
        hits = _keyword_hits(combined, cat["keywords"])
        score = min(1.0, hits * cat["severity_weight"])
        if hits > 0:
            results.append(
                {
                    "id": cat["id"],
                    "name": cat["name"],
                    "hits": hits,
                    "score": round(score, 4),
                    "severity_weight": cat["severity_weight"],
                    "tags": cat["tags"],
                }
            )

    # Aggregate risk: 1 - product(1 - score_i) for diminishing returns
    agg = 0.0
    prod = 1.0
    for r in results:
        prod *= (1.0 - r["score"])
    agg = 1.0 - prod

    return {
        "categories": results,
        "aggregate_risk": round(agg, 4),
    }


__all__ = ["classify_harm"]
