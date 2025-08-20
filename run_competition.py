# #!/usr/bin/env python3
# """Competition runner for OpenAI gpt-oss-20b red-teaming challenge."""

# import asyncio
# import json
# import os
# from datetime import datetime
# from typing import List, Dict
# import argparse

# from src.competition.findings_formatter import FindingsFormatter
# from src.competition.attack_vectors import COMPETITION_ATTACK_VECTORS
# from src.core.client_factory import ClientFactory
# from src.core.vulnerability_scanner import VulnerabilityScanner
# from src.config import load_config
# import sys, os

# # Force Kaggle to use your vendored torch
# VENDOR_DIR = "/kaggle/working/kaggleproject/vendor"
# sys.path.insert(0, VENDOR_DIR)


# async def run_competition_scan():
#     """Run comprehensive competition scan."""
    
#     config = load_config()
#     client = ClientFactory.create_client(config)
#     scanner = VulnerabilityScanner(client)
    
#     findings = []
    
#     print("🎯 Starting OpenAI gpt-oss-20b Red-Teaming Challenge...")
#     print(f"Testing {len(COMPETITION_ATTACK_VECTORS)} attack scenarios...")
    
#     for i, scenario in enumerate(COMPETITION_ATTACK_VECTORS, 1):
#         print(f"\n[{i}/{len(COMPETITION_ATTACK_VECTORS)}] Testing: {scenario.name}")
        
#         # Run attack scenario
#         result = await scanner.test_vulnerability(
#             prompt=scenario.prompt_template,
#             category=scenario.category,
#             expected_behavior=scenario.expected_vulnerability
#         )
        
#         if result.is_vulnerable:
#             print(f"✅ Vulnerability found: {result.vulnerability_type}")
            
#             # Create finding for competition
#             finding = FindingsFormatter.create_finding(
#                 issue_title=f"{scenario.name} - {result.vulnerability_type}",
#                 topic_area=scenario.category,
#                 overview=result.description,
#                 desired_behavior=f"Model should not exhibit {scenario.expected_vulnerability}",
#                 observed_behavior=result.evidence,
#                 severity=result.severity_score,
#                 breadth=result.breadth_score,
#                 harmony_response=result.model_response,
#                 steps_to_reproduce=result.reproduction_steps,
#                 notes=f"Automated discovery via {scenario.name} test"
#             )
            
#             findings.append(finding)
            
#             # Save individual finding
#             filename = f"findings_{len(findings)}_{scenario.category}.json"
#             FindingsFormatter.save_finding(finding, filename)
#             print(f"💾 Saved finding: {filename}")
    
#     # Generate summary report
#     summary = {
#         "total_scenarios_tested": len(COMPETITION_ATTACK_VECTORS),
#         "vulnerabilities_found": len(findings),
#         "categories_tested": list(set(f["issue_summary"]["topic_area"] for f in findings)),
#         "timestamp": datetime.utcnow().isoformat()
#     }
    
#     with open("competition_summary.json", "w") as f:
#         json.dump(summary, f, indent=2)
    
#     print(f"\n🎉 Competition scan complete!")
#     print(f"Found {len(findings)} vulnerabilities across {len(set(f['issue_summary']['topic_area'] for f in findings))} categories")
#     print(f"Findings saved as findings_*.json files")
#     print(f"Summary saved as competition_summary.json")

# if __name__ == "__main__":
#     import sys
#     import asyncio

#     if __name__ == "__main__":
#         parser = argparse.ArgumentParser(description="Run gpt-oss-20b red-teaming competition")
#         parser.add_argument("--output-dir", default=".", help="Directory to save findings")
#         parser.add_argument("--max-findings", type=int, default=5, help="Maximum findings to generate")
    
#         args = parser.parse_args()

#         if "ipykernel" in sys.modules:  # running inside Jupyter/Kaggle
#             import nest_asyncio
#             nest_asyncio.apply()
#             asyncio.get_event_loop().run_until_complete(run_competition_scan())
#         else:  # running as a normal Python script
#             asyncio.run(run_competition_scan())
#!/usr/bin/env python3
"""Competition runner for OpenAI gpt-oss-20b red-teaming challenge."""

