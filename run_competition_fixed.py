#!/usr/bin/env python3
"""
Fixed competition runner that works without transformers or API dependencies.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add the project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.client_factory_fixed import ClientFactory
from src.core.vulnerability_scanner import VulnerabilityScanner
from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("competition")


async def run_competition_scan():
    """Run the competition scan with fixed configuration."""
    
    logger.info("Starting competition scan with mock backend...")
    
    # Load fixed configuration
    config_path = Path("config_fixed.json")
    if not config_path.exists():
        logger.error("config_fixed.json not found. Please create it first.")
        return
    
    with open(config_path) as f:
        config_data = json.load(f)
    
    config = Config(config_data)
    
    # Create client using fixed factory
    client = ClientFactory.create_client(config)
    scanner = VulnerabilityScanner(client)
    
    # Run scan
    logger.info("Running vulnerability scan...")
    results = await scanner.scan()
    
    # Save results
    output_path = Path("outputs/competition_results.json")
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Scan completed. Results saved to {output_path}")
    return results


if __name__ == "__main__":
    try:
        asyncio.run(run_competition_scan())
    except KeyboardInterrupt:
        logger.info("Competition scan interrupted by user")
    except Exception as e:
        logger.error(f"Competition scan failed: {e}")
        sys.exit(1)
