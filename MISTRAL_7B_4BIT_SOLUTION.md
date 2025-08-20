# Mistral-7B 4-bit Quantization Solution for Google Colab (A100)

## Complete Error Analysis & Solution

### Root Causes of Your Errors:

1. **Deprecated API Usage**: Using `load_in_4bit=True` directly instead of `BitsAndBytesConfig`
2. **Version Mismatch**: Incompatible versions of transformers and bitsandbytes
3. **Incorrect Device Handling**: Calling `.to('cuda')` on a quantized model
4. **Missing dtype Specification**: Not specifying `torch_dtype` in configuration

### Key Fixes Implemented:

1. **Use BitsAndBytesConfig**: Properly configure 4-bit quantization
2. **Correct Versions**: Use compatible library versions
3. **No Manual Device Movement**: Use `device_map="auto"` instead of `.to('cuda')`
4. **Explicit dtype**: Set `torch_dtype=torch.float16`

## Quick Start Guide

### For Google Colab:

```python
# Cell 1: Install dependencies
!python setup_mistral_colab.py

# Cell 2: Run the model
!python mistral_7b_4bit_colab.py
```

### Or as a single Colab notebook:

```python
# Cell 1: Install dependencies
!pip install -q torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118
!pip install -q transformers==4.36.2 bitsandbytes==0.41.3 accelerate==0.25.0
!pip install -q scipy sentencepiece protobuf

# Cell 2: Load and use the model
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

# Configure 4-bit quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16
)

# Load model and tokenizer
model_id = "mistralai/Mistral-7B-Instruct-v0.1"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.float16
)

# Test generation
prompt = "Explain the benefits of 4-bit quantization."
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=100)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## Important Notes:

### DO NOT:
- Call `model.to('cuda')` on quantized models
- Use `load_in_4bit=True` directly in `from_pretrained()`
- Mix incompatible library versions
- Forget to specify `torch_dtype`

### DO:
- Use `BitsAndBytesConfig` for quantization settings
- Let `device_map="auto"` handle device placement
- Specify `torch_dtype=torch.float16`
- Use compatible library versions

## Memory Usage:

With 4-bit quantization on A100 (40GB):
- Model size: ~3.5-4GB (vs ~13GB unquantized)
- Peak memory during loading: ~8-10GB
- Inference memory: ~5-6GB

## Performance Tips:

1. **Double Quantization**: `bnb_4bit_use_double_quant=True` saves more memory
2. **NF4 Quantization**: `bnb_4bit_quant_type="nf4"` provides better quality
3. **Float16 Compute**: `bnb_4bit_compute_dtype=torch.float16` balances speed/quality

## Troubleshooting:

### If you still get errors:

1. **Clear GPU memory**:
   ```python
   import torch
   torch.cuda.empty_cache()
   ```

2. **Check versions**:
   ```python
   import transformers, bitsandbytes
   print(f"Transformers: {transformers.__version__}")
   print(f"Bitsandbytes: {bitsandbytes.__version__}")
   ```

3. **Restart runtime** if needed (Runtime → Restart runtime)

## Advanced Usage:

### Creating a Chat Interface:

```python
from transformers import pipeline

# Create pipeline
pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    device_map="auto"
)

# Chat function
def chat(message):
    formatted = f"[INST] {message} [/INST]"
    response = pipe(formatted, max_new_tokens=256, return_full_text=False)
    return response[0]['generated_text']

# Use it
print(chat("What is machine learning?"))
```

### Batch Processing:

```python
# Process multiple prompts efficiently
prompts = [
    "Explain quantum computing",
    "What is artificial intelligence?",
    "Describe neural networks"
]

# Tokenize all at once
inputs = tokenizer(prompts, return_tensors="pt", padding=True)

# Generate for all
with torch.no_grad():
    outputs = model.generate(**inputs, max_new_tokens=100)

# Decode all
for output in outputs:
    print(tokenizer.decode(output, skip_special_tokens=True))
    print("-" * 50)
```

## Complete Working Example:

See `mistral_7b_4bit_colab.py` for a full implementation with:
- Proper error handling
- Memory monitoring
- Chat interface
- Testing utilities

## Credits & Resources:

- Mistral AI: https://mistral.ai/
- Hugging Face Transformers: https://huggingface.co/docs/transformers
- BitsAndBytes: https://github.com/TimDettmers/bitsandbytes
- Quantization Guide: https://huggingface.co/docs/transformers/quantization
