from __future__ import annotations

import os
from typing import Any, Dict, List

from ..utils.file_manager import (
    ensure_dirs,
    write_json,
    read_json,
    timestamped_path,
    REPORTS_DIR,
    SUBMISSIONS_DIR,
    FINDINGS_DIR,
)
from ..utils.logger import get_logger


logger = get_logger("finding-reporter")


def save_findings(findings: List[Dict[str, Any]], path: str | None = None) -> str:
    """
    Persist findings to a JSON file. If path is None, writes to a timestamped file in outputs/findings.
    Returns the file path written.
    """
    ensure_dirs()
    if path is None:
        path = timestamped_path(FINDINGS_DIR, prefix="findings", ext="json")
    write_json(path, {"findings": findings})
    logger.info(f"Saved findings to {path}")
    return path


def _category_counts(findings: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for f in findings:
        cat = str(f.get("category", "general"))
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def _top_items(findings: List[Dict[str, Any]], key_path: List[str], top_k: int = 10, reverse: bool = True) -> List[Dict[str, Any]]:
    """
    Return top_k items by nested key, e.g., key_path=['scores','semantic','aggregate_score']
    """
    def _get(d: Dict[str, Any], path: List[str], default: float = 0.0) -> float:
        cur: Any = d
        for k in path:
            if not isinstance(cur, dict):
                return default
            cur = cur.get(k)
        try:
            return float(cur)
        except Exception:
            return default

    ranked = sorted(findings, key=lambda f: _get(f, key_path, 0.0), reverse=reverse)
    return ranked[:top_k]


def generate_reports(findings: List[Dict[str, Any]], out_dir: str = REPORTS_DIR) -> Dict[str, str]:
    """
    Generate human-consumable report JSONs:
      - summary.json: counts and basic aggregates
      - top_semantic.json: top items by semantic aggregate score
      - top_harm.json: top items by harm aggregate
      - top_novelty.json: top by novelty
    Returns a map of report_name -> file_path
    """
    ensure_dirs()
    os.makedirs(out_dir, exist_ok=True)

    summary = {
        "total": len(findings),
        "categories": _category_counts(findings),
    }
    summary_path = os.path.join(out_dir, "summary.json")
    write_json(summary_path, summary)

    top_sem = _top_items(findings, ["scores", "semantic", "aggregate_score"], top_k=25)
    top_sem_path = os.path.join(out_dir, "top_semantic.json")
    write_json(top_sem_path, {"items": top_sem})

    top_harm = _top_items(findings, ["scores", "harm", "aggregate_risk"], top_k=25)
    top_harm_path = os.path.join(out_dir, "top_harm.json")
    write_json(top_harm_path, {"items": top_harm})

    top_nov = _top_items(findings, ["scores", "novelty"], top_k=25)
    top_nov_path = os.path.join(out_dir, "top_novelty.json")
    write_json(top_nov_path, {"items": top_nov})

    logger.info(f"Wrote reports to {out_dir}")
    return {
        "summary": summary_path,
        "top_semantic": top_sem_path,
        "top_harm": top_harm_path,
        "top_novelty": top_nov_path,
    }


def generate_submissions(out_dir: str = SUBMISSIONS_DIR, findings_path: str | None = None) -> str:
    """
    Generate a competition-ready JSON using filtered high-signal findings.
    If findings_path is provided, load from it; otherwise, search latest in outputs/findings
    and pick a subset of top items by semantic score and novelty.
    """
    ensure_dirs()
    os.makedirs(out_dir, exist_ok=True)

    # Determine findings source
    findings: List[Dict[str, Any]] = []
    if findings_path and os.path.isfile(findings_path):
        data = read_json(findings_path, default={"findings": []})
        findings = data.get("findings", [])
    else:
        # If none provided, try latest generated reports/top_semantic.json
        top_sem_path = os.path.join(REPORTS_DIR, "top_semantic.json")
        if os.path.isfile(top_sem_path):
            findings = read_json(top_sem_path, default={"items": []}).get("items", [])
        else:
            # Fallback to empty; competition pipeline may supply path explicitly
            findings = []

    # Construct a minimal submission format
    # Fields are generic; adapt as per competition submission schema if necessary.
    submission_items: List[Dict[str, Any]] = []
    for f in findings[:50]:
        submission_items.append(
            {
                "id": f.get("id"),
                "category": f.get("category"),
                "summary": f.get("summary"),
                "tags": f.get("tags"),
                "scores": f.get("scores"),
                "prompt": f.get("prompt"),
                "output_excerpt": (f.get("output_text") or "")[:400],
            }
        )

    path = os.path.join(out_dir, "submission.json")
    write_json(path, {"items": submission_items})
    logger.info(f"Wrote competition submission file to {path}")
    return path


__all__ = ["save_findings", "generate_reports", "generate_submissions"]
