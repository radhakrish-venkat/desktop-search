#!/usr/bin/env python3
"""
Comprehensive startup script for Desktop Search
Handles LLM initialization, GPU detection, and performance optimization
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def check_ollama_installation():
    """Check if Ollama is installed"""
    try:
        result = subprocess.run(["ollama", "--version"], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def install_ollama():
    """Install Ollama if not present"""
    print("📦 Installing Ollama...")
    
    system = os.name
    if system == "nt":  # Windows
        print("   Please install Ollama manually from https://ollama.ai/")
        return False
    elif system == "posix":  # Unix/Linux/macOS
        try:
            # Try to install Ollama
            if os.path.exists("/etc/debian_version"):  # Debian/Ubuntu
                subprocess.run(["curl", "-fsSL", "https://ollama.ai/install.sh", "|", "sh"], 
                             shell=True, check=True)
            elif os.path.exists("/etc/redhat-release"):  # RHEL/CentOS
                subprocess.run(["curl", "-fsSL", "https://ollama.ai/install.sh", "|", "sh"], 
                             shell=True, check=True)
            elif os.path.exists("/System/Library/CoreServices/SystemVersion.plist"):  # macOS
                subprocess.run(["brew", "install", "ollama"], check=True)
            else:
                subprocess.run(["curl", "-fsSL", "https://ollama.ai/install.sh", "|", "sh"], 
                             shell=True, check=True)
            
            print("✅ Ollama installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install Ollama automatically")
            print("   Please install manually from https://ollama.ai/")
            return False
    else:
        print("❌ Unsupported operating system")
        return False

def download_default_model():
    """Download a default model if none are available"""
    print("📥 Downloading default model (phi3)...")
    
    try:
        subprocess.run(["ollama", "pull", "phi3"], check=True)
        print("✅ Default model downloaded successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to download default model")
        return False

def check_gpu_support():
    """Check GPU support and provide recommendations"""
    print("🎮 Checking GPU support...")
    
    gpu_info = {
        "nvidia": False,
        "amd": False,
        "apple": False,
        "intel": False
    }
    
    # Check NVIDIA
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True)
        if result.returncode == 0:
            gpu_info["nvidia"] = True
            print("✅ NVIDIA GPU detected")
    except FileNotFoundError:
        pass
    
    # Check AMD
    try:
        result = subprocess.run(["rocm-smi"], capture_output=True)
        if result.returncode == 0:
            gpu_info["amd"] = True
            print("✅ AMD GPU detected")
    except FileNotFoundError:
        pass
    
    # Check Apple Silicon
    if os.path.exists("/System/Library/CoreServices/SystemVersion.plist"):
        try:
            result = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], 
                                  capture_output=True, text=True)
            if "Apple" in result.stdout:
                gpu_info["apple"] = True
                print("✅ Apple Silicon GPU detected")
        except:
            pass
    
    # Check Intel
    if os.name == "posix" and not os.path.exists("/System/Library/CoreServices/SystemVersion.plist"):
        try:
            result = subprocess.run(["lspci"], capture_output=True, text=True)
            if "VGA" in result.stdout and "Intel" in result.stdout:
                gpu_info["intel"] = True
                print("✅ Intel GPU detected")
        except:
            pass
    
    if not any(gpu_info.values()):
        print("⚠️  No GPU detected - will use CPU only")
        print("💡 For better performance, consider:")
        print("   - NVIDIA GPU with CUDA support")
        print("   - AMD GPU with ROCm support")
        print("   - Apple Silicon (M1/M2)")
    
    return gpu_info

def initialize_system():
    """Initialize the complete system"""
    print("🚀 Desktop Search System Initialization")
    print("=" * 50)
    
    # Step 1: Check Ollama
    print("\n📦 Step 1: Checking Ollama installation...")
    if not check_ollama_installation():
        print("❌ Ollama not found")
        install_choice = input("Would you like to install Ollama? (y/n): ").lower()
        if install_choice == 'y':
            if not install_ollama():
                print("❌ Ollama installation failed")
                return False
        else:
            print("⚠️  LLM features will not be available without Ollama")
    
    # Step 2: Check GPU support
    print("\n🎮 Step 2: Checking GPU support...")
    gpu_info = check_gpu_support()
    
    # Step 3: Initialize application
    print("\n🔧 Step 3: Initializing application...")
    try:
        from pkg.utils.initialization import initialize_app
        if not initialize_app():
            print("❌ Application initialization failed")
            return False
    except Exception as e:
        print(f"❌ Error during application initialization: {e}")
        return False
    
    # Step 4: Initialize LLM system
    print("\n🤖 Step 4: Initializing LLM system...")
    try:
        from pkg.utils.llm_initialization import initialize_llm_system
        llm_results = initialize_llm_system()
        
        if llm_results.get("errors"):
            print("⚠️  LLM initialization warnings:")
            for error in llm_results["errors"]:
                print(f"   - {error}")
        
        # Check if models are available
        models = llm_results.get("models_available", [])
        if not models:
            print("📥 No models found, downloading default model...")
            if download_default_model():
                print("✅ Default model downloaded")
            else:
                print("⚠️  Failed to download default model")
                print("   Run manually: ollama pull phi3")
    
    except Exception as e:
        print(f"❌ Error during LLM initialization: {e}")
        print("⚠️  LLM features may not be available")
    
    print("\n✅ System initialization completed!")
    return True

def start_server(use_https=True):
    """Start the server with appropriate configuration"""
    print(f"\n🌐 Starting server ({'HTTPS' if use_https else 'HTTP'})...")
    
    if use_https:
        # Check for certificates
        certs_dir = Path("certs")
        key_file = certs_dir / "key.pem"
        cert_file = certs_dir / "cert.pem"
        
        if not key_file.exists() or not cert_file.exists():
            print("❌ SSL certificates not found!")
            print("   Generating certificates...")
            try:
                subprocess.run(["python", "generate_certs.py"], check=True)
            except subprocess.CalledProcessError:
                print("❌ Failed to generate certificates")
                print("   Switching to HTTP mode...")
                use_https = False
        
        if use_https:
            print("🔐 Starting with HTTPS...")
            subprocess.run(["python", "start_https.py"])
        else:
            print("🌐 Starting with HTTP...")
            subprocess.run(["python", "start_api.py"])
    else:
        print("🌐 Starting with HTTP...")
        subprocess.run(["python", "start_api.py"])

def main():
    """Main startup function"""
    print("🚀 Desktop Search Startup")
    print("=" * 30)
    
    # Initialize system
    if not initialize_system():
        print("❌ System initialization failed")
        sys.exit(1)
    
    # Ask user for server type
    print("\n🌐 Server Configuration:")
    print("1. HTTPS (recommended, secure)")
    print("2. HTTP (simple, no encryption)")
    
    while True:
        choice = input("Choose server type (1/2): ").strip()
        if choice == "1":
            start_server(use_https=True)
            break
        elif choice == "2":
            start_server(use_https=False)
            break
        else:
            print("Please enter 1 or 2")

if __name__ == "__main__":
    main() 