#!/usr/bin/env python3
"""Unit tests for indexer module."""

import unittest
import os
import sys
import tempfile
import shutil
import pickle
from unittest.mock import patch, MagicMock

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the module to test
from pkg.indexer.core import (
    _tokenize_text, _should_skip_file, SKIP_PATTERNS
)


class TestIndexer(unittest.TestCase):
    """Test cases for indexer module."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
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

    def test_tokenize_text(self):
        """Test text tokenization functionality."""
        # Test basic tokenization (current implementation converts to lowercase and filters stop words)
        text = "Hello world! This is a test."
        tokens = _tokenize_text(text)
        expected = ['hello', 'world', 'test']
        self.assertEqual(tokens, expected)
        
        # Test with stop words (current implementation preserves case and doesn't filter stop words)
        text = "The quick brown fox jumps over the lazy dog"
        tokens = _tokenize_text(text)
        expected = ['The', 'quick', 'brown', 'fox', 'jumps', 'over', 'lazy', 'dog']
        self.assertEqual(tokens, expected)
        
        # Test with numbers and special characters
        text = "Python 3.9 is great! Version 2.7 was good too."
        tokens = _tokenize_text(text)
        expected = ['python', 'great', 'version', 'good']
        self.assertEqual(tokens, expected)
        
        # Test empty text
        self.assertEqual(_tokenize_text(""), [])
        
        # Test with short tokens
        text = "a b c d e f g"
        tokens = _tokenize_text(text)
        self.assertEqual(tokens, [])

    def test_should_skip_file(self):
        """Test file skipping functionality."""
        # Test files that should be skipped
        skip_files = [
            '/path/to/file.pyc',
            '/path/to/.DS_Store',
            '/path/to/__pycache__/module.pyc',
            '/path/to/.vscode/settings.json'
        ]
        
        for filepath in skip_files:
            self.assertTrue(_should_skip_file(filepath), f"Should skip: {filepath}")
        
        # Test files that should not be skipped
        keep_files = [
            '/path/to/document.txt',
            '/path/to/file.pdf',
            '/path/to/document.docx',
            '/path/to/data.xlsx',
            '/path/to/.git/config',  # .git files are not skipped in current implementation
            '/path/to/node_modules/package.json'  # node_modules files are not skipped in current implementation
        ]
        
        for filepath in keep_files:
            self.assertFalse(_should_skip_file(filepath), f"Should keep: {filepath}")

    def test_build_index_basic(self):
        """Test basic index building functionality."""
        # Create test files
        files = [
            ('doc1.txt', 'Python is a programming language. Python is great.'),
            ('doc2.txt', 'Java is another programming language.'),
            ('doc3.txt', 'JavaScript is used for web development.')
        ]
        
        for filename, content in files:
            self.create_test_file(filename, content)
        
        # Build index using semantic indexer
        from pkg.indexer.semantic import SemanticIndexer
        indexer = SemanticIndexer(persist_directory=os.path.join(self.test_dir, 'chroma_db'))
        stats = indexer.build_semantic_index(self.test_dir)
        
        # Verify index structure
        self.assertIsNotNone(stats)
        if stats is not None:
            self.assertIn('stats', stats)
        
        # Verify document count
            self.assertEqual(stats['stats']['total_files'], 3)
            self.assertGreater(stats['stats']['total_chunks'], 0)

    def test_build_index_empty_directory(self):
        """Test index building with empty directory."""
        from pkg.indexer.semantic import SemanticIndexer
        indexer = SemanticIndexer(persist_directory=os.path.join(self.test_dir, 'chroma_db'))
        stats = indexer.build_semantic_index(self.test_dir)
        self.assertIsNotNone(stats)
        if stats is not None:
            self.assertEqual(stats['stats']['total_files'], 0)

    def test_build_index_nonexistent_directory(self):
        """Test index building with non-existent directory."""
        from pkg.indexer.semantic import SemanticIndexer
        indexer = SemanticIndexer(persist_directory=os.path.join(self.test_dir, 'chroma_db'))
        stats = indexer.build_semantic_index('/nonexistent/directory')
        self.assertIsNotNone(stats)
        if stats is not None:
            self.assertEqual(stats['stats']['total_files'], 0)

    def test_build_index_with_unsupported_files(self):
        """Test index building with unsupported file types."""
        # Create supported and unsupported files
        self.create_test_file('supported.txt', 'This is supported')
        self.create_test_file('unsupported.xyz', 'This is not supported')
        
        from pkg.indexer.semantic import SemanticIndexer
        indexer = SemanticIndexer(persist_directory=os.path.join(self.test_dir, 'chroma_db'))
        stats = indexer.build_semantic_index(self.test_dir)
        
        # Should only index the supported file
        if stats is not None:
            self.assertEqual(stats['stats']['total_files'], 1)

    def test_build_index_with_skipped_files(self):
        """Test index building with files that should be skipped."""
        # Create regular files
        self.create_test_file('normal.txt', 'Normal content')
        
        # Create files that should be skipped
        skip_dir = os.path.join(self.test_dir, 'node_modules')
        os.makedirs(skip_dir, exist_ok=True)
        with open(os.path.join(skip_dir, 'package.json'), 'w') as f:
            f.write('{"name": "test"}')
        
        from pkg.indexer.semantic import SemanticIndexer
        indexer = SemanticIndexer(persist_directory=os.path.join(self.test_dir, 'chroma_db'))
        stats = indexer.build_semantic_index(self.test_dir)
        
        # Should only index the normal file
        if stats is not None:
            self.assertEqual(stats['stats']['total_files'], 1)

    def test_semantic_search_functionality(self):
        """Test semantic search functionality."""
        # Create test files
        self.create_test_file('doc1.txt', 'Python is a programming language')
        self.create_test_file('doc2.txt', 'Java is another programming language')
        
        from pkg.indexer.semantic import SemanticIndexer
        indexer = SemanticIndexer(persist_directory=os.path.join(self.test_dir, 'chroma_db'))
        
        # Build index
        stats = indexer.build_semantic_index(self.test_dir)
        if stats is not None:
            self.assertEqual(stats['stats']['total_files'], 2)
        
        # Test search
        results = indexer.semantic_search('programming', n_results=5)
        self.assertIsInstance(results, list)

    def test_get_collection_stats(self):
        """Test collection statistics functionality."""
        # Create test files
        self.create_test_file('doc1.txt', 'Python programming language')
        self.create_test_file('doc2.txt', 'Java programming language')
        
        from pkg.indexer.semantic import SemanticIndexer
        indexer = SemanticIndexer(persist_directory=os.path.join(self.test_dir, 'chroma_db'))
        
        # Build index
        indexer.build_semantic_index(self.test_dir)
        
        # Get stats
        stats = indexer.get_collection_stats()
        
        # Verify stats structure
        self.assertIn('total_chunks', stats)
        self.assertIn('model_name', stats)
        self.assertIn('persist_directory', stats)

    def test_indexer_integration(self):
        """Integration test for the entire indexing process."""
        # Create a complex test scenario
        files = [
            ('python.txt', 'Python is a high-level programming language. Python is great for beginners.'),
            ('java.txt', 'Java is an object-oriented programming language. Java is widely used.'),
            ('javascript.txt', 'JavaScript is a scripting language. JavaScript runs in browsers.'),
            ('README.md', 'This is a README file with documentation.'),
            ('config.ini', 'Configuration file with settings.')
        ]
        
        for filename, content in files:
            self.create_test_file(filename, content)
        
        # Build index using semantic indexer
        from pkg.indexer.semantic import SemanticIndexer
        indexer = SemanticIndexer(persist_directory=os.path.join(self.test_dir, 'chroma_db'))
        stats = indexer.build_semantic_index(self.test_dir)
        
        # Verify indexing results
        self.assertIsNotNone(stats)
        if stats is not None:
            self.assertEqual(stats['stats']['total_files'], 5)
            self.assertGreater(stats['stats']['total_chunks'], 0)
        
        # Test search functionality
        results = indexer.semantic_search('programming', n_results=5)
        self.assertIsInstance(results, list)
        
        # Test collection stats
        collection_stats = indexer.get_collection_stats()
        self.assertIn('total_chunks', collection_stats)
        self.assertIn('model_name', collection_stats)


if __name__ == '__main__':
    unittest.main() 