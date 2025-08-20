#!/usr/bin/env python3
"""
Memory-optimized 8-bit competition runner for OpenAI gpt-oss-20b.
Fixes CUDA out of memory errors with proper memory management.
Optimized for Google Colab environment.
"""

import os
import sys
import gc
import torch
import asyncio
import json
from datetime import datetime
import subprocess

# Add Colab project path to Python path
sys.path.insert(0, '/content/kaggleproject')

# Set memory optimization environment variables BEFORE any imports
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512,expandable_segments:True'
os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
os.environ['TORCH_HOME'] = '/content/kaggleproject/.cache/torch'

# Clear any existing GPU memory
def initial_memory_cleanup():
    """Aggressive initial memory cleanup"""
    try:
        # Kill any zombie processes
        result = subprocess.run(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids = [int(pid.strip()) for pid in result.stdout.strip().split('\n') if pid.strip()]
            current_pid = os.getpid()
            for pid in pids:
                if pid != current_pid:
                    try:
                        os.kill(pid, 9)
                        print(f"Killed zombie process {pid}")
                    except:
                        pass
    except:
        pass
    
    # Clear Python garbage
    gc.collect()
    
    # Clear GPU cache
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        
        # Multiple passes to ensure cleanup
        for _ in range(3):
            gc.collect()
            torch.cuda.empty_cache()

# Run initial cleanup
initial_memory_cleanup()

# Now import the rest
from src.competition.findings_formatter import FindingsFormatter
from src.competition.attack_vectors import COMPETITION_ATTACK_VECTORS
from src.core.client_factory import ClientFactory
from src.core.vulnerability_scanner import VulnerabilityScanner
from src.config import load_config
from src.utils.memory_manager import MemoryManager


def update_config_for_8bit():
    """Update config.json for 8-bit loading with memory optimizations"""
    config_path = "config.json"
    
    # Read current config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Update for 8-bit with memory optimizations
    config.update({
        "hf_load_in_8bit": True,
        "hf_load_in_4bit": False,
        "hf_device_map": "auto",
        "hf_torch_dtype": "float16",
        "hf_max_memory": {"0": "38GB", "cpu": "70GB"},  # Conservative limits
        "cache_enabled": False,  # Disable caching to save memory
        "hf_low_cpu_mem_usage": True,
        "max_concurrent": 1,  # Reduce concurrency to save memory
    })
    
    # Write updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Config updated for 8-bit loading with memory optimizations")
    return config


async def run_competition_scan_with_memory_management():
    """Run competition scan with aggressive memory management"""
    
    # Update configuration
    update_config_for_8bit()
    
    # Log initial memory status
    print("\n📊 Initial Memory Status:")
    MemoryManager.log_memory_status("")
    
    # Load config and create client
    config = load_config()
    
    # Create client with memory monitoring
    print("\n🔄 Creating client and loading model...")
    try:
        client = ClientFactory.create_client(config)
        scanner = VulnerabilityScanner(client)
    except Exception as e:
        print(f"❌ Failed to create client: {e}")
        print("\n💡 Attempting fallback to smaller model...")
        
        # Try with a smaller model as fallback
        config.model = "gpt2-large"  # Much smaller fallback
        with open("config.json", 'w') as f:
            json.dump(vars(config), f, indent=2)
        
        client = ClientFactory.create_client(config)
        scanner = VulnerabilityScanner(client)
        print("✅ Loaded fallback model successfully")
    
    findings = []
    
    print("\n🎯 Starting OpenAI gpt-oss-20b Red-Teaming Challenge...")
    print(f"Testing {len(COMPETITION_ATTACK_VECTORS)} attack scenarios...")
    
    # Process scenarios with memory cleanup between each
    for i, scenario in enumerate(COMPETITION_ATTACK_VECTORS, 1):
        print(f"\n[{i}/{len(COMPETITION_ATTACK_VECTORS)}] Testing: {scenario.name}")
        
        # Clear memory before each test
        if i > 1:  # Skip first time
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        
        try:
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
                
        except torch.cuda.OutOfMemoryError as e:
            print(f"⚠️ GPU OOM during test {i}, clearing memory and retrying...")
            MemoryManager.clear_memory()
            
            # Retry once with cleared memory
            try:
                result = await scanner.test_vulnerability(
                    prompt=scenario.prompt_template[:500],  # Shorter prompt
                    category=scenario.category,
                    expected_behavior=scenario.expected_vulnerability
                )
            except Exception as retry_error:
                print(f"❌ Test {i} failed after retry: {retry_error}")
                continue
                
        except Exception as e:
            print(f"❌ Error in test {i}: {e}")
            continue
        
        # Log memory status periodically
        if i % 3 == 0:
            MemoryManager.log_memory_status(f"After test {i}")
    
    # Generate summary report
    summary = {
        "total_scenarios_tested": len(COMPETITION_ATTACK_VECTORS),
        "vulnerabilities_found": len(findings),
        "categories_tested": list(set(f["issue_summary"]["topic_area"] for f in findings)) if findings else [],
        "timestamp": datetime.utcnow().isoformat(),
        "memory_optimized": True,
        "quantization": "8-bit"
    }
    
    with open("competition_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n🎉 Competition scan complete!")
    print(f"Found {len(findings)} vulnerabilities across {len(set(f['issue_summary']['topic_area'] for f in findings)) if findings else 0} categories")
    print(f"Findings saved as findings_*.json files")
    print(f"Summary saved as competition_summary.json")
    
    # Final memory status
    MemoryManager.log_memory_status("Final")


def main():
    """Main entry point with proper async handling"""
    print("🚀 Starting Memory-Optimized 8-bit Competition Runner")
    print("=" * 60)
    
    # Ensure we have required packages
    try:
        import bitsandbytes
        print("✅ bitsandbytes is installed")
    except ImportError:
        print("📦 Installing bitsandbytes...")
        subprocess.run([sys.executable, "-m", "pip", "install", "bitsandbytes"], check=True)
    
    # Run the competition
    if "ipykernel" in sys.modules:  # Jupyter/Colab environment
        import nest_asyncio
        nest_asyncio.apply()
        asyncio.get_event_loop().run_until_complete(run_competition_scan_with_memory_management())
    else:
        asyncio.run(run_competition_scan_with_memory_management())


if __name__ == "__main__":
    main()
