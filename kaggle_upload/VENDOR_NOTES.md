# Vendor Environment Setup for Kaggle

## What is Vendor Environment?
The vendor environment pre-installs all dependencies into a local directory (`vendor/`) so you don't need to reinstall packages every time you restart a Kaggle notebook.

## Benefits:
- ✅ No repeated downloads of packages
- ✅ Faster notebook startup
- ✅ Consistent environment across sessions
- ✅ Works offline once uploaded

## How to Use:

### 1. Create Vendor Environment (One-time setup)
```python
# Run this once to create vendor environment
!python vendor_setup.py
```

### 2. Use Vendor Environment in Kaggle
```python
import sys
sys.path.insert(0, 'vendor')

# Now import your packages normally
import torch
import transformers
# etc...
```

### 3. Upload to Kaggle
1. Run `python vendor_setup.py` locally to create vendor directory
2. Upload the entire `kaggle_upload/` directory (including vendor/) to Kaggle as a dataset
3. In your Kaggle notebook, add:
   ```python
   import sys
   sys.path.insert(0, '/kaggle/input/your-dataset-name/vendor')
   ```

## File Structure:
```
kaggle_upload/
├── vendor/           # Pre-installed dependencies
├── vendor_setup.py   # Creates vendor environment
├── VENDOR_NOTES.md   # This file
├── KAGGLE_SETUP.py   # Original setup
└── ... (other files)
```

## Important Notes:
- Vendor directory will be ~100-500MB depending on dependencies
- Upload as Kaggle dataset for persistence across notebooks
- Works with both CPU and GPU Kaggle environments
