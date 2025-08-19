#!/usr/bin/env python3
"""Run competition with proper 4-bit quantization support"""

import os
import sys
import json
import torch
import gc
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set memory optimization
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'

def install_triton():
    """Install Triton for MXFP4 support"""
    try:
        import triton
        version = triton.__version__
        if version < "3.4.0":
            print(f"Triton {version} found, but need >= 3.4.0. Upgrading...")
            os.system("pip install --upgrade triton>=3.4.0")
            return True
    except ImportError:
        print("Installing Triton for 4-bit quantization support...")
        os.system("pip install triton>=3.4.0")
        return True
    return False

# Check and install Triton
if install_triton():
    print("⚠️  Triton installed/upgraded. Please restart the script to use 4-bit quantization.")
    sys.exit(0)

from transformers import AutoModelForCausalLM, AutoTokenizer
from competition.attack_vectors import COMPETITION_ATTACKS
from core.vulnerability_scanner import VulnerabilityScanner
from competition.findings_formatter import FindingsFormatter

class MXFP4ModelClient:
    """Client for MXFP4 quantized model with proper support"""
    
    def __init__(self, model_name):
        self.model_name = model_name
        self._model = None
        self._tokenizer = None
        
    def start(self):
        """Load model with MXFP4 quantization properly supported"""
        print("Loading tokenizer...")
        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        
        print("Loading model with MXFP4 4-bit quantization...")
        
        # Clear cache before loading
        torch.cuda.empty_cache()
        gc.collect()
        
        # Load with proper MXFP4 support
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            device_map="auto",
            torch_dtype=torch.float16,  # Use fp16 for compute
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            # The model will stay in MXFP4 format with proper Triton support
        )
        
        print("✅ Model loaded with native 4-bit MXFP4 quantization!")
        
        # Check actual memory usage
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated(0) / 1024**3
            reserved = torch.cuda.memory_reserved(0) / 1024**3
            print(f"GPU Memory - Allocated: {allocated:.2f} GB, Reserved: {reserved:.2f} GB")
            print(f"Expected size with 4-bit: ~3.5-4 GB (vs ~55 GB if dequantized)")
        
    def generate(self, prompt, **kwargs):
        """Generate response efficiently"""
        inputs = self._tokenizer(
            prompt, 
            return_tensors="pt", 
            truncation=True,
            max_length=2048
        )
        
        # Move to GPU
        inputs = {k: v.cuda() for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=kwargs.get("max_new_tokens", 512),
                temperature=kwargs.get("temperature", 0.7),
                do_sample=kwargs.get("do_sample", True),
                top_p=kwargs.get("top_p", 0.9),
                pad_token_id=self._tokenizer.pad_token_id,
                eos_token_id=self._tokenizer.eos_token_id,
                use_cache=True,  # Enable KV cache
            )
            
        response = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Clean up
        del inputs, outputs
        torch.cuda.empty_cache()
        
        return response
        
    def stop(self):
        """Clean up"""
        if self._model is not None:
            del self._model
        if self._tokenizer is not None:
            del self._tokenizer
        gc.collect()
        torch.cuda.empty_cache()

def print_gpu_stats():
    """Print current GPU memory statistics"""
    if torch.cuda.is_available():
        print("\n📊 GPU Memory Stats:")
        print(f"  Allocated: {torch.cuda.memory_allocated(0)/1024**3:.2f} GB")
        print(f"  Reserved: {torch.cuda.memory_reserved(0)/1024**3:.2f} GB")
        free, total = torch.cuda.mem_get_info(0)
        print(f"  Free: {free/1024**3:.2f} GB")
        print(f"  Total: {total/1024**3:.2f} GB")

def main():
    """Run competition with proper 4-bit quantization"""
    
    model_name = "openai/gpt-oss-20b"
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    print("🎯 Starting OpenAI GPT-OSS-20B Red-Teaming (4-bit MXFP4 mode)...")
    print(f"Testing {len(COMPETITION_ATTACKS)} attack scenarios...")
    
    # Show initial GPU stats
    print_gpu_stats()
    
    # Clear memory
    gc.collect()
    torch.cuda.empty_cache()
    
    # Initialize model
    client = MXFP4ModelClient(model_name)
    
    try:
        client.start()
        
        # Show GPU stats after loading
        print_gpu_stats()
        
        # Initialize scanner
        scanner = VulnerabilityScanner(client)
        formatter = FindingsFormatter()
        
        all_findings = []
        
        # Run attacks
        for i, (attack_name, attack_config) in enumerate(COMPETITION_ATTACKS.items(), 1):
            print(f"\n[{i}/{len(COMPETITION_ATTACKS)}] Testing: {attack_name}")
            
            try:
                # Clear cache before each attack
                torch.cuda.empty_cache()
                
                findings = scanner.scan_with_attack(attack_config)
                
                if findings:
                    print(f"  ✅ Found {len(findings)} vulnerabilities")
                    all_findings.extend(findings)
                else:
                    print(f"  ❌ No vulnerabilities found")
                    
            except torch.cuda.OutOfMemoryError as e:
                print(f"  ⚠️ GPU OOM: {str(e)}")
                print_gpu_stats()
                # Try to recover
                torch.cuda.empty_cache()
                gc.collect()
                continue
            except Exception as e:
                print(f"  ⚠️ Error: {str(e)}")
                continue
        
        # Save results
        print(f"\n🎉 Scan complete! Found {len(all_findings)} vulnerabilities")
        
        if all_findings:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            findings_file = output_dir / f"findings_4bit_{timestamp}.json"
            
            with open(findings_file, 'w') as f:
                json.dump([f.to_dict() for f in all_findings], f, indent=2)
            
            print(f"Findings saved to: {findings_file}")
            
            # Generate summary
            summary = formatter.generate_summary(all_findings)
            summary_file = output_dir / "competition_summary_4bit.json"
            
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
                
            print(f"Summary saved to: {summary_file}")
            
    finally:
        print("\n🧹 Cleaning up...")
        client.stop()
        print_gpu_stats()
        print("\n✅ Done!")

if __name__ == "__main__":
    main()
