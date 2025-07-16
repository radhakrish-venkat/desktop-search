#!/usr/bin/env python3
"""
LLM Performance Benchmark Script
Tests LLM performance and provides optimization recommendations
"""

import time
import json
import statistics
from typing import List, Dict, Any
from pkg.llm.local_llm import get_llm_manager, LLMConfig
from pkg.indexer.semantic import SemanticIndexer

def run_benchmark_tests() -> Dict[str, Any]:
    """Run comprehensive LLM performance benchmarks"""
    
    print("🚀 Starting LLM Performance Benchmark...")
    print("=" * 60)
    
    llm_manager = get_llm_manager()
    results = {
        "provider_status": {},
        "response_times": [],
        "cache_performance": {},
        "throughput_tests": {},
        "recommendations": []
    }
    
    # Test 1: Provider Status
    print("\n📊 Test 1: Provider Status")
    print("-" * 30)
    
    status = llm_manager.get_provider_status()
    results["provider_status"] = status
    
    active_provider = status.get("active_provider")
    if active_provider:
        print(f"✅ Active Provider: {active_provider}")
    else:
        print("❌ No active provider found")
        return results
    
    # Test 2: Response Time Benchmark
    print("\n⏱️  Test 2: Response Time Benchmark")
    print("-" * 30)
    
    test_queries = [
        "What is machine learning?",
        "Explain artificial intelligence",
        "How does deep learning work?",
        "What are neural networks?",
        "Describe natural language processing"
    ]
    
    response_times = []
    for i, query in enumerate(test_queries, 1):
        print(f"   Testing query {i}/{len(test_queries)}: {query[:50]}...")
        
        start_time = time.time()
        try:
            # Perform search
            indexer = SemanticIndexer(
                persist_directory='data/chroma_db',
                model_name='all-MiniLM-L6-v2'
            )
            search_results = indexer.semantic_search(query, n_results=5)
            
            # Enhance with LLM
            enhanced_result = llm_manager.enhance_search_results(query, search_results)
            
            end_time = time.time()
            response_time = end_time - start_time
            response_times.append(response_time)
            
            print(f"      ✅ Response time: {response_time:.2f}s")
            
        except Exception as e:
            print(f"      ❌ Error: {e}")
            response_times.append(None)
    
    # Calculate statistics
    valid_times = [t for t in response_times if t is not None]
    if valid_times:
        results["response_times"] = {
            "times": valid_times,
            "average": statistics.mean(valid_times),
            "median": statistics.median(valid_times),
            "min": min(valid_times),
            "max": max(valid_times),
            "std_dev": statistics.stdev(valid_times) if len(valid_times) > 1 else 0
        }
        
        print(f"\n   📈 Response Time Statistics:")
        print(f"      Average: {results['response_times']['average']:.2f}s")
        print(f"      Median: {results['response_times']['median']:.2f}s")
        print(f"      Min: {results['response_times']['min']:.2f}s")
        print(f"      Max: {results['response_times']['max']:.2f}s")
        print(f"      Std Dev: {results['response_times']['std_dev']:.2f}s")
    
    # Test 3: Cache Performance
    print("\n💾 Test 3: Cache Performance")
    print("-" * 30)
    
    performance_stats = llm_manager.get_performance_stats()
    results["cache_performance"] = performance_stats
    
    print(f"   Total Requests: {performance_stats.get('total_requests', 0)}")
    print(f"   Cache Hits: {performance_stats.get('cache_hits', 0)}")
    print(f"   Cache Hit Rate: {performance_stats.get('cache_hit_rate', 0.0):.2%}")
    print(f"   Average Response Time: {performance_stats.get('average_response_time', 0.0):.2f}s")
    
    # Test 4: Throughput Test
    print("\n🔄 Test 4: Throughput Test")
    print("-" * 30)
    
    # Test concurrent requests
    concurrent_queries = [
        "What is AI?",
        "Explain ML",
        "Deep learning basics",
        "Neural networks",
        "Computer vision"
    ]
    
    start_time = time.time()
    try:
        # This would ideally test actual concurrent requests
        # For now, we'll simulate with sequential requests
        for query in concurrent_queries:
            indexer = SemanticIndexer(
                persist_directory='data/chroma_db',
                model_name='all-MiniLM-L6-v2'
            )
            search_results = indexer.semantic_search(query, n_results=3)
            llm_manager.enhance_search_results(query, search_results)
        
        end_time = time.time()
        total_time = end_time - start_time
        throughput = len(concurrent_queries) / total_time
        
        results["throughput_tests"] = {
            "queries_per_second": throughput,
            "total_time": total_time,
            "queries_processed": len(concurrent_queries)
        }
        
        print(f"   Queries per second: {throughput:.2f}")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Queries processed: {len(concurrent_queries)}")
        
    except Exception as e:
        print(f"   ❌ Throughput test failed: {e}")
    
    # Generate Recommendations
    print("\n💡 Test 5: Performance Recommendations")
    print("-" * 30)
    
    recommendations = []
    
    # Check response times
    if valid_times and statistics.mean(valid_times) > 5.0:
        recommendations.append("Consider using a smaller/faster model (e.g., phi3 instead of llama2)")
    
    if valid_times and statistics.mean(valid_times) > 10.0:
        recommendations.append("Response times are very slow - check GPU availability and model size")
    
    # Check cache performance
    cache_hit_rate = performance_stats.get('cache_hit_rate', 0.0)
    if cache_hit_rate < 0.1:
        recommendations.append("Cache hit rate is low - consider increasing cache size or optimizing queries")
    
    # Check configuration
    config = llm_manager.config
    if not config.use_gpu:
        recommendations.append("Enable GPU acceleration for faster inference")
    
    if not config.cache_responses:
        recommendations.append("Enable response caching for repeated queries")
    
    if config.max_concurrent_requests < 8:
        recommendations.append("Increase max concurrent requests to 8 for better throughput")
    
    if config.cache_size < 1000:
        recommendations.append("Consider increasing cache size to 1000+ for better hit rates")
    
    # Check provider status
    if not status.get("active_provider"):
        recommendations.append("No active LLM provider - install and configure Ollama")
    
    results["recommendations"] = recommendations
    
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
    
    if not recommendations:
        print("   ✅ No immediate optimizations needed - system is performing well!")
    
    return results

