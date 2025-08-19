#!/usr/bin/env python3
"""
Kaggle Vendor Directory Fix Script
Fixes issues with corrupted torch signal module that interferes with Python's standard library
"""

import os
import sys
import shutil
from pathlib import Path

def fix_vendor_torch_signal():
    """Fix the corrupted torch signal module that interferes with Python's standard library"""
    
    print("🔧 Fixing vendor directory issues...")
    
    # Possible vendor directory locations in Kaggle
    vendor_paths = [
        "/kaggle/working/vendor",
        "/kaggle/working/kaggleproject/vendor",
        "./vendor",
        "vendor"
    ]
    
    fixed = False
    
    for vendor_dir in vendor_paths:
        torch_signal_path = os.path.join(vendor_dir, "torch", "signal")
        
        if os.path.exists(torch_signal_path):
            print(f"📁 Found torch signal module at: {torch_signal_path}")
            
            # Check if __init__.py exists and is corrupted
            init_file = os.path.join(torch_signal_path, "__init__.py")
            
            if os.path.exists(init_file):
                try:
                    with open(init_file, 'r') as f:
                        content = f.read()
                        
                    # Check for the corrupted "fro" statement
                    if content.strip().startswith("fro") or len(content.strip()) < 10:
                        print(f"❌ Found corrupted __init__.py with content: {repr(content[:50])}")
                        
                        # Rename the corrupted directory
                        backup_path = torch_signal_path + "_backup"
                        if os.path.exists(backup_path):
                            shutil.rmtree(backup_path)
                        
                        shutil.move(torch_signal_path, backup_path)
                        print(f"✅ Moved corrupted module to: {backup_path}")
                        fixed = True
                        
                except Exception as e:
                    print(f"⚠️ Error reading {init_file}: {e}")
                    # If we can't read it, it's probably corrupted, so rename it
                    backup_path = torch_signal_path + "_backup"
                    if os.path.exists(backup_path):
                        shutil.rmtree(backup_path)
                    shutil.move(torch_signal_path, backup_path)
                    print(f"✅ Moved problematic module to: {backup_path}")
                    fixed = True
    
    if fixed:
        print("✅ Vendor directory issues fixed!")
    else:
        print("ℹ️ No corrupted torch signal module found.")
    
    # Also ensure vendor directory is in sys.path but AFTER standard library
    for vendor_dir in vendor_paths:
        if os.path.exists(vendor_dir) and vendor_dir not in sys.path:
            # Add to the end, not the beginning
            sys.path.append(vendor_dir)
            print(f"✅ Added {vendor_dir} to Python path")

def setup_kaggle_environment():
    """Setup proper environment for Kaggle"""
    
    # Fix the vendor torch signal issue first
    fix_vendor_torch_signal()
    
    # Set up environment variables
    os.environ['PYTHONPATH'] = '/kaggle/working:' + os.environ.get('PYTHONPATH', '')
    os.environ['TRANSFORMERS_CACHE'] = '/kaggle/working/.cache/transformers'
    os.environ['HF_HOME'] = '/kaggle/working/.cache/huggingface'
    
    print("✅ Kaggle environment configured")

if __name__ == "__main__":
    setup_kaggle_environment()
    
    # Test that standard library imports work
    try:
        import asyncio
        import signal
        import subprocess
        print("✅ Standard library imports working correctly!")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)
