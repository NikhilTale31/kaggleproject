#!/usr/bin/env python3
"""
Kaggle Setup Script with Vendor Dependencies
This script handles file upload and dependency management for Kaggle
"""

import os
import sys
import subprocess
import hashlib
import json
from pathlib import Path

class KaggleSetup:
    def __init__(self):
        self.project_root = Path.cwd()
        self.vendor_dir = self.project_root / "vendor"
        self.checksum_file = self.vendor_dir / ".checksums"
        
    def create_vendor_directory(self):
        """Create vendor directory for dependencies"""
        self.vendor_dir.mkdir(exist_ok=True)
        print("✅ Vendor directory created")
    
    def calculate_checksum(self, file_path):
        """Calculate MD5 checksum of requirements file"""
        if not file_path.exists():
            return None
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def save_checksum(self, checksum):
        """Save current checksum"""
        with open(self.checksum_file, 'w') as f:
            json.dump({"requirements_checksum": checksum}, f)
    
    def load_checksum(self):
        """Load saved checksum"""
        if not self.checksum_file.exists():
            return None
        try:
            with open(self.checksum_file, 'r') as f:
                data = json.load(f)
                return data.get("requirements_checksum")
        except:
            return None
    
    def check_dependencies_changed(self):
        """Check if requirements have changed"""
        current_checksum = self.calculate_checksum(Path("requirements_competition.txt"))
        saved_checksum = self.load_checksum()
        return current_checksum != saved_checksum
    
    def install_dependencies(self):
        """Install dependencies with vendor method"""
        print("🔍 Checking dependencies...")
        
        # Check if dependencies already installed
        if not self.check_dependencies_changed():
            print("✅ Dependencies already up to date, skipping installation")
            return
        
        print("📦 Installing dependencies...")
        
        # Install to vendor directory
        cmd = [
            sys.executable, "-m", "pip", "install",
            "-r", "requirements_competition.txt",
            "--target", str(self.vendor_dir),
            "--upgrade"
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            current_checksum = self.calculate_checksum(Path("requirements_competition.txt"))
            self.save_checksum(current_checksum)
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            sys.exit(1)
    
    def setup_kaggle_paths(self):
        """Setup paths for Kaggle environment"""
        vendor_path = str(self.vendor_dir)
        if vendor_path not in sys.path:
            sys.path.insert(0, vendor_path)
        
        # Create .env file for Kaggle
        env_content = f"""
# Kaggle environment setup
PYTHONPATH={vendor_path}:$PYTHONPATH
TRANSFORMERS_CACHE=/kaggle/working/.cache/transformers
HF_HOME=/kaggle/working/.cache/huggingface
"""
        with open(".env", "w") as f:
            f.write(env_content)
        
        print("✅ Kaggle paths configured")
    
    def create_upload_package(self):
        """Create package for Kaggle upload"""
        # Create upload directory
        upload_dir = Path("kaggle_upload")
        upload_dir.mkdir(exist_ok=True)
        
        # Copy all necessary files
        files_to_copy = [
            "src/", "data/", "config_competition.json", "requirements_competition.txt",
            "run_competition.py", "run_discovery.py", "run_discovery_checkpoint.py",
            "KAGGLE_NOTEBOOK.ipynb", "KAGGLE_SETUP.py"
        ]
        
        for item in files_to_copy:
            if Path(item).exists():
                if Path(item).is_dir():
                    os.system(f"cp -r {item} {upload_dir}/")
                else:
                    os.system(f"cp {item} {upload_dir}/")
        
        # Create upload instructions
        instructions = """
# Kaggle Upload Instructions

## Files to upload:
1. Upload entire `kaggle_upload/` directory to Kaggle
2. Upload `KAGGLE_NOTEBOOK.ipynb` as a new notebook
3. Upload `requirements_competition.txt` for dependencies

## Quick start:
```python
!python KAGGLE_SETUP.py
!python run_competition.py
```
"""
        with open(upload_dir / "UPLOAD_INSTRUCTIONS.md", "w") as f:
            f.write(instructions)
        
        print(f"✅ Upload package created at: {upload_dir}")
        print("📁 Upload these files to Kaggle:")
        print("   - kaggle_upload/ directory")
        print("   - KAGGLE_NOTEBOOK.ipynb")
    
    def run_setup(self):
        """Complete setup process"""
        print("🚀 Starting Kaggle setup...")
        
        self.create_vendor_directory()
        self.install_dependencies()
        self.setup_kaggle_paths()
        self.create_upload_package()
        
        print("\n🎉 Setup complete!")
        print("\nNext steps:")
        print("1. Upload kaggle_upload/ directory to Kaggle")
        print("2. Run: !python KAGGLE_SETUP.py")
        print("3. Run: !python run_competition.py")

if __name__ == "__main__":
    setup = KaggleSetup()
    setup.run_setup()