def save_benchmark_results(results: Dict[str, Any], filename: str = "llm_benchmark_results.json"):
    """Save benchmark results to a JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Benchmark results saved to: {filename}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")

def print_summary(results: Dict[str, Any]):
    """Print a summary of benchmark results"""
    print("\n" + "=" * 60)
    print("📊 BENCHMARK SUMMARY")
    print("=" * 60)
    
    # Provider Status
    status = results.get("provider_status", {})
    active_provider = status.get("active_provider", "None")
    print(f"Active Provider: {active_provider}")
    
    # Response Times
    response_times = results.get("response_times", {})
    if response_times:
        avg_time = response_times.get("average", 0)
        print(f"Average Response Time: {avg_time:.2f}s")
        
        if avg_time < 2.0:
            print("✅ Response times are excellent!")
        elif avg_time < 5.0:
            print("⚠️  Response times are acceptable")
        else:
            print("❌ Response times are slow - consider optimizations")
    
    # Cache Performance
    cache_perf = results.get("cache_performance", {})
    cache_hit_rate = cache_perf.get("cache_hit_rate", 0.0)
    print(f"Cache Hit Rate: {cache_hit_rate:.2%}")
    
    if cache_hit_rate > 0.3:
        print("✅ Cache performance is good!")
    elif cache_hit_rate > 0.1:
        print("⚠️  Cache performance is acceptable")
    else:
        print("❌ Cache performance is poor - consider optimizations")
    
    # Throughput
    throughput = results.get("throughput_tests", {})
    if throughput:
        qps = throughput.get("queries_per_second", 0)
        print(f"Throughput: {qps:.2f} queries/second")
        
        if qps > 1.0:
            print("✅ Throughput is good!")
        elif qps > 0.5:
            print("⚠️  Throughput is acceptable")
        else:
            print("❌ Throughput is low - consider optimizations")
    
    # Recommendations
    recommendations = results.get("recommendations", [])
    if recommendations:
        print(f"\n🔧 Optimization Recommendations ({len(recommendations)}):")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("\n✅ No optimizations needed - system is performing well!")

def main():
    """Main benchmark function"""
    print("🤖 LLM Performance Benchmark Tool")
    print("=" * 60)
    
    try:
        # Run benchmarks
        results = run_benchmark_tests()
        
        # Print summary
        print_summary(results)
        
        # Save results
        save_benchmark_results(results)
        
        print("\n🎉 Benchmark completed successfully!")
        print("💡 Use 'python main.py llm optimize' to apply recommended optimizations")
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 