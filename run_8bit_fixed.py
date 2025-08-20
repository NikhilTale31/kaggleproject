#!/usr/bin/env python3
"""
Fixed 8-bit runner that properly handles MXFP4 models and memory management.
"""

import os
import sys
import subprocess

# Set environment variables BEFORE any imports
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['TRANSFORMERS_CACHE'] = '/kaggle/working/cache'

print("🔧 Setting up 8-bit quantization environment...")

# Check if bitsandbytes is installed
try:
    import bitsandbytes
    print("✅ bitsandbytes is already installed")
except ImportError:
    print("📦 Installing bitsandbytes...")
    subprocess.run([sys.executable, "-m", "pip", "install", "bitsandbytes"], check=True)
    print("✅ bitsandbytes installed")

# Clear GPU cache before starting
try:
    import torch
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        print(f"🧹 Cleared GPU cache. Available memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
except:
    pass

# Update config to use 8-bit
import json

config_path = "config.json"
print(f"\n📝 Updating {config_path} for 8-bit quantization...")

# Read existing config
try:
    with open(config_path, 'r') as f:
        config = json.load(f)
except:
    config = {}

# Update config for 8-bit
config.update({
    "backend": "hf_local",
    "model": "openai/gpt-oss-20b",
    "hf_load_in_8bit": True,
    "hf_load_in_4bit": False,  # Disable 4-bit
    "hf_device_map": "auto",
    "hf_torch_dtype": "float16",
    "hf_max_memory": {0: "35GB", "cpu": "60GB"},  # Leave some GPU memory free
    "cache_enabled": False,  # Disable caching to save memory
})

# Write updated config
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("✅ Config updated for 8-bit quantization")
print("\n🚀 Starting competition with 8-bit quantization...")

# Run the competition
try:
    subprocess.run([sys.executable, "run_competition.py"], check=True)
except subprocess.CalledProcessError as e:
    print(f"\n❌ Error running competition: {e}")
    print("\n💡 Troubleshooting tips:")
    print("1. Make sure you have enough disk space for model download")
    print("2. Try running: nvidia-smi")
    print("3. Check if another process is using GPU memory")
    print("4. Try restarting the runtime")
