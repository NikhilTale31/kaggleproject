# Complete Sequence to Run 8-bit Version with Memory Fix (Google Colab)

## Quick Start (Just Run This!)

```bash
cd /content/kaggleproject
python run_competition_8bit_memory_fixed.py
```

That's it! This script handles everything automatically.

## For Google Colab Users

Make sure you're in the correct directory:
```bash
!pwd  # Should show: /content/kaggleproject
```

If not, navigate there first:
```bash
cd /content/kaggleproject
```

## What This Script Does:

1. **Sets memory optimization environment variables**
   - `PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512,expandable_segments:True`
   - Prevents GPU memory fragmentation

2. **Clears GPU memory aggressively**
   - Kills zombie processes
   - Clears cache multiple times
   - Monitors memory usage

3. **Updates config.json automatically**
   - Enables 8-bit loading
   - Sets conservative memory limits
   - Disables 4-bit mode

4. **Handles errors gracefully**
   - Retries on OOM errors
   - Falls back to smaller models if needed
   - Continues testing even if some fail

## Manual Steps (If You Prefer)

If you want to run the steps manually instead:

### Step 1: Clear GPU Memory
```bash
python -c "import torch; torch.cuda.empty_cache()"
```

### Step 2: Set Environment Variables
```bash
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export CUDA_LAUNCH_BLOCKING=1
```

### Step 3: Install Dependencies
```bash
pip install bitsandbytes accelerate
```

### Step 4: Run Competition
```bash
python run_competition.py
```

## Memory Requirements

- **8-bit model**: ~10-11GB GPU memory
- **Your A100**: 40GB (plenty of space!)
- **System RAM**: 83GB (more than enough)

## Troubleshooting

If you still get OOM errors:

1. **Check for other processes**:
   ```bash
   nvidia-smi
   ```

2. **Kill all Python processes**:
   ```bash
   pkill -f python
   ```

3. **Restart runtime** (in Colab):
   Runtime → Restart runtime

4. **Run the memory-fixed script**:
   ```bash
   python run_competition_8bit_memory_fixed.py
   ```

## Expected Output

```
🚀 Starting Memory-Optimized 8-bit Competition Runner
============================================================
✅ bitsandbytes is installed
✅ Config updated for 8-bit loading with memory optimizations

📊 Initial Memory Status:
  GPU: 0.00/39.56 GB (0.0% used)
  RAM: 13.45/83.00 GB (16.2% used)

🔄 Creating client and loading model...
[hf_local] Attempting 8-bit quantized load
[hf_local] Successfully loaded in 8-bit mode

🎯 Starting OpenAI gpt-oss-20b Red-Teaming Challenge...
Testing 7 attack scenarios...

[1/7] Testing: Deceptive Alignment Detection
...
```

## Why This Works

1. **Memory fragmentation fix**: The environment variable prevents PyTorch from fragmenting GPU memory
2. **8-bit quantization**: Reduces model from 40GB+ to ~10GB
3. **Aggressive cleanup**: Ensures no memory leaks between tests
4. **Conservative limits**: Leaves headroom for inference

Your A100 with 40GB is more than capable of running this!
