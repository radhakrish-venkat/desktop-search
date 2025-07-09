#!/usr/bin/env python3
"""Unit tests for searcher module."""

import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the module to test
from pkg.searcher.core import _tokenize_text


class TestSearcher(unittest.TestCase):
    """Test cases for searcher module."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create a sample index for testing
        self.sample_index = {
            'inverted_index': {
                'python': {'doc1', 'doc3'},
                'programming': {'doc1', 'doc2', 'doc3'},
                'java': {'doc2'},
                'javascript': {'doc3'},
                'language': {'doc1', 'doc2', 'doc3'},
                'web': {'doc3'},
                'development': {'doc3'},
                'object': {'doc2'},
                'oriented': {'doc2'}
            },
            'document_store': {
                'doc1': {
                    'filepath': '/path/to/python.txt',
                    'text': 'Python is a programming language. Python is great for beginners.',
                    'extension': '.txt'
                },
                'doc2': {
                    'filepath': '/path/to/java.txt',
                    'text': 'Java is an object-oriented programming language. Java is widely used.',
                    'extension': '.txt'
                },
                'doc3': {
                    'filepath': '/path/to/javascript.txt',
                    'text': 'JavaScript is a programming language used for web development.',
                    'extension': '.txt'
                }
            }
        }

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_tokenize_text(self):
        """Test text tokenization functionality."""
        # Test basic tokenization (current implementation preserves case)
        text = "Hello world! This is a test."
        tokens = _tokenize_text(text)
        expected = ['hello', 'world', 'this', 'test']
        self.assertEqual(tokens, expected)
        
        # Test with stop words
        text = "The quick brown fox jumps over the lazy dog"
        tokens = _tokenize_text(text)
        expected = ['quick', 'brown', 'fox', 'jumps', 'lazy', 'dog']
        self.assertEqual(tokens, expected)
        
        # Test with numbers and special characters
        text = "Python 3.9 is great! Version 2.7 was good too."
        tokens = _tokenize_text(text)
        expected = ['Python', 'great', 'Version', 'good']
        self.assertEqual(tokens, expected)
        
        # Test empty text
        self.assertEqual(_tokenize_text(""), [])
        
        # Test with short tokens
        text = "a b c d e f g"
        tokens = _tokenize_text(text)
        self.assertEqual(tokens, [])

    def test_semantic_search_basic(self):
        """Test basic semantic search functionality."""
        # Create test files
        import tempfile
        test_dir = tempfile.mkdtemp()
        try:
            # Create test files
            files = [
                ('doc1.txt', 'Python is a programming language. Python is great for beginners.'),
                ('doc2.txt', 'Java is an object-oriented programming language. Java is widely used.'),
                ('doc3.txt', 'JavaScript is a programming language used for web development.')
            ]
            
            for filename, content in files:
                filepath = os.path.join(test_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Build semantic index
            from pkg.indexer.semantic import SemanticIndexer
            indexer = SemanticIndexer(persist_directory=os.path.join(test_dir, 'chroma_db'))
            stats = indexer.build_semantic_index(test_dir)
            
            # Test search
            results = indexer.semantic_search('programming', n_results=5)
            
            self.assertIsInstance(results, list)
            self.assertGreater(len(results), 0)
            
            # Verify result structure
            for result in results:
                self.assertIn('filepath', result)
                self.assertIn('snippet', result)
                self.assertIn('similarity', result)
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_semantic_search_no_results(self):
        """Test semantic search with no matching results."""
        # Create test files
        import tempfile
        test_dir = tempfile.mkdtemp()
        try:
            # Create test files
            files = [
                ('doc1.txt', 'Python is a programming language.'),
                ('doc2.txt', 'Java is another programming language.')
            ]
            
            for filename, content in files:
                filepath = os.path.join(test_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Build semantic index
            from pkg.indexer.semantic import SemanticIndexer
            indexer = SemanticIndexer(persist_directory=os.path.join(test_dir, 'chroma_db'))
            indexer.build_semantic_index(test_dir)
            
            # Test search for something that won't be found
            results = indexer.semantic_search('nonexistent', n_results=5)
            self.assertEqual(results, [])
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_semantic_search_ranking(self):
        """Test semantic search result ranking."""
        # Create test files
        import tempfile
        test_dir = tempfile.mkdtemp()
        try:
            # Create test files with different content
            files = [
                ('doc1.txt', 'Python programming language is great. Python is amazing.'),
                ('doc2.txt', 'Python programming language is good.'),
                ('doc3.txt', 'Java is another programming language.')
            ]
            
            for filename, content in files:
                filepath = os.path.join(test_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Build semantic index
            from pkg.indexer.semantic import SemanticIndexer
            indexer = SemanticIndexer(persist_directory=os.path.join(test_dir, 'chroma_db'))
            indexer.build_semantic_index(test_dir)
            
            # Test search
            results = indexer.semantic_search('python programming', n_results=5)
            
            # Should have results
            self.assertGreater(len(results), 0)
            
            # Results should be ranked by similarity
            if len(results) > 1:
                self.assertGreaterEqual(results[0]['similarity'], results[1]['similarity'])
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_semantic_search_max_results(self):
        """Test semantic search result limiting."""
        # Create test files
        import tempfile
        test_dir = tempfile.mkdtemp()
        try:
            # Create multiple test files
            for i in range(10):
                filepath = os.path.join(test_dir, f'doc{i}.txt')
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f'Test document {i} contains some content.')
            
            # Build semantic index
            from pkg.indexer.semantic import SemanticIndexer
            indexer = SemanticIndexer(persist_directory=os.path.join(test_dir, 'chroma_db'))
            indexer.build_semantic_index(test_dir)
            
            # Test with custom limit
            results = indexer.semantic_search('test', n_results=3)
            self.assertLessEqual(len(results), 3)
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_semantic_search_edge_cases(self):
        """Test semantic search with edge cases."""
        # Create test files
        import tempfile
        test_dir = tempfile.mkdtemp()
        try:
            # Create test files
            files = [
                ('doc1.txt', 'Python is a programming language.'),
                ('doc2.txt', 'Java is another programming language.')
            ]
            
            for filename, content in files:
                filepath = os.path.join(test_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Build semantic index
            from pkg.indexer.semantic import SemanticIndexer
            indexer = SemanticIndexer(persist_directory=os.path.join(test_dir, 'chroma_db'))
            indexer.build_semantic_index(test_dir)
            
            # Test empty query
            results = indexer.semantic_search('', n_results=5)
            self.assertEqual(results, [])
            
            # Test query with only whitespace
            results = indexer.semantic_search('   ', n_results=5)
            self.assertEqual(results, [])
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_searcher_integration(self):
        """Integration test for the entire search process."""
        # Create test files
        import tempfile
        test_dir = tempfile.mkdtemp()
        try:
            # Create test files
            files = [
                ('doc1.txt', 'Python is a programming language. Python is great for beginners.'),
                ('doc2.txt', 'Java is an object-oriented programming language. Java is widely used.'),
                ('doc3.txt', 'JavaScript is a programming language used for web development.')
            ]
            
            for filename, content in files:
                filepath = os.path.join(test_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Build semantic index
            from pkg.indexer.semantic import SemanticIndexer
            indexer = SemanticIndexer(persist_directory=os.path.join(test_dir, 'chroma_db'))
            indexer.build_semantic_index(test_dir)
            
            # Test complete search workflow
            queries = [
                "python",
                "programming language",
                "java javascript",
                "web development",
                "nonexistent term"
            ]
            
            for query in queries:
                results = indexer.semantic_search(query, n_results=5)
                self.assertIsInstance(results, list)
                
                # Verify result structure
                for result in results:
                    self.assertIn('filepath', result)
                    self.assertIn('snippet', result)
                    self.assertIn('similarity', result)
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main() 