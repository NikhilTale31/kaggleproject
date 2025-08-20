#!/usr/bin/env python3
"""Fix script for 8-bit loading issues with OpenAI GPT-OSS-20B"""

import os
import sys
import subprocess
import json

def main():
    print("Fixing 8-bit loading configuration...")
    
    # 1. Check and install required packages
    print("\n1. Checking dependencies...")
    try:
        import bitsandbytes
        print("   - bitsandbytes: OK")
    except ImportError:
        print("   - Installing bitsandbytes...")
        subprocess.run([sys.executable, "-m", "pip", "install", "bitsandbytes>=0.41.0"], check=True)
    
    try:
        import accelerate
        print("   - accelerate: OK")
    except ImportError:
        print("   - Installing accelerate...")
        subprocess.run([sys.executable, "-m", "pip", "install", "accelerate>=0.20.0"], check=True)
    
    # 2. Update transformers to latest version
    print("\n2. Updating transformers to latest version...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "transformers>=4.36.0"], check=True)
    
    # 3. Set environment variables
    print("\n3. Setting environment variables...")
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
    os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
    
    # 4. Clear GPU cache
    print("\n4. Clearing GPU cache...")
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            print("   - GPU cache cleared")
    except Exception as e:
        print(f"   - Could not clear GPU cache: {e}")
    
    # 5. Update config.json for optimal 8-bit settings
    print("\n5. Updating config.json...")
    config_path = "config.json"
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Update config for 8-bit loading
        config.update({
            "hf_load_in_8bit": True,
            "hf_load_in_4bit": False,
            "hf_device_map": "auto",
            "hf_max_memory": {"0": "35GB", "cpu": "60GB"},
            "hf_torch_dtype": "float16",
            "hf_low_cpu_mem_usage": True
        })
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print("   - Config updated for 8-bit loading")
    
    # 6. Create a test script
    print("\n6. Creating test script...")
    test_script = """
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

print("Testing 8-bit loading...")
model_id = "openai/gpt-oss-20b"

# Create 8-bit config
bnb_config = BitsAndBytesConfig(
    load_in_8bit=True,
    bnb_8bit_compute_dtype=torch.float16,
)

print(f"Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_id)

print(f"Loading model in 8-bit...")
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto",
    low_cpu_mem_usage=True,
)

print("Model loaded successfully!")
print(f"Model device: {next(model.parameters()).device}")
print(f"Model dtype: {next(model.parameters()).dtype}")
"""
    
    with open("test_8bit_loading.py", "w") as f:
        f.write(test_script)
    
    print("\n7. Instructions:")
    print("   - The configuration has been fixed")
    print("   - Run 'python test_8bit_loading.py' to test 8-bit loading")
    print("   - Then run 'python run_competition.py' to start the competition")
    
    print("\nDone! The 8-bit loading should now work properly.")

if __name__ == "__main__":
    main()
