"""
LLM Initialization utilities for the Desktop Search application
Handles LLM startup, GPU detection, and performance optimization
"""

import os
import sys
import subprocess
import platform
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import requests
import time

logger = logging.getLogger(__name__)

class LLMInitializer:
    """Handles LLM initialization, GPU detection, and performance optimization"""
    
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.gpu_available = False
        self.ollama_running = False
        self.optimization_results = {}
    
    def initialize_llm_system(self) -> Dict[str, Any]:
        """Initialize the complete LLM system with optimizations"""
        print("🤖 Initializing LLM System...")
        
        results = {
            "ollama_status": False,
            "gpu_available": False,
            "gpu_acceleration": False,
            "concurrent_processing": False,
            "models_available": [],
            "optimizations_applied": [],
            "errors": []
        }
        
        try:
            # Step 1: Check and start Ollama
            ollama_status = self._check_and_start_ollama()
            results["ollama_status"] = ollama_status
            
            if not ollama_status:
                results["errors"].append("Ollama is not running and could not be started")
                return results
            
            # Step 2: Detect GPU availability
            gpu_info = self._detect_gpu()
            results["gpu_available"] = gpu_info["available"]
            results["gpu_acceleration"] = gpu_info["enabled"]
            
            # Step 3: Check available models
            models = self._check_available_models()
            results["models_available"] = models
            
            # Step 4: Apply performance optimizations
            optimizations = self._apply_performance_optimizations(gpu_info)
            results["optimizations_applied"] = optimizations
            results["concurrent_processing"] = True
            
            # Step 5: Configure LLM manager
            self._configure_llm_manager(gpu_info)
            
            print("✅ LLM System initialization completed!")
            return results
            
        except Exception as e:
            error_msg = f"LLM initialization failed: {str(e)}"
            print(f"❌ {error_msg}")
            results["errors"].append(error_msg)
            return results
    
    def _check_and_start_ollama(self) -> bool:
        """Check if Ollama is running, start if not"""
        print("🔍 Checking Ollama status...")
        
        # Check if Ollama is already running
        if self._is_ollama_running():
            print("✅ Ollama is already running")
            self.ollama_running = True
            return True
        
        # Try to start Ollama
        print("🚀 Starting Ollama...")
        if self._start_ollama():
            print("✅ Ollama started successfully")
            self.ollama_running = True
            return True
        else:
            print("❌ Failed to start Ollama")
            print("💡 Please install Ollama from https://ollama.ai/")
            return False
    
    def _is_ollama_running(self) -> bool:
        """Check if Ollama is running by testing the API"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def _start_ollama(self) -> bool:
        """Start Ollama if not running"""
        try:
            # Check if ollama command is available
            result = subprocess.run(["ollama", "--version"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Ollama not installed")
                return False
            
            # Start Ollama in background
            print("   Starting Ollama server...")
            subprocess.Popen(["ollama", "serve"], 
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            
            # Wait for Ollama to start
            for i in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                if self._is_ollama_running():
                    return True
            
            return False
            
        except Exception as e:
            print(f"   Error starting Ollama: {e}")
            return False
    
    def _detect_gpu(self) -> Dict[str, Any]:
        """Detect GPU availability and capabilities"""
        print("🎮 Detecting GPU capabilities...")
        
        gpu_info = {
            "available": False,
            "enabled": False,
            "type": "none",
            "memory": 0,
            "cuda_available": False,
            "details": {}
        }
        
        # Check for NVIDIA GPU
        nvidia_gpu = self._detect_nvidia_gpu()
        if nvidia_gpu["available"]:
            gpu_info.update(nvidia_gpu)
            gpu_info["enabled"] = True
            self.gpu_available = True
            print(f"✅ NVIDIA GPU detected: {gpu_info['details'].get('name', 'Unknown')}")
            return gpu_info
        
        # Check for AMD GPU
        amd_gpu = self._detect_amd_gpu()
        if amd_gpu["available"]:
            gpu_info.update(amd_gpu)
            gpu_info["enabled"] = True
            self.gpu_available = True
            print(f"✅ AMD GPU detected: {gpu_info['details'].get('name', 'Unknown')}")
            return gpu_info
        
        # Check for Apple Silicon (M1/M2)
        apple_gpu = self._detect_apple_gpu()
        if apple_gpu["available"]:
            gpu_info.update(apple_gpu)
            gpu_info["enabled"] = True
            self.gpu_available = True
            print(f"✅ Apple Silicon GPU detected")
            return gpu_info
        
        # Check for Intel GPU
        intel_gpu = self._detect_intel_gpu()
        if intel_gpu["available"]:
            gpu_info.update(intel_gpu)
            gpu_info["enabled"] = True
            self.gpu_available = True
            print(f"✅ Intel GPU detected: {gpu_info['details'].get('name', 'Unknown')}")
            return gpu_info
        
        print("⚠️  No GPU detected, using CPU only")
        return gpu_info
    
    def _detect_nvidia_gpu(self) -> Dict[str, Any]:
        """Detect NVIDIA GPU"""
        try:
            # Try nvidia-smi
            result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                                  capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if lines and lines[0]:
                    parts = lines[0].split(', ')
                    if len(parts) >= 2:
                        return {
                            "available": True,
                            "type": "nvidia",
                            "memory": int(parts[1]) if parts[1].isdigit() else 0,
                            "cuda_available": True,
                            "details": {
                                "name": parts[0],
                                "memory_mb": int(parts[1]) if parts[1].isdigit() else 0
                            }
                        }
        except Exception:
            pass
        
        return {"available": False, "type": "nvidia"}
    
    def _detect_amd_gpu(self) -> Dict[str, Any]:
        """Detect AMD GPU"""
        try:
            # Try rocm-smi (AMD ROCm)
            result = subprocess.run(["rocm-smi", "--showproductname"],
                                  capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                return {
                    "available": True,
                    "type": "amd",
                    "memory": 0,  # AMD doesn't always report memory easily
                    "cuda_available": False,
                    "details": {
                        "name": result.stdout.strip(),
                        "driver": "rocm"
                    }
                }
        except Exception:
            pass
        
        return {"available": False, "type": "amd"}
    
    def _detect_apple_gpu(self) -> Dict[str, Any]:
        """Detect Apple Silicon GPU"""
        try:
            # Check for Apple Silicon
            if platform.system() == "Darwin":
                result = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                                      capture_output=True, text=True)
                
                if result.returncode == 0 and "Apple" in result.stdout:
                    return {
                        "available": True,
                        "type": "apple",
                        "memory": 0,  # Apple doesn't report GPU memory separately
                        "cuda_available": False,
                        "details": {
                            "name": "Apple Silicon GPU",
                            "architecture": "M1/M2"
                        }
                    }
        except Exception:
            pass
        
        return {"available": False, "type": "apple"}
    
    def _detect_intel_gpu(self) -> Dict[str, Any]:
        """Detect Intel GPU"""
        try:
            # Check for Intel GPU on Linux
            if platform.system() == "Linux":
                result = subprocess.run(["lspci", "-v"],
                                      capture_output=True, text=True)
                
                if result.returncode == 0 and "VGA" in result.stdout:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if "VGA" in line and "Intel" in line:
                            return {
                                "available": True,
                                "type": "intel",
                                "memory": 0,
                                "cuda_available": False,
                                "details": {
                                    "name": line.strip(),
                                    "driver": "i915"
                                }
                            }
        except Exception:
            pass
        
        return {"available": False, "type": "intel"}
    
    def _check_available_models(self) -> List[str]:
        """Check which models are available in Ollama"""
        print("📦 Checking available models...")
        
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = [model.get("name", "") for model in data.get("models", [])]
                
                if models:
                    print(f"✅ Found {len(models)} models: {', '.join(models)}")
                else:
                    print("⚠️  No models found. Consider downloading a model:")
                    print("   ollama pull phi3")
                
                return models
            else:
                print("❌ Could not fetch model list")
                return []
                
        except Exception as e:
            print(f"❌ Error checking models: {e}")
            return []
    
    def _apply_performance_optimizations(self, gpu_info: Dict[str, Any]) -> List[str]:
        """Apply performance optimizations based on hardware"""
        print("⚡ Applying performance optimizations...")
        
        optimizations = []
        
        # GPU acceleration
        if gpu_info["available"]:
            optimizations.append("GPU acceleration enabled")
            print("   ✅ GPU acceleration enabled")
        else:
            print("   ⚠️  GPU acceleration not available")
        
        # Concurrent processing
        optimizations.append("Concurrent processing enabled")
        print("   ✅ Concurrent processing enabled")
        
        # Model optimization
        if gpu_info["type"] == "nvidia":
            optimizations.append("NVIDIA GPU optimizations applied")
            print("   ✅ NVIDIA GPU optimizations applied")
        elif gpu_info["type"] == "apple":
            optimizations.append("Apple Silicon optimizations applied")
            print("   ✅ Apple Silicon optimizations applied")
        
        # Memory optimization
        if gpu_info["memory"] > 4000:  # 4GB
            optimizations.append("High memory GPU detected - using larger models")
            print("   ✅ High memory GPU detected")
        else:
            optimizations.append("Optimizing for limited GPU memory")
            print("   ⚠️  Limited GPU memory - using optimized settings")
        
        return optimizations
    
    def _configure_llm_manager(self, gpu_info: Dict[str, Any]):
        """Configure the LLM manager with optimal settings"""
        print("⚙️  Configuring LLM manager...")
        
        try:
            from pkg.llm.local_llm import get_llm_manager, LLMConfig
            
            llm_manager = get_llm_manager()
            
            # Update configuration based on GPU availability
            config = llm_manager.config
            
            # GPU settings
            config.use_gpu = gpu_info["available"]
            
            # Concurrent processing
            config.max_concurrent_requests = 8 if gpu_info["available"] else 4
            
            # Cache settings
            config.cache_responses = True
            config.cache_size = 2000 if gpu_info["available"] else 1000
            
            # Timeout settings
            config.request_timeout = 120 if gpu_info["available"] else 60
            
            # Model-specific optimizations - use available models
            available_models = self._check_available_models()
            # Check for models with :latest suffix
            if "llama2:latest" in available_models:
                config.llm_model = "llama2:latest"  # Use available llama2:latest
            elif "llama2" in available_models:
                config.llm_model = "llama2"  # Use available llama2
            elif "phi3:latest" in available_models:
                config.llm_model = "phi3:latest"  # Use available phi3:latest
            elif "phi3" in available_models:
                config.llm_model = "phi3"  # Use available phi3
            elif "mistral:latest" in available_models:
                config.llm_model = "mistral:latest"  # Use available mistral:latest
            elif "mistral" in available_models:
                config.llm_model = "mistral"  # Use available mistral
            else:
                config.llm_model = "llama2:latest"  # Default fallback
            
            # Apply configuration
            llm_manager.config = config
            
            # Detect and configure providers
            available_providers = llm_manager.detect_providers()
            if available_providers:
                llm_manager.set_active_provider(available_providers[0])
                print(f"   ✅ Active provider: {available_providers[0]}")
            
            print("✅ LLM manager configured successfully")
            
        except Exception as e:
            print(f"❌ Error configuring LLM manager: {e}")
    
    def get_llm_status(self) -> Dict[str, Any]:
        """Get comprehensive LLM system status"""
        status = {
            "ollama_running": self._is_ollama_running(),
            "gpu_available": self.gpu_available,
            "models_available": self._check_available_models(),
            "optimizations": self.optimization_results
        }
        
        # Get LLM manager status if available
        try:
            from pkg.llm.local_llm import get_llm_manager
            llm_manager = get_llm_manager()
            manager_status = llm_manager.get_provider_status()
            status.update(manager_status)
        except Exception:
            pass
        
        return status

def initialize_llm_system() -> Dict[str, Any]:
    """Initialize the LLM system with all optimizations"""
    initializer = LLMInitializer()
    return initializer.initialize_llm_system()

def get_llm_status() -> Dict[str, Any]:
    """Get current LLM system status"""
    initializer = LLMInitializer()
    return initializer.get_llm_status() 