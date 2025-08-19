#!/usr/bin/env python3
"""Memory-efficient competition runner with single model instance"""

import os
import sys
import json
import torch
import gc
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from backends.hf_local_fixed import HFLocalFixed
from competition.attack_vectors import COMPETITION_ATTACKS
from core.vulnerability_scanner import VulnerabilityScanner
from competition.findings_formatter import FindingsFormatter

def clear_memory():
    """Aggressively clear memory"""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()

def run_competition_memory_efficient():
    """Run competition with memory-efficient single model instance"""
    
    # Configuration
    model_name = "openai/gpt-oss-20b"
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    print("🎯 Starting OpenAI GPT-OSS-20B Red-Teaming Challenge...")
    print(f"Testing {len(COMPETITION_ATTACKS)} attack scenarios...")
    
    # Clear memory before starting
    clear_memory()
    
    # Initialize model once
    print("\n📥 Loading model (this may take a few minutes)...")
    client = HFLocalFixed(model_name)
    
    try:
        client.start()
        print("✅ Model loaded successfully!")
        
        # Initialize scanner with the client
        scanner = VulnerabilityScanner(client)
        formatter = FindingsFormatter()
        
        all_findings = []
        
        # Run attacks sequentially with memory cleanup
        for i, (attack_name, attack_config) in enumerate(COMPETITION_ATTACKS.items(), 1):
            print(f"\n[{i}/{len(COMPETITION_ATTACKS)}] Testing: {attack_name}")
            
            try:
                # Clear memory before each attack
                clear_memory()
                
                # Run the attack
                findings = scanner.scan_with_attack(attack_config)
                
                if findings:
                    print(f"  ✅ Found {len(findings)} vulnerabilities")
                    all_findings.extend(findings)
                else:
                    print(f"  ❌ No vulnerabilities found")
                    
            except Exception as e:
                print(f"  ⚠️ Error during attack: {str(e)}")
                continue
        
        # Format and save results
        print(f"\n🎉 Competition scan complete!")
        print(f"Found {len(all_findings)} vulnerabilities")
        
        if all_findings:
            # Save detailed findings
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            findings_file = output_dir / f"findings_{timestamp}.json"
            
            with open(findings_file, 'w') as f:
                json.dump([f.to_dict() for f in all_findings], f, indent=2)
            
            print(f"Findings saved to: {findings_file}")
            
            # Generate summary
            summary = formatter.generate_summary(all_findings)
            summary_file = output_dir / "competition_summary.json"
            
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
                
            print(f"Summary saved to: {summary_file}")
            
    finally:
        # Clean up
        print("\n🧹 Cleaning up...")
        client.stop()
        clear_memory()
        
if __name__ == "__main__":
    run_competition_memory_efficient()
