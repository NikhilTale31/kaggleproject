#!/usr/bin/env python3
"""
Enhanced entry-point for the red-teaming discovery pipeline with checkpoint support.
This script adds persistent storage for prompts and vulnerability results across Kaggle sessions.
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

from src.config import load_config
from src.core.vulnerability_scanner import run_scan
from src.utils.file_manager import ensure_dirs
from src.utils.logger import get_logger
from src.utils.checkpoint_manager import checkpoint_manager

logger = get_logger("cli")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Red-teaming Framework - Discovery Runner with Checkpoints",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["full", "quick", "novel"],
        default="quick",
        help="Scan mode to run",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Optional category filter",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to config.json",
    )
    parser.add_argument(
        "--print-summary",
        action="store_true",
        help="Print JSON summary to stdout when finished",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from previous checkpoint",
    )
    parser.add_argument(
        "--export-checkpoints",
        type=str,
        help="Export checkpoints to directory for Kaggle dataset",
    )
    parser.add_argument(
        "--clear-checkpoints",
        action="store_true",
        help="Clear all existing checkpoints",
    )
    return parser.parse_args(argv)


async def main_async(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    ensure_dirs()

    # Handle checkpoint operations
    if args.export_checkpoints:
        checkpoint_manager.export_checkpoints(args.export_checkpoints)
        print(f"Checkpoints exported to {args.export_checkpoints}")
        return 0

    if args.clear_checkpoints:
        checkpoint_manager.clear_checkpoints()
        print("All checkpoints cleared")
        return 0

    # Show checkpoint info
    checkpoint_info = checkpoint_manager.get_checkpoint_info()
    print("=== Checkpoint Status ===")
    print(json.dumps(checkpoint_info, indent=2))

    # Load previous state if resuming
    if args.resume:
        prompts = checkpoint_manager.load_prompts()
        vulnerabilities = checkpoint_manager.load_vulnerabilities()
        
        if prompts or vulnerabilities:
            print(f"Resumed with {len(prompts)} prompts and {len(vulnerabilities)} vulnerabilities")
            # You can use these to skip already tested prompts
        else:
            print("No checkpoints found, starting fresh")

    # Run discovery
    summary: Dict[str, Any] = await run_scan(mode=args.mode, category=args.category, config=cfg)
    
    # Save checkpoints
    checkpoint_manager.save_prompts(summary.get("prompts", []))
    checkpoint_manager.save_vulnerabilities(summary.get("vulnerabilities", []))
    checkpoint_manager.save_session_state({
        "mode": args.mode,
        "category": args.category,
        "timestamp": str(Path.cwd()),
        "results_count": len(summary.get("vulnerabilities", []))
    })

    logger.info("Discovery run completed")
    if args.print_summary:
        print(json.dumps(summary, indent=2))
    return 0


def main() -> int:
    args = parse_args()
    try:
        return asyncio.run(main_async(args))
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        # Save partial results on interrupt
        checkpoint_manager.save_session_state({
            "status": "interrupted",
            "timestamp": str(Path.cwd())
        })
        return 130
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
