#!/usr/bin/env python3
"""
Test script for LLM startup and GPU detection
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_llm_initialization():
    """Test LLM initialization"""
    print("🧪 Testing LLM initialization...")
    
    try:
        from pkg.utils.llm_initialization import initialize_llm_system
        
        results = initialize_llm_system()
        
        print("\n📊 LLM Initialization Results:")
        print("=" * 40)
        
        # Check Ollama status
        ollama_status = results.get("ollama_status", False)
        print(f"Ollama Status: {'✅ Running' if ollama_status else '❌ Not running'}")
        
        # Check GPU status
        gpu_available = results.get("gpu_available", False)
        gpu_acceleration = results.get("gpu_acceleration", False)
        print(f"GPU Available: {'✅ Yes' if gpu_available else '❌ No'}")
        print(f"GPU Acceleration: {'✅ Enabled' if gpu_acceleration else '❌ Disabled'}")
        
        # Check concurrent processing
        concurrent = results.get("concurrent_processing", False)
        print(f"Concurrent Processing: {'✅ Enabled' if concurrent else '❌ Disabled'}")
        
        # Check models
        models = results.get("models_available", [])
        if models:
            print(f"Available Models: {', '.join(models)}")
        else:
            print("Available Models: None")
        
        # Check optimizations
        optimizations = results.get("optimizations_applied", [])
        if optimizations:
            print("\nOptimizations Applied:")
            for opt in optimizations:
                print(f"   ✅ {opt}")
        else:
            print("\nNo optimizations applied")
        
        # Check errors
        errors = results.get("errors", [])
        if errors:
            print("\nErrors:")
            for error in errors:
                print(f"   ❌ {error}")
        
        # Overall result
        if errors:
            print(f"\n❌ LLM initialization failed with {len(errors)} error(s)")
            return False
        else:
            print(f"\n✅ LLM initialization successful!")
            return True
            
    except Exception as e:
        print(f"❌ Error during LLM initialization test: {e}")
        return False

def test_gpu_detection():
    """Test GPU detection specifically"""
    print("\n🎮 Testing GPU detection...")
    
    try:
        from pkg.utils.llm_initialization import LLMInitializer
        
        initializer = LLMInitializer()
        gpu_info = initializer._detect_gpu()
        
        print(f"GPU Type: {gpu_info.get('type', 'none')}")
        print(f"GPU Available: {'✅ Yes' if gpu_info.get('available') else '❌ No'}")
        print(f"GPU Enabled: {'✅ Yes' if gpu_info.get('enabled') else '❌ No'}")
        print(f"GPU Memory: {gpu_info.get('memory', 0)} MB")
        print(f"CUDA Available: {'✅ Yes' if gpu_info.get('cuda_available') else '❌ No'}")
        
        details = gpu_info.get('details', {})
        if details:
            print("GPU Details:")
            for key, value in details.items():
                print(f"   {key}: {value}")
        
        return gpu_info.get('available', False)
        
    except Exception as e:
        print(f"❌ Error during GPU detection test: {e}")
        return False

def test_ollama_status():
    """Test Ollama status"""
    print("\n🔍 Testing Ollama status...")
    
    try:
        from pkg.utils.llm_initialization import LLMInitializer
        
        initializer = LLMInitializer()
        is_running = initializer._is_ollama_running()
        
        print(f"Ollama Running: {'✅ Yes' if is_running else '❌ No'}")
        
        if is_running:
            models = initializer._check_available_models()
            print(f"Available Models: {', '.join(models) if models else 'None'}")
        
        return is_running
        
    except Exception as e:
        print(f"❌ Error during Ollama status test: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 LLM Startup Test Suite")
    print("=" * 40)
    
    tests = [
        ("GPU Detection", test_gpu_detection),
        ("Ollama Status", test_ollama_status),
        ("LLM Initialization", test_llm_initialization)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        results[test_name] = test_func()
    
    print(f"\n📊 Test Results:")
    print("=" * 40)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! LLM system is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit(main()) 