# Fix for New Error: 8-bit Loading and MXFP4 Dequantization

## The Problem

Your new error shows two issues:

1. **8-bit loading fails**: `'BitsAndBytesConfig' object has no attribute 'get_loading_attributes'`
   - This is a version compatibility issue between transformers and bitsandbytes

2. **Model still being dequantized**: The MXFP4 model is still expanding to 16-bit
   - GPU memory usage: 38.62 GiB allocated (almost full 40GB)
   - Still trying to allocate more memory

## The Solution

### Quick Fix: Run the Fixed Script

```bash
python run_8bit_fixed.py
```

This script will:
1. Set proper environment variables
2. Install/verify bitsandbytes
3. Clear GPU cache
4. Configure 8-bit loading correctly
5. Run the competition

### Manual Fix Steps

If you want to fix it manually:

1. **Clear GPU Memory First**:
```bash
python -c "import torch; torch.cuda.empty_cache()"
```

2. **Set Environment Variables**:
```bash
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export CUDA_VISIBLE_DEVICES=0
```

3. **Install Dependencies**:
```bash
pip install bitsandbytes accelerate
```

4. **Update config.json**:
```json
{
  "backend": "hf_local",
  "model": "openai/gpt-oss-20b",
  "hf_load_in_8bit": true,
  "hf_load_in_4bit": false,
  "hf_device_map": "auto",
  "hf_torch_dtype": "float16",
  "hf_max_memory": {"0": "35GB", "cpu": "60GB"},
  "cache_enabled": false
}
```

5. **Run the competition**:
```bash
python run_competition.py
```

## Why This Works

1. **Direct 8-bit loading**: Uses `load_in_8bit=True` parameter instead of BitsAndBytesConfig
2. **Memory limits**: Sets max GPU usage to 35GB (leaving 5GB free)
3. **CPU offloading**: Allows using system RAM if needed
4. **Cache disabled**: Saves memory during loading

## Alternative: Force 4-bit with Triton

If 8-bit still fails, install Triton to keep the model in 4-bit:

```bash
pip install triton>=3.4.0
python run_competition_4bit_fixed.py
```

## Memory Usage Comparison

| Method | GPU Memory | Status |
|--------|-----------|---------|
| 16-bit (current) | ~55GB | ❌ Too large |
| 8-bit (fixed) | ~10-11GB | ✅ Fits easily |
| 4-bit (with Triton) | ~4GB | ✅ Most efficient |

## Troubleshooting

If you still get errors:

1. **Check GPU usage**:
```bash
nvidia-smi
```

2. **Kill other processes**:
```bash
# Find process using GPU
nvidia-smi | grep python
# Kill it
kill -9 <PID>
```

3. **Restart runtime** (in Colab):
   - Runtime → Restart runtime
   - Then run `python run_8bit_fixed.py`

4. **Use CPU-GPU mixed mode**:
```python
config["hf_max_memory"] = {0: "20GB", "cpu": "60GB"}
```

This will use 20GB GPU + 60GB system RAM.
