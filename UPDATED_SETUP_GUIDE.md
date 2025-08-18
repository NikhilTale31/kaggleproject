# Updated Setup Guide - OpenAI gpt-oss-20b Vulnerability Scanner

## Important Update: NO API KEY NEEDED!

The gpt-oss-20b model is **freely available** on HuggingFace with Apache 2.0 license. You can run it locally without any API keys!

## Quick Setup for Google Colab / Kaggle

### 1. Install Dependencies
```bash
# For Google Colab/Kaggle with GPU
!pip install -q --upgrade torch
!pip install -q transformers triton==3.4 kernels
!pip uninstall -q torchvision torchaudio -y

# Install project dependencies
!pip install -r requirements_fixed_clean.txt
```

**Note:** Restart runtime after installation!

### 2. Run the Vulnerability Scanner
```bash
# No API key configuration needed!
python run_competition.py
```

## Local Setup (with GPU)

### 1. Create Virtual Environment
```bash
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
```

### 2. Install PyTorch with CUDA
```bash
# For CUDA 12.1
pip install --index-url https://download.pytorch.org/whl/cu121 torch

# Install other dependencies
pip install -r requirements_fixed_clean.txt
```

### 3. Run the Scanner
```bash
python run_competition.py
```

## How It Works

The project uses the **HuggingFace backend** (`hf_local`) which:
1. Downloads the model from `openai/gpt-oss-20b` automatically
2. Loads it with MXFP4 quantization (only 3.6B active parameters)
3. Runs inference locally on your GPU
4. No API costs or rate limits!

## Configuration Details

The `config.json` is already set up correctly:
- `"backend": "hf_local"` - Uses HuggingFace local inference
- `"model": "openai/gpt-oss-20b"` - The free model
- `"api_key": null` - No key needed!
- `"hf_device_map": "cuda"` - Uses GPU automatically
- `"hf_reasoning_effort": "medium"` - Can be "low", "medium", or "high"

## Memory Requirements

- **Minimum**: 16GB GPU VRAM (Google Colab free tier works!)
- **Recommended**: 24GB+ for faster inference
- The model uses MXFP4 quantization, making it very efficient

## Competition Advantages

1. **Free to run** - No API costs while testing thousands of prompts
2. **No rate limits** - Run as fast as your GPU allows
3. **Full control** - Modify model parameters for better vulnerability discovery
4. **Reasoning effort control** - Adjust model's thinking depth per attack

## Files to Keep/Delete

**KEEP:**
- `requirements_fixed_clean.txt` - The correct dependencies file
- All other project files

**DELETE:**
- `requirementupdated_fixed.txt` - Has errors
- `requirements_competition.txt` - Outdated

## Running the Competition

```bash
# This will:
# 1. Load gpt-oss-20b from HuggingFace (first run downloads ~40GB)
# 2. Test 7 attack vectors automatically
# 3. Generate findings_*.json files for submission
# 4. Create competition_summary.json with results

python run_competition.py
```

## Tips for Better Results

1. **Increase reasoning effort** for complex attacks:
   - Edit `config.json`: `"hf_reasoning_effort": "high"`

2. **Add custom attack vectors**:
   - Edit `src/competition/attack_vectors.py`

3. **Adjust generation parameters**:
   - `hf_max_new_tokens`: Increase for longer responses
   - `hf_temperature`: Lower for more focused attacks

## No API Key, No Problem!

This project is designed to work with the FREE gpt-oss-20b model. You get:
- Unlimited local inference
- No API costs
- Full model access
- Complete control over parameters

Happy vulnerability hunting! 🎯
