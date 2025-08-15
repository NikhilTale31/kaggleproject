"""
Vendor Setup Script for Kaggle
Pre-installs dependencies to avoid repeated downloads
"""

import subprocess
import sys
from pathlib import Path

def setup_vendor_environment():
    """Create vendor environment with pre-installed dependencies"""
    
    # Create vendor directory
    vendor_dir = Path("vendor")
    vendor_dir.mkdir(exist_ok=True)
    
    # Install dependencies to vendor directory
    requirements_file = "requirements_competition.txt"
    
    if Path(requirements_file).exists():
        print("📦 Setting up vendor environment...")
        
        # Install to vendor directory
        cmd = [
            sys.executable, "-m", "pip", "install",
            "-r", requirements_file,
            "-t", str(vendor_dir),
            "--upgrade"
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print("✅ Vendor environment ready!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error setting up vendor: {e}")
            return False
    
    return False

if __name__ == "__main__":
    setup_vendor_environment()