import sys
import os
import shutil

# CRITICAL: Fix vendor directory issues BEFORE any other imports
def fix_vendor_before_imports():
    """Fix vendor directory issues before importing anything else"""
    vendor_paths = [
        "/content/kaggleproject/vendor",
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

# Set environment variables to help find PyTorch
os.environ['TORCH_HOME'] = "/content/kaggleproject/.cache/torch"
os.environ['CUDA_HOME'] = '/usr/local/cuda'
# Set PyTorch memory allocation to avoid fragmentation
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'

# Now import everything else
import asyncio
import json
from datetime import datetime
from typing import List, Dict
import argparse
import gc

# Try to import torch first to verify it's working
try:
    import torch
    print(f"✅ PyTorch loaded successfully: {torch.__version__}")
    # Clear any existing GPU memory right after import
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
except ImportError as e:
    print(f"❌ Failed to import PyTorch: {e}")
    print(f"Current sys.path: {sys.path[:3]}")  # Show first 3 paths

from src.competition.findings_formatter import FindingsFormatter
from src.competition.attack_vectors import COMPETITION_ATTACK_VECTORS
from src.core.client_factory import ClientFactory
from src.core.vulnerability_scanner import VulnerabilityScanner
from src.config import load_config
from src.utils.memory_manager import MemoryManager, prepare_for_model_loading


async def run_competition_scan():
    """Run comprehensive competition scan."""
    
    # Prepare memory before loading model
    print("🧹 Preparing memory for model loading...")
    model_size_gb = 20.0  # For gpt-oss-20b
    can_load, memory_message = prepare_for_model_loading(model_size_gb)
    print(f"📊 Memory status: {memory_message}")
    
    config = load_config()
    
    # Log initial memory status
    MemoryManager.log_memory_status("Before creating client")
    
    client = ClientFactory.create_client(config)
    scanner = VulnerabilityScanner(client)
    
    # Log memory after model loading
    MemoryManager.log_memory_status("After model loading")
    
    findings = []
    
    print("\n🎯 Starting OpenAI gpt-oss-20b Red-Teaming Challenge...")
    print(f"Testing {len(COMPETITION_ATTACK_VECTORS)} attack scenarios...")
    
    for i, scenario in enumerate(COMPETITION_ATTACK_VECTORS, 1):
        print(f"\n[{i}/{len(COMPETITION_ATTACK_VECTORS)}] Testing: {scenario.name}")
        
        # Clear memory before each test (except first)
        if i > 1:
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
            
            # Retry once with cleared memory and shorter prompt
            try:
                result = await scanner.test_vulnerability(
                    prompt=scenario.prompt_template[:500],  # Shorter prompt
                    category=scenario.category,
                    expected_behavior=scenario.expected_vulnerability
                )
                if result.is_vulnerable:
                    print(f"✅ Vulnerability found on retry: {result.vulnerability_type}")
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
        "categories_tested": list(set(f["issue_summary"]["topic_area"] for f in findings)),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    with open("competition_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n🎉 Competition scan complete!")
    print(f"Found {len(findings)} vulnerabilities across {len(set(f['issue_summary']['topic_area'] for f in findings)) if findings else 0} categories")
    print(f"Findings saved as findings_*.json files")
    print(f"Summary saved as competition_summary.json")
    
    # Final memory status
    MemoryManager.log_memory_status("Final")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run gpt-oss-20b red-teaming competition")
    parser.add_argument("--output-dir", default=".", help="Directory to save findings")
    parser.add_argument("--max-findings", type=int, default=5, help="Maximum findings to generate")

    args = parser.parse_args()

    if "ipykernel" in sys.modules:  # running inside Jupyter/Kaggle
        import nest_asyncio
        nest_asyncio.apply()
        asyncio.get_event_loop().run_until_complete(run_competition_scan())
    else:  # running as a normal Python script
        asyncio.run(run_competition_scan())