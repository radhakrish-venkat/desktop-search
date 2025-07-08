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
        'tests.test_integration',
        'tests.test_security'  # Added security tests
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

def run_security_tests():
    """Run only security tests."""
    print("🔒 Running Security Tests...")
    
    loader = unittest.TestLoader()
    try:
        security_suite = loader.loadTestsFromName('tests.test_security')
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(security_suite)
        
        if result.wasSuccessful():
            print("✅ All security tests passed!")
        else:
            print("❌ Some security tests failed!")
        
        return result.wasSuccessful()
    except Exception as e:
        print(f"❌ Failed to run security tests: {e}")
        return False

if __name__ == '__main__':
    print("🧪 Desktop Search Test Suite")
    print("=" * 50)
    
    # Check if user wants to run only security tests
    if len(sys.argv) > 1 and sys.argv[1] == '--security':
        success = run_security_tests()
        sys.exit(0 if success else 1)
    
    # Run all tests
    print("Running all tests...")
    result, duration = run_all_tests()
    
    print("\n" + "=" * 50)
    print(f"⏱️  Total test time: {duration:.2f} seconds")
    
    if result.wasSuccessful():
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        sys.exit(1) 