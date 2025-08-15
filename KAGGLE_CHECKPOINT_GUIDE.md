# Kaggle Checkpoint Guide

## Persistent Storage for Kaggle Sessions

This guide explains how to use checkpoints to avoid re-running expensive vulnerability scans on Kaggle.

## Quick Start

### 1. First Session (Save Checkpoints)
```bash
python run_discovery_checkpoint.py --mode quick --export-checkpoints /kaggle/working/checkpoints
```

### 2. Create Kaggle Dataset
1. After running, save the `outputs/checkpoints` directory as a Kaggle Dataset
2. Go to Kaggle → Datasets → Create Dataset
3. Upload the `outputs/checkpoints` directory

### 3. Subsequent Sessions (Resume from Checkpoints)
```python
# In your Kaggle notebook
import sys
sys.path.append('/kaggle/input/your-checkpoint-dataset/checkpoints')

# Run with resume
!python run_discovery_checkpoint.py --mode quick --resume
```

## Checkpoint Files

- **prompts.json**: All tested prompts
- **vulnerabilities.json**: All discovered vulnerabilities
- **session.pkl**: Complete session state

## Usage Examples

### Basic Usage
```bash
# Run normally
python run_discovery_checkpoint.py --mode quick

# Resume from previous
python run_discovery_checkpoint.py --mode quick --resume

# Export for Kaggle dataset
python run_discovery_checkpoint.py --export-checkpoints /kaggle/working/checkpoints

# Clear old checkpoints
python run_discovery_checkpoint.py --clear-checkpoints
```

### In Kaggle Notebook
```python
# Add checkpoint dataset to path
import sys
sys.path.append('/kaggle/input/redteaming-checkpoints')

# Run with resume to avoid re-testing
!python run_discovery_checkpoint.py --mode quick --resume
```

## Benefits
- **Avoid re-testing**: Skip already tested prompts
- **Persistent storage**: Results survive kernel restarts
- **Incremental updates**: Add new results to existing checkpoints
- **Kaggle dataset**: Share checkpoints across sessions
