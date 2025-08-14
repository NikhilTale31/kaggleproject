from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any, Dict

from src.config import load_config
from src.core.vulnerability_scanner import run_scan
from src.utils.file_manager import ensure_dirs
from src.utils.logger import get_logger


logger = get_logger("cli")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Red-teaming Framework - Discovery Runner",
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
        help="Optional category filter (e.g., prompt_injection, cot_leakage, system_leakage, tool_orchestration, temporal_deception, steganography)",
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
    return parser.parse_args(argv)


async def main_async(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    ensure_dirs()

    summary: Dict[str, Any] = await run_scan(mode=args.mode, category=args.category, config=cfg)
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
        return 130
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
