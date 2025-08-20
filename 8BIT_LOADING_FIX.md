# 8-Bit Loading Fix for OpenAI GPT-OSS-20B

## The Error

You're encountering this error:
```
The `load_in_4bit` and `load_in_8bit` arguments are deprecated and will be removed in the future versions. 
Please, pass a `BitsAndBytesConfig` object in `quantization_config` argument instead.
...
'BitsAndBytesConfig' object has no attribute 'get_loading_attributes'
```

## Root Cause

1. **Deprecated API**: The `load_in_8bit=True` parameter is deprecated in newer transformers versions
2. **Version Mismatch**: There's a compatibility issue between transformers and bitsandbytes versions
3. **Config Format**: The model expects `quantization_config` instead of direct `load_in_8bit` parameter

## Solution

### Step 1: Run the Fix Script

```bash
python fix_8bit_loading.py
```

This script will:
- Update all dependencies to compatible versions
- Fix the configuration
- Set proper environment variables
- Create a test script

### Step 2: Test 8-Bit Loading

```bash
python test_8bit_loading.py
```

### Step 3: Run Your Competition

```bash
python run_competition.py
```

## What Was Fixed

1. **Updated hf_local.py**: 
   - Removed duplicate 8-bit loading code
   - Uses `BitsAndBytesConfig` with `quantization_config` parameter
   - Properly handles memory clearing on failure

2. **Dependencies Updated**:
   - `transformers>=4.36.0` (for proper BitsAndBytesConfig support)
   - `bitsandbytes>=0.41.0` (for compatibility)
   - `accelerate>=0.20.0` (for device mapping)

3. **Configuration**:
   - Set `hf_load_in_8bit: true`
   - Added memory limits
   - Enabled low CPU memory usage

## Alternative: Use 4-Bit Instead

If 8-bit still has issues, you can use 4-bit quantization which uses even less memory:

```bash
# Update config.json
sed -i 's/"hf_load_in_8bit": true/"hf_load_in_8bit": false/g' config.json
sed -i 's/"hf_load_in_4bit": false/"hf_load_in_4bit": true/g' config.json

# Run with 4-bit
python run_competition.py
```

## Memory Usage Comparison

- **Full Precision (FP16)**: ~40GB (won't fit on most GPUs)
- **8-bit Quantization**: ~20GB (fits on A100-40GB, V100-32GB)
- **4-bit Quantization**: ~10GB (fits on most GPUs)

## Troubleshooting

If you still get errors:

1. **Clear GPU Memory**:
   ```python
   import torch
   torch.cuda.empty_cache()
   ```

2. **Check GPU Memory**:
   ```bash
   nvidia-smi
   ```

3. **Use CPU Offloading**:
   ```json
   "hf_device_map": "auto",
   "hf_max_memory": {"0": "30GB", "cpu": "60GB"}
   ```

4. **Reduce Batch Size**:
   - Process fewer prompts at once
   - Use shorter prompts

## Expected Output

When working correctly, you should see:
```
PyTorch loaded successfully: 2.x.x
Preparing memory for model loading...
Memory status: GPU has 39.56 GB free (need 20.00 GB)
[hf_local] Attempting 8-bit quantized load
[hf_local] Successfully loaded in 8-bit mode
Starting OpenAI gpt-oss-20b Red-Teaming Challenge...
```

The model will load in 8-bit precision, using approximately 20GB of GPU memory instead of 40GB+.
