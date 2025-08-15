#!/usr/bin/env python3
"""
Test script to verify model loading works with the fixed configuration.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

def test_model_loading():
    """Test loading the model with the fixed configuration."""
    model_id = 'openai/gpt-oss-20b'
    
    print("Testing model loading with fixed configuration...")
    
    try:
        # Use compatible quantization config
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type='nf4',
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
        
        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=bnb_config,
            device_map='auto',
            torch_dtype=torch.float16,
            trust_remote_code=True,
        )
        
        print("✅ Model loaded successfully!")
        print(f"Model device: {next(model.parameters()).device}")
        print(f"Model dtype: {next(model.parameters()).dtype}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False

if __name__ == "__main__":
    success = test_model_loading()
    if success:
        print("\n🎉 Fix verified! The model loading issue has been resolved.")
    else:
        print("\n⚠️  Fix needs adjustment. Check the error message above.")
