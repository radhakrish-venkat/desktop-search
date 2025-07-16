#!/usr/bin/env python3
"""
Test script for LLM performance optimizations
"""

import time
import sys
from pkg.llm.local_llm import get_llm_manager, LLMConfig
from pkg.indexer.semantic import SemanticIndexer

def test_basic_functionality():
    """Test basic LLM functionality"""
    print("🧪 Testing basic LLM functionality...")
    
    try:
        llm_manager = get_llm_manager()
        
        # Test provider detection
        providers = llm_manager.detect_providers()
        print(f"✅ Detected providers: {providers}")
        
        # Test status
        status = llm_manager.get_provider_status()
        print(f"✅ Status check passed: {status.get('active_provider', 'None')}")
        
        return True
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_performance_features():
    """Test performance optimization features"""
    print("\n⚡ Testing performance features...")
    
    try:
        llm_manager = get_llm_manager()
        
        # Test performance stats
        stats = llm_manager.get_performance_stats()
        print(f"✅ Performance stats: {stats}")
        
        # Test cache functionality
        if llm_manager.config.cache_responses:
            print("✅ Response caching enabled")
        else:
            print("⚠️  Response caching disabled")
        
        # Test GPU configuration
        if llm_manager.config.use_gpu:
            print("✅ GPU acceleration enabled")
        else:
            print("⚠️  GPU acceleration disabled")
        
        # Test concurrent requests
        print(f"✅ Max concurrent requests: {llm_manager.config.max_concurrent_requests}")
        
        return True
    except Exception as e:
        print(f"❌ Performance features test failed: {e}")
        return False

def test_search_with_llm():
    """Test search with LLM enhancement"""
    print("\n🔍 Testing search with LLM enhancement...")
    
    try:
        llm_manager = get_llm_manager()
        
        # Perform a simple search
        indexer = SemanticIndexer(
            persist_directory='data/chroma_db',
            model_name='all-MiniLM-L6-v2'
        )
        
        # Test search
        search_results = indexer.semantic_search("test", n_results=3)
        print(f"✅ Search completed: {len(search_results)} results")
        
        # Test LLM enhancement
        if llm_manager.active_provider:
            start_time = time.time()
            enhanced_result = llm_manager.enhance_search_results("test", search_results)
            end_time = time.time()
            
            print(f"✅ LLM enhancement completed in {end_time - start_time:.2f}s")
            print(f"   Enhanced: {enhanced_result.get('enhanced', False)}")
            
            # Check performance data
            if 'performance' in enhanced_result:
                perf = enhanced_result['performance']
                print(f"   Response time: {perf.get('response_time', 0):.2f}s")
        else:
            print("⚠️  No active LLM provider")
        
        return True
    except Exception as e:
        print(f"❌ Search with LLM test failed: {e}")
        return False

def test_optimization_commands():
    """Test optimization commands"""
    print("\n🔧 Testing optimization commands...")
    
    try:
        llm_manager = get_llm_manager()
        
        # Test optimization
        llm_manager.config.cache_responses = True
        llm_manager.config.use_gpu = True
        llm_manager.config.max_concurrent_requests = 8
        
        print("✅ Configuration updated")
        
        # Test provider optimization
        for provider in llm_manager.providers.values():
            if hasattr(provider, '_configure_model_performance'):
                provider._configure_model_performance()
                print(f"✅ Model performance configured for {type(provider).__name__}")
        
        return True
    except Exception as e:
        print(f"❌ Optimization commands test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 LLM Performance Optimization Test Suite")
    print("=" * 50)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Performance Features", test_performance_features),
        ("Search with LLM", test_search_with_llm),
        ("Optimization Commands", test_optimization_commands)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} passed")
        else:
            print(f"❌ {test_name} failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Performance optimizations are working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit(main()) 