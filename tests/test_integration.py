#!/usr/bin/env python3
"""Integration tests for the complete desktop search system."""

import unittest
import os
import sys
import tempfile
import shutil
import pickle
from click.testing import CliRunner
from typing import cast, Dict, Any

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the modules to test
from cli_commands.cli import cli
from pkg.indexer.core import build_index, save_index, load_index, get_index_stats
from pkg.searcher.core import search_index, search_with_highlighting
from pkg.file_parsers.parsers import get_text_from_file


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.runner = CliRunner()
        self.test_files = []

    def tearDown(self):
        """Clean up test fixtures."""
        for filepath in self.test_files:
            if os.path.exists(filepath):
                os.remove(filepath)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_test_file(self, filename, content):
        """Helper to create a test file."""
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        self.test_files.append(filepath)
        return filepath

    def test_complete_workflow(self):
        """Test the complete indexing and search workflow."""
        # Create test files with various content
        files = [
            ('python_guide.txt', 'Python is a high-level programming language. Python is great for beginners and experts alike.'),
            ('java_tutorial.txt', 'Java is an object-oriented programming language. Java is widely used in enterprise applications.'),
            ('javascript_notes.txt', 'JavaScript is a scripting language used for web development. JavaScript runs in browsers.'),
            ('programming_concepts.txt', 'Programming concepts include variables, functions, loops, and data structures.'),
            ('web_development.txt', 'Web development involves HTML, CSS, and JavaScript. Modern web development uses frameworks.'),
            ('data_science.txt', 'Data science combines statistics, programming, and domain expertise. Python is popular for data science.')
        ]
        
        for filename, content in files:
            self.create_test_file(filename, content)
        
        # Test 1: Build index
        print("\n--- Testing Index Building ---")
        index_data = build_index(self.test_dir)
        
        self.assertIsNotNone(index_data)
        index_data = cast(Dict[str, Any], index_data)
        self.assertIn('inverted_index', index_data)
        self.assertIn('document_store', index_data)
        self.assertIn('stats', index_data)
        
        # Verify all files were indexed
        self.assertEqual(len(index_data['document_store']), 6)
        
        # Verify some expected tokens
        inverted_index = index_data['inverted_index']
        self.assertIn('python', inverted_index)
        self.assertIn('java', inverted_index)
        self.assertIn('javascript', inverted_index)
        self.assertIn('programming', inverted_index)
        self.assertIn('development', inverted_index)
        
        print(f"✅ Index built successfully with {len(index_data['document_store'])} documents")
        
        # Test 2: Get index statistics
        print("\n--- Testing Index Statistics ---")
        stats = get_index_stats(index_data)
        
        self.assertIn('total_documents', stats)
        self.assertIn('unique_tokens', stats)
        self.assertIn('total_tokens', stats)
        self.assertIn('avg_tokens_per_doc', stats)
        self.assertIn('most_common_tokens', stats)
        
        print(f"✅ Statistics: {stats['total_documents']} documents, {stats['unique_tokens']} unique tokens")
        
        # Test 3: Basic search
        print("\n--- Testing Basic Search ---")
        search_queries = [
            ('python', 2),  # Should find python_guide.txt and data_science.txt
            ('java', 1),    # Should find java_tutorial.txt
            ('javascript', 2),  # Should find javascript_notes.txt and web_development.txt
            ('programming', 4),  # Should find multiple files
            ('web development', 2),  # Should find javascript_notes.txt and web_development.txt
            ('nonexistent', 0)  # Should find nothing
        ]
        
        for query, expected_count in search_queries:
            results = search_index(query, index_data)
            print(f"Query '{query}': {len(results)} results (expected {expected_count})")
            self.assertEqual(len(results), expected_count)
            
            # Verify result structure
            for result in results:
                self.assertIn('filepath', result)
                self.assertIn('snippet', result)
                self.assertIsInstance(result['filepath'], str)
                self.assertIsInstance(result['snippet'], str)
        
        print("✅ Basic search tests passed")
        
        # Test 4: Enhanced search with highlighting
        print("\n--- Testing Enhanced Search ---")
        enhanced_results = search_with_highlighting("python programming", index_data)
        
        self.assertGreater(len(enhanced_results), 0)
        
        # Verify enhanced result structure
        for result in enhanced_results:
            self.assertIn('filepath', result)
            self.assertIn('snippet', result)
            self.assertIn('score', result)
            self.assertIn('extension', result)
            self.assertIn('doc_id', result)
            self.assertIn('file_size', result)
            self.assertIsInstance(result['score'], float)
            self.assertGreaterEqual(result['score'], 0)
        
        print(f"✅ Enhanced search returned {len(enhanced_results)} results")
        
        # Test 5: Save and load index
        print("\n--- Testing Index Persistence ---")
        index_file = os.path.join(self.test_dir, 'test_index.pkl')
        
        # Save index
        success = save_index(index_data, index_file)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(index_file))
        
        # Load index
        loaded_data = load_index(index_file)
        self.assertIsNotNone(loaded_data)
        loaded_data = cast(Dict[str, Any], loaded_data)
        
        # Verify loaded data matches original
        self.assertEqual(loaded_data['inverted_index'], index_data['inverted_index'])
        self.assertEqual(loaded_data['document_store'], index_data['document_store'])
        self.assertEqual(loaded_data['indexed_directory'], index_data['indexed_directory'])
        
        print("✅ Index save/load tests passed")
        
        # Test 6: Search with loaded index
        print("\n--- Testing Search with Loaded Index ---")
        loaded_results = search_index("python", loaded_data)
        original_results = search_index("python", index_data)
        
        self.assertEqual(len(loaded_results), len(original_results))
        print("✅ Search with loaded index works correctly")

    def test_cli_integration(self):
        """Test CLI integration with real files."""
        # Create test files
        files = [
            ('document1.txt', 'This document contains information about Python programming.'),
            ('document2.txt', 'Another document about Java programming and software development.'),
            ('document3.txt', 'A third document discussing web development with JavaScript.')
        ]
        
        for filename, content in files:
            self.create_test_file(filename, content)
        
        # Test CLI index command
        print("\n--- Testing CLI Index Command ---")
        result = self.runner.invoke(cli, ['index', self.test_dir])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Starting indexing of directory', result.output)
        self.assertIn('Indexing complete', result.output)
        self.assertIn('Indexed 3 documents', result.output)
        
        print("✅ CLI index command works")
        
        # Test CLI search command (requires index in context)
        print("\n--- Testing CLI Search Command ---")
        # Note: This test requires the index to be in the CLI context
        # In a real scenario, you'd need to set up the context properly
        
        # Test CLI search with load option
        index_file = os.path.join(self.test_dir, 'cli_test_index.pkl')
        
        # Build and save index
        index_data = build_index(self.test_dir)
        index_data = cast(Dict[str, Any], index_data)
        save_index(index_data, index_file)
        
        # Test search with load
        result = self.runner.invoke(cli, ['search', 'python', '--load', index_file])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Searching for: \'python\'', result.output)
        
        print("✅ CLI search command works")

    def test_file_parser_integration(self):
        """Test file parser integration with real files."""
        print("\n--- Testing File Parser Integration ---")
        
        # Test text file parsing
        test_content = "This is a test document with some content about programming."
        test_file = self.create_test_file('test_parser.txt', test_content)
        
        extracted_text, extension = get_text_from_file(test_file)
        
        self.assertEqual(extracted_text, test_content)
        self.assertEqual(extension, '.txt')
        
        print("✅ Text file parsing works")
        
        # Test unsupported file
        unsupported_file = self.create_test_file('test.xyz', 'Unsupported content')
        extracted_text, extension = get_text_from_file(unsupported_file)
        
        self.assertIsNone(extracted_text)
        self.assertEqual(extension, '.xyz')
        
        print("✅ Unsupported file handling works")

    def test_large_dataset_performance(self):
        """Test performance with larger datasets."""
        print("\n--- Testing Performance with Larger Dataset ---")
        
        # Create 50 test files
        for i in range(50):
            content = f"Document {i} contains information about various topics including programming, development, and technology. "
            content += f"This is document number {i} with some unique content about specific subjects."
            self.create_test_file(f'doc_{i:02d}.txt', content)
        
        # Build index
        start_time = __import__('time').time()
        index_data = build_index(self.test_dir)
        index_data = cast(Dict[str, Any], index_data)
        build_time = __import__('time').time() - start_time
        
        self.assertIsNotNone(index_data)
        self.assertEqual(len(index_data['document_store']), 50)
        
        print(f"✅ Built index for 50 documents in {build_time:.2f} seconds")
        
        # Test search performance
        start_time = __import__('time').time()
        results = search_index("programming development", index_data)
        search_time = __import__('time').time() - start_time
        
        self.assertGreater(len(results), 0)
        print(f"✅ Search completed in {search_time:.3f} seconds with {len(results)} results")

    def test_error_handling_integration(self):
        """Test error handling in integration scenarios."""
        print("\n--- Testing Error Handling ---")
        
        # Test with non-existent directory
        index_data = build_index('/nonexistent/directory')
        self.assertIsNone(index_data)
        
        # Test with empty directory
        empty_dir = os.path.join(self.test_dir, 'empty')
        os.makedirs(empty_dir, exist_ok=True)
        index_data = build_index(empty_dir)
        index_data = cast(Dict[str, Any], index_data)
        
        self.assertIsNotNone(index_data)
        self.assertEqual(len(index_data['document_store']), 0)
        
        # Test search with empty index
        results = search_index("test", index_data)
        self.assertEqual(results, [])
        
        print("✅ Error handling works correctly")

    def test_search_ranking_integration(self):
        """Test search ranking with real data."""
        print("\n--- Testing Search Ranking ---")
        
        # Create files with different relevance to a query
        files = [
            ('highly_relevant.txt', 'Python programming language is the main topic of this document. Python is mentioned multiple times.'),
            ('moderately_relevant.txt', 'This document discusses programming in general, including Python as one of many languages.'),
            ('slightly_relevant.txt', 'This document is about software development, which sometimes involves programming languages like Python.')
        ]
        
        for filename, content in files:
            self.create_test_file(filename, content)
        
        # Build index
        index_data = build_index(self.test_dir)
        index_data = cast(Dict[str, Any], index_data)
        
        # Test search ranking
        results = search_with_highlighting("python programming", index_data)
        
        self.assertGreater(len(results), 0)
        
        # Results should be ranked by relevance
        # The first result should have the highest score
        if len(results) > 1:
            self.assertGreaterEqual(results[0]['score'], results[1]['score'])
        
        print(f"✅ Search ranking returned {len(results)} results with scores: {[r['score'] for r in results]}")

    def test_mixed_file_types_integration(self):
        """Test integration with mixed file types."""
        print("\n--- Testing Mixed File Types ---")
        
        # Create files with different extensions
        files = [
            ('document.txt', 'Text document with content about programming.'),
            ('notes.md', 'Markdown file with programming notes.'),
            ('config.ini', 'Configuration file with settings.'),
            ('data.csv', 'CSV file with data.'),
            ('script.py', 'Python script file.'),
            ('.hidden.txt', 'Hidden file that should be skipped.'),
            ('temp.tmp', 'Temporary file that should be skipped.')
        ]
        
        for filename, content in files:
            self.create_test_file(filename, content)
        
        # Build index
        index_data = build_index(self.test_dir)
        index_data = cast(Dict[str, Any], index_data)
        
        # Should only index supported files (txt files)
        # Should skip hidden and temp files
        expected_files = ['document.txt']
        actual_files = [os.path.basename(doc['filepath']) for doc in index_data['document_store'].values()]
        
        for expected_file in expected_files:
            self.assertIn(expected_file, actual_files)
        
        print(f"✅ Mixed file types: indexed {len(index_data['document_store'])} files")
        print(f"   Expected: {expected_files}")
        print(f"   Actual: {actual_files}")


if __name__ == '__main__':
    unittest.main(verbosity=2) 