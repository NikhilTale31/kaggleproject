"""
Setup script for Mistral-7B 4-bit quantization on Google Colab
Run this first to install all required dependencies with correct versions.
"""

import subprocess
import sys

def run_command(command):
    """Run a shell command and print output."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode == 0

def install_dependencies():
    """Install all required dependencies with correct versions."""
    print("🔧 Installing dependencies for Mistral-7B 4-bit quantization...\n")
    
    # First, upgrade pip
    print("📦 Upgrading pip...")
    run_command(f"{sys.executable} -m pip install --upgrade pip")
    
    # Install PyTorch with CUDA support (for A100)
    print("\n📦 Installing PyTorch with CUDA support...")
    run_command(f"{sys.executable} -m pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118")
    
    # Install transformers with latest version that supports proper BitsAndBytes integration
    print("\n📦 Installing Transformers...")
    run_command(f"{sys.executable} -m pip install transformers==4.36.2")
    
    # Install bitsandbytes for 4-bit quantization
    print("\n📦 Installing bitsandbytes...")
    run_command(f"{sys.executable} -m pip install bitsandbytes==0.41.3")
    
    # Install accelerate for model loading
    print("\n📦 Installing accelerate...")
    run_command(f"{sys.executable} -m pip install accelerate==0.25.0")
    
    # Install additional dependencies
    print("\n📦 Installing additional dependencies...")
    run_command(f"{sys.executable} -m pip install scipy sentencepiece protobuf")
    
    print("\n✅ All dependencies installed successfully!")

def verify_installation():
    """Verify that all components are properly installed."""
    print("\n🔍 Verifying installation...")
    
    try:
        import torch
        print(f"✓ PyTorch version: {torch.__version__}")
        print(f"✓ CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"✓ CUDA version: {torch.version.cuda}")
            print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
        
        import transformers
        print(f"✓ Transformers version: {transformers.__version__}")
        
        import bitsandbytes
        print(f"✓ Bitsandbytes version: {bitsandbytes.__version__}")
        
        import accelerate
        print(f"✓ Accelerate version: {accelerate.__version__}")
        
        print("\n✅ All components verified successfully!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Mistral-7B 4-bit Quantization Setup for Google Colab\n")
    
    # Install dependencies
    install_dependencies()
    
    # Verify installation
    if verify_installation():
        print("\n🎉 Setup completed successfully!")
        print("\nYou can now run the main script:")
        print("  python mistral_7b_4bit_colab.py")
    else:
        print("\n❌ Setup failed. Please check the errors above.")

if __name__ == "__main__":
    main()
