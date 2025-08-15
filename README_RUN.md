# Complete Guide to Run AI Vulnerability Discovery Tool

## Quick Start (Automated)

### Windows
1. Double-click `RUN_PROJECT.bat`
2. Follow the on-screen prompts
3. Results will be saved in the `outputs/` directory

### Linux/Mac
1. Open terminal in project directory
2. Run: `./RUN_PROJECT.sh`
3. Follow the on-screen prompts
4. Results will be saved in the `outputs/` directory

## Manual Setup Guide

### 1. Prerequisites
- Python 3.8 or higher
- Virtual environment (recommended)

### 2. Environment Setup
```bash
# Create virtual environment
python -m venv myenv

# Activate virtual environment
# Windows:
myenv\Scripts\activate
# Linux/Mac:
source myenv/bin/activate

# Install dependencies
pip install -r requirementupdated_fixed.txt
```

### 3. Configuration
Before running, ensure `config.json` contains:
- Your API keys (OpenAI, HuggingFace, etc.)
- Model configurations
- Output settings

### 4. Running the Tool

#### Option A: Standard Discovery
```bash
python run_discovery.py
```

#### Option B: Checkpoint-Enabled Discovery (Recommended for long runs)
```bash
python run_discovery_checkpoint.py
```

### 5. Understanding the Outputs

#### Directory Structure:
```
outputs/
├── checkpoints/          # Resume points for long runs
├── results/             # Final vulnerability reports
├── logs/               # Execution logs
└── temp/               # Temporary files

data/
├── prompts/            # Attack prompts
├── reference/          # Reference materials
└── datasets/           # Input datasets
```

### 6. Advanced Usage

#### Custom Configuration:
Edit `config.json` to customize:
- Target models
- Attack strategies
- Output formats
- API endpoints

#### Resume from Checkpoint:
```bash
# Automatic with run_discovery_checkpoint.py
# Checkpoints are saved in outputs/checkpoints/
```

### 7. Troubleshooting

#### Common Issues:
1. **Import errors**: Ensure virtual environment is activated
2. **API errors**: Check API keys in config.json
3. **Memory issues**: Reduce batch size in config.json
4. **Permission errors**: Run `chmod +x RUN_PROJECT.sh` on Linux/Mac

#### Debug Mode:
```bash
# Enable verbose logging
python -u run_discovery.py --debug
```

### 8. Testing
```bash
# Run unit tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_api_client.py
```

### 9. Project Components

#### Core Files:
- `run_discovery.py`: Main entry point
- `run_discovery_checkpoint.py`: Checkpoint-enabled version
- `config.json`: Configuration settings
- `src/core/`: Core discovery logic
- `src/attacks/`: Attack generation
- `src/backends/`: AI backend integrations

#### Key Features:
- Multi-backend support (OpenAI, HuggingFace, local models)
- Checkpoint/resume capability
- Comprehensive vulnerability scanning
- Configurable attack strategies
- Detailed logging and reporting

### 10. Support

For issues:
1. Check logs in `outputs/logs/`
2. Verify configuration in `config.json`
3. Ensure all dependencies are installed
4. Check API key validity

## Quick Commands Reference

| Command | Description |
|---------|-------------|
| `RUN_PROJECT.bat` | Windows automated setup |
| `./RUN_PROJECT.sh` | Linux/Mac automated setup |
| `python run_discovery.py` | Standard discovery |
| `python run_discovery_checkpoint.py` | Checkpoint discovery |
| `python -m pytest tests/` | Run all tests |
| `pip install -r requirementupdated_fixed.txt` | Install dependencies |
