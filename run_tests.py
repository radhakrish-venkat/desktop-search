#!/usr/bin/env python3
"""Test runner for the desktop search application."""

import unittest
import sys
import os
import time
from io import StringIO

# Add the project root to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def run_all_tests():
    """Run all tests and return results."""
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(project_root, 'tests')
    
    # Find all test files
    test_files = [
        'tests.test_file_parsers',
        'tests.test_indexer', 
        'tests.test_searcher',
        'tests.test_cli',
        'tests.test_integration'
    ]
    
    # Create test suite
    suite = unittest.TestSuite()
    
    for test_module in test_files:
        try:
            module_suite = loader.loadTestsFromName(test_module)
            suite.addTest(module_suite)
            print(f"✅ Loaded tests from {test_module}")
        except Exception as e:
            print(f"❌ Failed to load tests from {test_module}: {e}")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=StringIO())
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    return result, end_time - start_time

def run_specific_test(test_name):
    """Run a specific test module."""
    loader = unittest.TestLoader()
    
    try:
        suite = loader.loadTestsFromName(f'tests.{test_name}')
        runner = unittest.TextTestRunner(verbosity=2)
        start_time = time.time()
        result = runner.run(suite)
        end_time = time.time()
        
        return result, end_time - start_time
    except Exception as e:
        print(f"❌ Failed to run test {test_name}: {e}")
        return None, 0

def print_test_summary(result, duration):
    """Print a summary of test results."""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if result:
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
        print(f"Duration: {duration:.2f} seconds")
        
        if result.failures:
            print("\nFAILURES:")
            for test, traceback in result.failures:
                print(f"  ❌ {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if result.errors:
            print("\nERRORS:")
            for test, traceback in result.errors:
                print(f"  ❌ {test}: {traceback.split('Exception:')[-1].strip()}")
        
        if result.wasSuccessful():
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n❌ {len(result.failures) + len(result.errors)} TESTS FAILED")
    else:
        print("❌ No test results available")

def main():
    """Main test runner function."""
    print("Desktop Search - Test Runner")
    print("="*40)
    
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        print(f"Running specific test: {test_name}")
        result, duration = run_specific_test(test_name)
    else:
        # Run all tests
        print("Running all tests...")
        result, duration = run_all_tests()
    
    print_test_summary(result, duration)
    
    # Exit with appropriate code
    if result and result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main() 