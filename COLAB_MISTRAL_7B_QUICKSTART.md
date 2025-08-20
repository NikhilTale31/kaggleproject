# Google Colab Quick Start Guide for Mistral-7B 4-bit

## Complete Step-by-Step Sequence for Google Colab

### Option 1: Using the Jupyter Notebook (Easiest)

1. **Upload the notebook to Colab:**
   - Go to [Google Colab](https://colab.research.google.com/)
   - Click "File" → "Upload notebook"
   - Upload `Mistral_7B_4bit_Colab.ipynb`
   - Run each cell in order

### Option 2: Manual Setup in New Colab

Copy and paste these commands in separate cells:

#### Cell 1: Check GPU
```python
import torch
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
```

#### Cell 2: Install Dependencies
```python
!pip install -q torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118
!pip install -q transformers==4.36.2
!pip install -q bitsandbytes==0.41.3
!pip install -q accelerate==0.25.0
!pip install -q scipy sentencepiece protobuf
```

#### Cell 3: Import and Configure
```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import warnings
warnings.filterwarnings("ignore")

# Configure 4-bit quantization
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16
)
```

#### Cell 4: Load Model
```python
# Model setup
model_id = "mistralai/Mistral-7B-Instruct-v0.1"

# Load tokenizer
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_id)
tokenizer.pad_token = tokenizer.eos_token

# Load model with 4-bit quantization
print("Loading model (this takes 2-3 minutes)...")
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.float16
)

print(f"✅ Model loaded! Memory: {model.get_memory_footprint() / 1e9:.2f} GB")
```

#### Cell 5: Test Generation
```python
# Test the model
prompt = "Explain quantum computing in simple terms."
formatted_prompt = f"[INST] {prompt} [/INST]"

inputs = tokenizer(formatted_prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=200, temperature=0.7, do_sample=True)

response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(response.split("[/INST]")[-1].strip())
```

#### Cell 6: Create Chat Function
```python
def chat(message):
    formatted = f"[INST] {message} [/INST]"
    inputs = tokenizer(formatted, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=256, temperature=0.7, do_sample=True)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response.split("[/INST]")[-1].strip()

# Test it
print(chat("What is machine learning?"))
```

### Option 3: Using the Python Scripts

#### Cell 1: Upload Files
```python
# First, upload these files to Colab:
# - mistral_7b_4bit_colab.py
# - setup_mistral_colab.py

from google.colab import files
uploaded = files.upload()
```

#### Cell 2: Run Setup
```python
!python setup_mistral_colab.py
```

#### Cell 3: Run Main Script
```python
!python mistral_7b_4bit_colab.py
```

## Important Notes:

1. **GPU Required**: Make sure GPU is enabled:
   - Runtime → Change runtime type → Hardware accelerator → GPU (A100/V100/T4)

2. **Memory Usage**: 
   - With 4-bit: ~3.5-4GB
   - Without: ~13-14GB

3. **First Run**: Model download takes 5-10 minutes on first run

4. **Errors to Avoid**:
   - ❌ Don't use `model.to('cuda')` 
   - ❌ Don't use `load_in_4bit=True` directly
   - ✅ Use BitsAndBytesConfig
   - ✅ Use `device_map="auto"`

## Quick Test After Setup:

```python
# Quick functionality test
test_prompts = [
    "What is AI?",
    "Write a haiku about coding",
    "Explain recursion with an example"
]

for prompt in test_prompts:
    print(f"\n💬 {prompt}")
    print(f"🤖 {chat(prompt)}")
    print("-" * 50)
```

## Troubleshooting:

If you get errors:

1. **Clear GPU memory:**
   ```python
   import gc
   torch.cuda.empty_cache()
   gc.collect()
   ```

2. **Restart runtime:**
   - Runtime → Restart runtime

3. **Check versions:**
   ```python
   import transformers, bitsandbytes
   print(f"Transformers: {transformers.__version__}")
   print(f"Bitsandbytes: {bitsandbytes.__version__}")
   ```

That's it! You should now have a working Mistral-7B model with 4-bit quantization in Google Colab.
