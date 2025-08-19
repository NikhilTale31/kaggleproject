#!/usr/bin/env python3
"""Run competition with 8-bit quantization for memory efficiency"""

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

from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from competition.attack_vectors import COMPETITION_ATTACKS
from core.vulnerability_scanner import VulnerabilityScanner
from competition.findings_formatter import FindingsFormatter

class QuantizedModelClient:
    """Client for 8-bit quantized model"""
    
    def __init__(self, model_name):
        self.model_name = model_name
        self._model = None
        self._tokenizer = None
        
    def start(self):
        """Load model with 8-bit quantization"""
        print("Loading tokenizer...")
        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        
        print("Loading model with 8-bit quantization...")
        quantization_config = BitsAndBytesConfig(
            load_in_8bit=True,
            bnb_8bit_compute_dtype=torch.float16,
            bnb_8bit_use_double_quant=True,
            bnb_8bit_quant_type="nf4"
        )
        
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=quantization_config,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        
        print("✅ Model loaded with 8-bit quantization!")
        print(f"Memory allocated: {torch.cuda.memory_allocated(0)/1024**3:.2f} GB")
        
    def generate(self, prompt, **kwargs):
        """Generate response"""
        inputs = self._tokenizer(prompt, return_tensors="pt", truncation=True)
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
            )
            
        response = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Clean up
        del inputs, outputs
        torch.cuda.empty_cache()
        
        return response
        
    def stop(self):
        """Clean up"""
        del self._model, self._tokenizer
        gc.collect()
        torch.cuda.empty_cache()

def main():
    """Run competition with 8-bit quantization"""
    
    # First, check if bitsandbytes is installed
    try:
        import bitsandbytes
    except ImportError:
        print("❌ bitsandbytes not installed. Installing...")
        os.system("pip install bitsandbytes")
        print("Please restart the script after installation.")
        return
    
    model_name = "openai/gpt-oss-20b"
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    print("🎯 Starting OpenAI GPT-OSS-20B Red-Teaming (8-bit mode)...")
    print(f"Testing {len(COMPETITION_ATTACKS)} attack scenarios...")
    
    # Clear memory
    gc.collect()
    torch.cuda.empty_cache()
    
    # Initialize model
    client = QuantizedModelClient(model_name)
    
    try:
        client.start()
        
        # Initialize scanner
        scanner = VulnerabilityScanner(client)
        formatter = FindingsFormatter()
        
        all_findings = []
        
        # Run attacks
        for i, (attack_name, attack_config) in enumerate(COMPETITION_ATTACKS.items(), 1):
            print(f"\n[{i}/{len(COMPETITION_ATTACKS)}] Testing: {attack_name}")
            
            try:
                findings = scanner.scan_with_attack(attack_config)
                
                if findings:
                    print(f"  ✅ Found {len(findings)} vulnerabilities")
                    all_findings.extend(findings)
                else:
                    print(f"  ❌ No vulnerabilities found")
                    
            except Exception as e:
                print(f"  ⚠️ Error: {str(e)}")
                continue
        
        # Save results
        print(f"\n🎉 Scan complete! Found {len(all_findings)} vulnerabilities")
        
        if all_findings:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            findings_file = output_dir / f"findings_8bit_{timestamp}.json"
            
            with open(findings_file, 'w') as f:
                json.dump([f.to_dict() for f in all_findings], f, indent=2)
            
            print(f"Findings saved to: {findings_file}")
            
    finally:
        client.stop()
        print("\n✅ Cleanup complete!")

if __name__ == "__main__":
    main()
