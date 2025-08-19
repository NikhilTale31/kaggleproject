#!/usr/bin/env python3
"""Competition runner for OpenAI gpt-oss-20b red-teaming challenge."""

import sys
import os
import shutil

# CRITICAL: Fix vendor directory issues BEFORE any other imports
def fix_vendor_before_imports():
    """Fix vendor directory issues before importing anything else"""
    vendor_paths = [
        "/kaggle/working/vendor",
        "/kaggle/working/kaggleproject/vendor",
        "./vendor",
        "vendor"
    ]
    
    for vendor_dir in vendor_paths:
        torch_signal_path = os.path.join(vendor_dir, "torch", "signal")
        
        if os.path.exists(torch_signal_path):
            # Check if __init__.py exists and is corrupted
            init_file = os.path.join(torch_signal_path, "__init__.py")
            
            if os.path.exists(init_file):
                try:
                    with open(init_file, 'r') as f:
                        content = f.read()
                    
                    # Check for the corrupted "fro" statement
                    if content.strip().startswith("fro") or len(content.strip()) < 10:
                        # Rename the corrupted directory
                        backup_path = torch_signal_path + "_backup"
                        if os.path.exists(backup_path):
                            shutil.rmtree(backup_path)
                        shutil.move(torch_signal_path, backup_path)
                        print(f"✅ Fixed corrupted torch signal module")
                except:
                    # If we can't read it, rename it anyway
                    backup_path = torch_signal_path + "_backup"
                    if os.path.exists(backup_path):
                        shutil.rmtree(backup_path)
                    shutil.move(torch_signal_path, backup_path)
                    print(f"✅ Fixed problematic torch signal module")
    
    # Add vendor to path but AFTER standard library
    for vendor_dir in vendor_paths:
        if os.path.exists(vendor_dir) and vendor_dir not in sys.path:
            sys.path.append(vendor_dir)

# Fix vendor issues before any imports
fix_vendor_before_imports()

# Now safe to import everything else
import asyncio
import json
from datetime import datetime
from typing import List, Dict
import argparse

from src.competition.findings_formatter import FindingsFormatter
from src.competition.attack_vectors import COMPETITION_ATTACK_VECTORS
from src.core.client_factory import ClientFactory
from src.core.vulnerability_scanner import VulnerabilityScanner
from src.config import load_config

async def run_competition_scan():
    """Run comprehensive competition scan."""
    
    config = load_config()
    client = ClientFactory.create_client(config)
    scanner = VulnerabilityScanner(client)
    
    findings = []
    
    print("🎯 Starting OpenAI gpt-oss-20b Red-Teaming Challenge...")
    print(f"Testing {len(COMPETITION_ATTACK_VECTORS)} attack scenarios...")
    
    for i, scenario in enumerate(COMPETITION_ATTACK_VECTORS, 1):
        print(f"\n[{i}/{len(COMPETITION_ATTACK_VECTORS)}] Testing: {scenario.name}")
        
        # Run attack scenario
        result = await scanner.test_vulnerability(
            prompt=scenario.prompt_template,
            category=scenario.category,
            expected_behavior=scenario.expected_vulnerability
        )
        
        if result.is_vulnerable:
            print(f"✅ Vulnerability found: {result.vulnerability_type}")
            
            # Create finding for competition
            finding = FindingsFormatter.create_finding(
                issue_title=f"{scenario.name} - {result.vulnerability_type}",
                topic_area=scenario.category,
                overview=result.description,
                desired_behavior=f"Model should not exhibit {scenario.expected_vulnerability}",
                observed_behavior=result.evidence,
                severity=result.severity_score,
                breadth=result.breadth_score,
                harmony_response=result.model_response,
                steps_to_reproduce=result.reproduction_steps,
                notes=f"Automated discovery via {scenario.name} test"
            )
            
            findings.append(finding)
            
            # Save individual finding
            filename = f"findings_{len(findings)}_{scenario.category}.json"
            FindingsFormatter.save_finding(finding, filename)
            print(f"💾 Saved finding: {filename}")
    
    # Generate summary report
    summary = {
        "total_scenarios_tested": len(COMPETITION_ATTACK_VECTORS),
        "vulnerabilities_found": len(findings),
        "categories_tested": list(set(f["issue_summary"]["topic_area"] for f in findings)),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    with open("competition_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n🎉 Competition scan complete!")
    print(f"Found {len(findings)} vulnerabilities across {len(set(f['issue_summary']['topic_area'] for f in findings))} categories")
    print(f"Findings saved as findings_*.json files")
    print(f"Summary saved as competition_summary.json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run gpt-oss-20b red-teaming competition")
    parser.add_argument("--output-dir", default=".", help="Directory to save findings")
    parser.add_argument("--max-findings", type=int, default=5, help="Maximum findings to generate")
    
    args = parser.parse_args()
    
    asyncio.run(run_competition_scan())
