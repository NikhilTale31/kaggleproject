from __future__ import annotations

from typing import Any, Dict, List

from ..analysis.pattern_detector import detect_patterns
from ..analysis.semantic_analyzer import semantic_signals
from ..analysis.harm_classifier import classify_harm
from ..analysis.novelty_scorer import score_novelty


def analyze_response(prompt_obj: Dict[str, Any], response_obj: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Analyze a single prompt/response pair using multiple detectors and heuristics.

    Args:
      prompt_obj: {
         "id": str,
         "type": "single" | "multi",
         "prompt": str (for single) OR "messages": [{role, content}, ...] (for multi),
         ...
      }
      response_obj: {
         "output_text": str,
         "raw": dict,
         "meta": {...}
      }
      context: optional additional metadata

    Returns:
      finding: {
        "id": str,
        "category": str,
        "tags": list[str],
        "scores": {
            "patterns": {...},
            "semantic": {...},
            "harm": {...},
            "novelty": float
        },
        "summary": str,
        "prompt": str,
        "output_text": str,
        "raw": dict,
        "meta": {...}
      }
    """
    context = context or {}
    prompt_text = ""
    if prompt_obj.get("type") == "multi":
        # For analysis, join messages as a single text blob
        parts = []
        for m in (prompt_obj.get("messages") or []):
            parts.append(f"{m.get('role','user')}: {m.get('content','')}")
        prompt_text = "\n".join(parts)
    else:
        prompt_text = str(prompt_obj.get("prompt", ""))

    output_text = str(response_obj.get("output_text", ""))

    patt = detect_patterns(f"{prompt_text}\n{output_text}")
    sem = semantic_signals(prompt_text, output_text, context=context)
    harm = classify_harm(prompt_text, output_text, context=context)

    # Map prompt metadata into novelty item
    item = {
        "title": prompt_obj.get("id", "item"),
        "description": prompt_text[:300],
        "tags": prompt_obj.get("tags", []),
    }
    novelty = score_novelty(item)

    category = str(prompt_obj.get("category", "general"))
    tags = list(prompt_obj.get("tags", []))

    # Simple summary synthesis
    top_flags = [k for k, v in (patt.get("flags") or {}).items() if v]
    summary_parts = [
        f"Category={category}",
        f"Flags={','.join(top_flags[:5])}" if top_flags else "Flags=none",
        f"SemAgg={sem.get('aggregate_score',0)}",
        f"HarmAgg={harm.get('aggregate_risk',0)}",
        f"Novelty={novelty}",
    ]
    summary = " | ".join(summary_parts)

    return {
        "id": prompt_obj.get("id"),
        "category": category,
        "tags": tags,
        "scores": {
            "patterns": patt,
            "semantic": sem,
            "harm": harm,
            "novelty": novelty,
        },
        "summary": summary,
        "prompt": prompt_text,
        "output_text": output_text,
        "raw": response_obj.get("raw"),
        "meta": {
            **(response_obj.get("meta") or {}),
            "source": prompt_obj.get("metadata", {}).get("source"),
        },
    }


def aggregate_findings(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate a list of findings into overall metrics useful for reporting.
    """
    total = len(findings)
    by_category: Dict[str, int] = {}
    avg_scores = {
        "patterns": 0.0,
        "semantic": 0.0,
        "harm": 0.0,
        "novelty": 0.0,
    }

    if total == 0:
        return {"total": 0, "by_category": {}, "avg_scores": avg_scores}

    for f in findings:
        cat = str(f.get("category", "general"))
        by_category[cat] = by_category.get(cat, 0) + 1

        patt_score = float(((f.get("scores") or {}).get("patterns") or {}).get("score", 0.0))
        sem_agg = float(((f.get("scores") or {}).get("semantic") or {}).get("aggregate_score", 0.0))
        harm_agg = float(((f.get("scores") or {}).get("harm") or {}).get("aggregate_risk", 0.0))
        nov = float((f.get("scores") or {}).get("novelty", 0.0))

        avg_scores["patterns"] += patt_score
        avg_scores["semantic"] += sem_agg
        avg_scores["harm"] += harm_agg
        avg_scores["novelty"] += nov

    for k in avg_scores:
        avg_scores[k] = round(avg_scores[k] / total, 4)

    return {"total": total, "by_category": by_category, "avg_scores": avg_scores}


__all__ = ["analyze_response", "aggregate_findings"]
