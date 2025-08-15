#!/bin/bash

echo "========================================"
echo "    AI VULNERABILITY DISCOVERY TOOL"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed!"
    echo "Please install Python 3.8+"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "myenv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv myenv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment!"
        exit 1
    fi
    echo "Virtual environment created successfully!"
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source myenv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r requirementupdated_fixed.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies!"
    exit 1
fi
echo "Dependencies installed successfully!"

# Create necessary directories
echo "Creating output directories..."
mkdir -p outputs
mkdir -p data/prompts
mkdir -p data/reference

# Check config.json exists
if [ ! -f "config.json" ]; then
    echo "WARNING: config.json not found!"
    echo "Please create config.json with your API keys and settings"
    exit 1
fi

# Run the main discovery script
echo
echo "========================================"
echo "Starting Vulnerability Discovery..."
echo "========================================"
echo

# Ask user which script to run
echo "Choose which script to run:"
echo "1. Standard discovery (run_discovery.py)"
echo "2. Checkpoint-enabled discovery (run_discovery_checkpoint.py)"
echo

read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo "Running standard discovery..."
        python run_discovery.py
        ;;
    2)
        echo "Running checkpoint-enabled discovery..."
        python run_discovery_checkpoint.py
        ;;
    *)
        echo "Invalid choice, running standard discovery..."
        python run_discovery.py
        ;;
esac

echo
echo "========================================"
echo "Discovery process completed!"
echo "Check the 'outputs' directory for results"
echo "========================================"
