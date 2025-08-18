#!/usr/bin/env python3
"""
Smart dependency installer that checks vendor directory first.
Avoids re-downloading packages if they already exist.
Perfect for Kaggle/Colab where sessions restart frequently.
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

# Detect environment
if 'KAGGLE_KERNEL_RUN_TYPE' in os.environ:
    VENDOR_DIR = "/kaggle/working/vendor"
    ENV_NAME = "Kaggle"
elif 'COLAB_GPU' in os.environ:
    VENDOR_DIR = "/content/vendor"
    ENV_NAME = "Colab"
else:
    VENDOR_DIR = os.path.join(os.getcwd(), "vendor")
    ENV_NAME = "Local"

# Add vendor directory to Python path FIRST
sys.path.insert(0, VENDOR_DIR)

def check_package_installed(package_name):
    """Check if a package is available for import."""
    # Handle special cases
    if package_name == "bitsandbytes" and sys.platform == "win32":
        return True  # Skip on Windows
    
    # Map package names to import names
    import_map = {
        "python-dotenv": "dotenv",
        "asyncio-throttle": "asyncio_throttle",
        "huggingface_hub": "huggingface_hub",
        "huggingface-hub": "huggingface_hub",
        "pytest-asyncio": "pytest_asyncio",
        "pytest-cov": "pytest_cov",
        "types-aiohttp": "types_aiohttp"
    }
    
    import_name = import_map.get(package_name, package_name)
    
    # First check if it's in vendor directory
    vendor_package_path = os.path.join(VENDOR_DIR, import_name)
    if os.path.exists(vendor_package_path) or os.path.exists(vendor_package_path + ".py"):
        return True
    
    # Then check if it's importable
    spec = importlib.util.find_spec(import_name)
    return spec is not None

def parse_requirements(req_file):
    """Parse requirements.txt and return list of packages."""
    packages = []
    with open(req_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Handle platform-specific markers
            if ';' in line:
                pkg, condition = line.split(';', 1)
                # Check platform condition
                if 'platform_system != "Windows"' in condition and sys.platform == "win32":
                    continue
                line = pkg.strip()
            # Extract package name (before any version specifier)
            for sep in ['==', '>=', '<=', '>', '<', '~=']:
                if sep in line:
                    pkg_name = line.split(sep)[0].strip()
                    break
            else:
                pkg_name = line.strip()
            
            packages.append((pkg_name, line))
    return packages

def smart_install():
    """Install only missing packages to vendor directory."""
    print(f"🔍 Smart Install for {ENV_NAME}")
    print(f"📁 Vendor directory: {VENDOR_DIR}")
    
    # Create vendor directory if it doesn't exist
    os.makedirs(VENDOR_DIR, exist_ok=True)
    
    # Check for requirements file
    req_file = "requirements_fixed_clean.txt"
    if not os.path.exists(req_file):
        print(f"❌ {req_file} not found!")
        return
    
    # Parse requirements
    packages = parse_requirements(req_file)
    
    # Check which packages need installation
    to_install = []
    already_installed = []
    
    for pkg_name, full_spec in packages:
        if check_package_installed(pkg_name):
            already_installed.append(pkg_name)
        else:
            to_install.append(full_spec)
    
    # Report status
    print(f"\n✅ Already installed ({len(already_installed)}): {', '.join(already_installed[:5])}{'...' if len(already_installed) > 5 else ''}")
    
    if to_install:
        print(f"\n📦 Need to install ({len(to_install)}): {', '.join([p.split('==')[0] for p in to_install[:5]])}{'...' if len(to_install) > 5 else ''}")
        
        # Install missing packages to vendor directory
        print(f"\n🔧 Installing to {VENDOR_DIR}...")
        cmd = [sys.executable, "-m", "pip", "install", "--target", VENDOR_DIR, "--upgrade"] + to_install
        
        try:
            subprocess.check_call(cmd)
            print("\n✅ Installation complete!")
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Installation failed: {e}")
            print("Trying individual package installation...")
            
            # Try installing packages one by one
            for pkg in to_install:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "--target", VENDOR_DIR, pkg])
                    print(f"✅ Installed {pkg}")
                except:
                    print(f"❌ Failed to install {pkg}")
    else:
        print("\n✨ All packages already installed! No downloads needed.")
    
    # Final setup
    print(f"\n🔧 Setting up Python path...")
    print(f"sys.path[0] = {VENDOR_DIR}")
    
    # Create a setup confirmation file
    setup_file = os.path.join(VENDOR_DIR, ".setup_complete")
    with open(setup_file, 'w') as f:
        f.write(f"Setup completed for {ENV_NAME}\n")
        f.write(f"Vendor directory: {VENDOR_DIR}\n")
        f.write(f"Packages: {len(already_installed) + len(to_install)}\n")
    
    print("\n✅ Smart install complete! You can now run your project.")
    print("\n📝 Next steps:")
    print("1. If this is your first run, restart the runtime")
    print("2. Run: python run_competition.py")

if __name__ == "__main__":
    smart_install()
