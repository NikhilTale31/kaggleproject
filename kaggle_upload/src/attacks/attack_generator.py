from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from ..utils.file_manager import read_json, TEMPLATES_DIR, DATA_DIR
from .jailbreak_patterns import JAILBREAK_PATTERNS, apply_pattern
from .novel_attacks import NOVEL_ATTACKS, synthesize_variants
from .multi_turn_attacks import MULTI_TURN_CHAINS, iter_conversation


def load_templates(templates_dir: str = TEMPLATES_DIR) -> Dict[str, Any]:
    """
    Load all template JSONs from templates directory.
    Expected files:
      - attack_templates.json
      - payload_library.json
      - context_injections.json
    """
    attack_templates = read_json(os.path.join(templates_dir, "attack_templates.json"), default={"templates": []})
    payload_library = read_json(os.path.join(templates_dir, "payload_library.json"), default={"payloads": []})
    context_injections = read_json(os.path.join(templates_dir, "context_injections.json"), default={"contexts": []})
    return {
        "attack_templates": attack_templates.get("templates", []),
        "payload_library": payload_library.get("payloads", []),
        "context_injections": context_injections.get("contexts", []),
    }


def _load_prompts(data_dir: str = DATA_DIR) -> Dict[str, List[str]]:
    base_prompts = read_json(os.path.join(data_dir, "prompts", "base_prompts.json"), default={"prompts": []}).get("prompts", [])
    adv_prompts = read_json(os.path.join(data_dir, "prompts", "adversarial_prompts.json"), default={"prompts": []}).get("prompts", [])
    ctx_prompts = read_json(os.path.join(data_dir, "prompts", "context_prompts.json"), default={"prompts": []}).get("prompts", [])
    return {
        "base": [str(x) for x in base_prompts],
        "adversarial": [str(x) for x in adv_prompts],
        "context": [str(x) for x in ctx_prompts],
    }


def _filter_by_category(items: List[Dict[str, Any]], category: Optional[str]) -> List[Dict[str, Any]]:
    if not category:
        return items
    cat = category.strip().lower()
    return [x for x in items if str(x.get("category", "")).lower() == cat or cat in [t.lower() for t in x.get("tags", [])]]


def generate_single_turn_attacks(category: Optional[str] = None, limit: Optional[int] = None, templates_dir: str = TEMPLATES_DIR, data_dir: str = DATA_DIR) -> List[Dict[str, Any]]:
    """
    Compose single-turn attack prompts using:
      - base + adversarial prompts
      - jailbreak patterns applied to payloads
      - novel attack variants
      - template-driven payload/context combinations
    Returns a list of dicts with fields:
      - id, type, prompt, tags, category, metadata
    """
    out: List[Dict[str, Any]] = []

    tmpl = load_templates(templates_dir)
    ploads = [str(p.get("text", p)) for p in tmpl.get("payload_library", [])]
    contexts = [str(c.get("text", c)) for c in tmpl.get("context_injections", [])]

    prompts = _load_prompts(data_dir)
    bases = prompts["base"]
    advs = prompts["adversarial"]

    # 1) Apply jailbreak patterns to adversarial payloads
    jb = _filter_by_category(JAILBREAK_PATTERNS, category)
    for i, pattern in enumerate(jb):
        for j, payload in enumerate(advs[: max(1, len(advs))]):
            text = apply_pattern(payload, pattern)
            out.append(
                {
                    "id": f"single_jb_{pattern['id']}_{j}",
                    "type": "single",
                    "prompt": text,
                    "tags": pattern.get("tags", []),
                    "category": pattern.get("category", "general"),
                    "metadata": {"source": "jailbreak_pattern", "pattern_id": pattern["id"]},
                }
            )

    # 2) Template-driven compositions (attack_templates.json)
    for t in tmpl.get("attack_templates", []):
        if category and str(t.get("category", "")).lower() != category.lower():
            # allow tag or category match in future; for now strict on category field if provided
            continue
        t_text = str(t.get("template", ""))
        t_tags = t.get("tags", [])
        t_cat = t.get("category", "general")
        for p in (ploads or ["benign payload"]):
            for c in (contexts or ["generic context"]):
                rendered = (
                    t_text.replace("{{payload}}", p)
                    .replace("{{context}}", c)
                )
                out.append(
                    {
                        "id": f"single_tmpl_{t.get('id','tmpl')}_{hash(rendered) & 0xffff}",
                        "type": "single",
                        "prompt": rendered,
                        "tags": t_tags,
                        "category": t_cat,
                        "metadata": {"source": "attack_template", "template_id": t.get("id", "tmpl")},
                    }
                )

    # 3) Novel attack variants
    nav = _filter_by_category(NOVEL_ATTACKS, category)
    for base in nav:
        variants = synthesize_variants(base, k=2, context="generic context", payload="benign payload")
        for v in variants:
            out.append(
                {
                    "id": f"single_novel_{v['id']}",
                    "type": "single",
                    "prompt": v["prompt"],
                    "tags": v.get("tags", []),
                    "category": v.get("category", "general"),
                    "metadata": {"source": "novel_attack", "base_id": base.get("id")},
                }
            )

    # 4) Base prompts mixed with contexts
    for bp in bases:
        for c in (contexts or [""]):
            rendered = f"{c}\n\n{bp}" if c else bp
            out.append(
                {
                    "id": f"single_base_{hash(rendered) & 0xffff}",
                    "type": "single",
                    "prompt": rendered,
                    "tags": ["base"],
                    "category": "general",
                    "metadata": {"source": "base+context"},
                }
            )

    # Apply category filter late to enforce that all returned items match the requested category or tags
    if category:
        out = _filter_by_category(out, category)

    # Optionally truncate after filtering
    if limit is not None and limit > 0:
        out = out[:limit]

    return out


def generate_multi_turn_attacks(category: Optional[str] = None, limit: Optional[int] = None, payload: str = "benign payload") -> List[Dict[str, Any]]:
    """
    Return multi-turn conversation specs:
      - id, type='multi', messages=[...], tags, category, metadata
    """
    out: List[Dict[str, Any]] = []
    chains = _filter_by_category(MULTI_TURN_CHAINS, category)
    for ch in chains:
        msgs = iter_conversation(ch, payload=payload)
        out.append(
            {
                "id": f"multi_{ch['id']}",
                "type": "multi",
                "messages": msgs,
                "tags": ch.get("tags", []),
                "category": ch.get("category", "general"),
                "metadata": {"source": "multi_turn_chain", "chain_id": ch["id"]},
            }
        )
    if limit is not None and limit > 0:
        out = out[:limit]
    return out


__all__ = ["load_templates", "generate_single_turn_attacks", "generate_multi_turn_attacks"]
