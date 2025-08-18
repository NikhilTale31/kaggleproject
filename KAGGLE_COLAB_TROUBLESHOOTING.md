# Kaggle/Colab Troubleshooting Guide

## 1. File Not Found Errors

### Problem: "File not found" even though .py file exists

**Common Causes & Solutions:**

### A. Wrong Working Directory
```python
# Always check your current directory first
import os
print("Current directory:", os.getcwd())
print("Files here:", os.listdir())

# If you're not in the project root, change directory:
os.chdir('/kaggle/working/openai-project')  # For Kaggle
os.chdir('/content/openai-project')          # For Colab
```

### B. Path Issues with Imports
```python
# Add the project root to Python path
import sys
sys.path.insert(0, '/kaggle/working/openai-project')  # Kaggle
sys.path.insert(0, '/content/openai-project')         # Colab

# Now imports will work
from src.core.vulnerability_scanner import VulnerabilityScanner
```

### C. Complete Setup Cell for Kaggle/Colab
```python
# Run this as your FIRST cell
import os
import sys

# Detect environment
if 'COLAB_GPU' in os.environ:
    PROJECT_ROOT = '/content/openai-project'
elif 'KAGGLE_KERNEL_RUN_TYPE' in os.environ:
    PROJECT_ROOT = '/kaggle/working/openai-project'
else:
    PROJECT_ROOT = os.getcwd()

# Change to project directory
if os.path.exists(PROJECT_ROOT):
    os.chdir(PROJECT_ROOT)
else:
    print(f"Project not found at {PROJECT_ROOT}")
    print("Current directory:", os.getcwd())
    print("Available directories:", os.listdir())

# Add to Python path
sys.path.insert(0, PROJECT_ROOT)

# Verify setup
print(f"Working directory: {os.getcwd()}")
print(f"Python path includes: {PROJECT_ROOT}")
```

## 2. Module Not Found After Installing Requirements

### Problem: "ModuleNotFoundError" even after pip install

**Solutions:**

### A. Restart Runtime (Most Common Fix)
```python
# After installing packages, you MUST restart:
# Colab: Runtime → Restart runtime
# Kaggle: Run → Restart & Clear Output

# Then run your imports in a new cell
```

### B. Force Reinstall Specific Package
```python
# Sometimes packages don't install properly
!pip uninstall -y package_name
!pip install --force-reinstall package_name

# For our project:
!pip uninstall -y transformers accelerate
!pip install --force-reinstall transformers==4.38.2 accelerate==0.25.0
```

### C. Check Installation Location
```python
# Verify where packages are installed
import site
print("Package locations:", site.getsitepackages())

# Check if specific package is installed
import pkg_resources
installed = [pkg.key for pkg in pkg_resources.working_set]
print("transformers installed:", 'transformers' in installed)
```

### D. Complete Installation Script
```python
# Cell 1: Install everything properly
!pip install --upgrade pip
!pip install -q --upgrade torch  # Colab only
!pip install -q -r requirements_fixed_clean.txt

# Cell 2: Verify installations
import subprocess
import sys

def check_package(package_name):
    try:
        __import__(package_name)
        print(f"✅ {package_name} installed")
    except ImportError:
        print(f"❌ {package_name} NOT installed")
        # Try to install it
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

# Check all critical packages
packages = ['transformers', 'accelerate', 'torch', 'aiohttp', 'pydantic', 'httpx']
for pkg in packages:
    check_package(pkg)

print("\n⚠️ NOW RESTART THE RUNTIME!")
```

## 3. Common Kaggle/Colab Specific Issues

### A. Kaggle Internet Access
```python
# Kaggle disables internet by default
# Enable it: Settings → Internet → On (requires phone verification)
```

### B. Colab Drive Mounting
```python
# If you stored files in Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Then navigate to your project
os.chdir('/content/drive/MyDrive/openai-project')
```

### C. Memory Issues
```python
# Check available memory
!free -h

# Clear cache if needed
import gc
import torch
gc.collect()
torch.cuda.empty_cache()
```

## 4. Complete Working Setup

### For Kaggle:
```python
# Cell 1: Setup
!git clone https://github.com/your-repo/openai-project.git
%cd openai-project
!pip install -q -r requirements_fixed_clean.txt

# Cell 2: After restart
import os, sys
os.chdir('/kaggle/working/openai-project')
sys.path.insert(0, '/kaggle/working/openai-project')

# Cell 3: Run
!python run_competition.py
```

### For Colab:
```python
# Cell 1: Setup
!git clone https://github.com/your-repo/openai-project.git
%cd openai-project
!pip install -q --upgrade torch
!pip install -q -r requirements_fixed_clean.txt
!pip uninstall -q torchvision torchaudio -y

# Cell 2: After restart
import os, sys
os.chdir('/content/openai-project')
sys.path.insert(0, '/content/openai-project')

# Cell 3: Run
!python run_competition.py
```

## 5. Debug Checklist

If still having issues:

1. **Check working directory**: `print(os.getcwd())`
2. **List files**: `print(os.listdir())`
3. **Check Python path**: `print(sys.path)`
4. **Verify package**: `!pip show package_name`
5. **Check imports**: `python -c "import package_name"`
6. **Restart runtime**: Always after installing packages
7. **Check GPU**: `!nvidia-smi` (should show GPU)
8. **Check memory**: `!free -h`

## 6. Emergency Fix

If nothing works, use this nuclear option:

```python
# Complete reset and setup
!rm -rf /kaggle/working/*  # or /content/* for Colab
!git clone https://github.com/your-repo/openai-project.git
!cd openai-project && pip install -q -r requirements_fixed_clean.txt
!cd openai-project && python -m pip install -e .
# Restart runtime
# Then:
%cd openai-project
!python run_competition.py
