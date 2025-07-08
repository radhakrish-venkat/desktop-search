#!/usr/bin/env python3
"""Unit tests for indexer module."""

import unittest
import os
import tempfile
import shutil
import pickle
from unittest.mock import patch, MagicMock

# Import the module to test
from pkg.indexer.core import (
    build_index, save_index, load_index, get_index_stats,
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
        # Test basic tokenization
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
        expected = ['python', 'great', 'version', 'good']
        self.assertEqual(tokens, expected)
        
        # Test empty text
        self.assertEqual(_tokenize_text(""), [])
        self.assertEqual(_tokenize_text(None), [])
        
        # Test with short tokens
        text = "a b c d e f g"
        tokens = _tokenize_text(text)
        self.assertEqual(tokens, [])

    def test_should_skip_file(self):
        """Test file skipping functionality."""
        # Test files that should be skipped
        skip_files = [
            '/path/to/.git/config',
            '/path/to/node_modules/package.json',
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
            '/path/to/data.xlsx'
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
        
        # Build index
        index_data = build_index(self.test_dir)
        
        # Verify index structure
        self.assertIsNotNone(index_data)
        self.assertIn('inverted_index', index_data)
        self.assertIn('document_store', index_data)
        self.assertIn('indexed_directory', index_data)
        self.assertIn('stats', index_data)
        
        # Verify document count
        self.assertEqual(len(index_data['document_store']), 3)
        
        # Verify some expected tokens
        inverted_index = index_data['inverted_index']
        self.assertIn('python', inverted_index)
        self.assertIn('programming', inverted_index)
        self.assertIn('java', inverted_index)
        self.assertIn('javascript', inverted_index)

    def test_build_index_empty_directory(self):
        """Test index building with empty directory."""
        index_data = build_index(self.test_dir)
        self.assertIsNotNone(index_data)
        self.assertEqual(len(index_data['document_store']), 0)

    def test_build_index_nonexistent_directory(self):
        """Test index building with non-existent directory."""
        index_data = build_index('/nonexistent/directory')
        self.assertIsNone(index_data)

    def test_build_index_with_unsupported_files(self):
        """Test index building with unsupported file types."""
        # Create supported and unsupported files
        self.create_test_file('supported.txt', 'This is supported')
        self.create_test_file('unsupported.xyz', 'This is not supported')
        
        index_data = build_index(self.test_dir)
        
        # Should only index the supported file
        self.assertEqual(len(index_data['document_store']), 1)
        
        # Check that the supported file was indexed
        doc_store = index_data['document_store']
        for doc_info in doc_store.values():
            self.assertTrue(doc_info['filepath'].endswith('.txt'))

    def test_build_index_with_skipped_files(self):
        """Test index building with files that should be skipped."""
        # Create regular files
        self.create_test_file('normal.txt', 'Normal content')
        
        # Create files that should be skipped
        skip_dir = os.path.join(self.test_dir, '.git')
        os.makedirs(skip_dir, exist_ok=True)
        with open(os.path.join(skip_dir, 'config'), 'w') as f:
            f.write('git config')
        
        index_data = build_index(self.test_dir)
        
        # Should only index the normal file
        self.assertEqual(len(index_data['document_store']), 1)

    def test_save_and_load_index(self):
        """Test index saving and loading functionality."""
        # Create test files and build index
        self.create_test_file('test.txt', 'Test content')
        index_data = build_index(self.test_dir)
        
        # Save index
        index_file = os.path.join(self.test_dir, 'test_index.pkl')
        success = save_index(index_data, index_file)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(index_file))
        
        # Load index
        loaded_data = load_index(index_file)
        self.assertIsNotNone(loaded_data)
        
        # Verify loaded data matches original
        self.assertEqual(loaded_data['inverted_index'], index_data['inverted_index'])
        self.assertEqual(loaded_data['document_store'], index_data['document_store'])
        self.assertEqual(loaded_data['indexed_directory'], index_data['indexed_directory'])

    def test_save_index_error_handling(self):
        """Test index saving error handling."""
        # Test saving to non-existent directory
        index_data = {'test': 'data'}
        success = save_index(index_data, '/nonexistent/path/index.pkl')
        self.assertFalse(success)

    def test_load_index_error_handling(self):
        """Test index loading error handling."""
        # Test loading non-existent file
        loaded_data = load_index('/nonexistent/index.pkl')
        self.assertIsNone(loaded_data)
        
        # Test loading invalid pickle file
        invalid_file = os.path.join(self.test_dir, 'invalid.pkl')
        with open(invalid_file, 'w') as f:
            f.write('not a pickle file')
        
        loaded_data = load_index(invalid_file)
        self.assertIsNone(loaded_data)

    def test_get_index_stats(self):
        """Test index statistics functionality."""
        # Create test files and build index
        files = [
            ('doc1.txt', 'Python programming language'),
            ('doc2.txt', 'Java programming language'),
            ('doc3.txt', 'JavaScript programming language')
        ]
        
        for filename, content in files:
            self.create_test_file(filename, content)
        
        index_data = build_index(self.test_dir)
        stats = get_index_stats(index_data)
        
        # Verify stats structure
        self.assertIn('total_files', stats)
        self.assertIn('skipped_files', stats)
        self.assertIn('unique_tokens', stats)
        self.assertIn('total_documents', stats)
        self.assertIn('total_tokens', stats)
        self.assertIn('avg_tokens_per_doc', stats)
        self.assertIn('most_common_tokens', stats)
        
        # Verify some expected values
        self.assertEqual(stats['total_documents'], 3)
        self.assertGreater(stats['unique_tokens'], 0)
        self.assertGreater(stats['total_tokens'], 0)
        self.assertGreater(stats['avg_tokens_per_doc'], 0)
        self.assertIsInstance(stats['most_common_tokens'], list)

    def test_get_index_stats_empty_index(self):
        """Test statistics with empty index."""
        index_data = {
            'inverted_index': {},
            'document_store': {},
            'stats': {'total_files': 0, 'skipped_files': 0, 'unique_tokens': 0, 'total_documents': 0}
        }
        
        stats = get_index_stats(index_data)
        self.assertEqual(stats['total_documents'], 0)
        self.assertEqual(stats['total_tokens'], 0)
        self.assertEqual(stats['avg_tokens_per_doc'], 0)

    def test_get_index_stats_none(self):
        """Test statistics with None index."""
        stats = get_index_stats(None)
        self.assertEqual(stats, {})

    def test_indexer_integration(self):
        """Integration test for the entire indexing process."""
        # Create a complex test scenario
        files = [
            ('python.txt', 'Python is a high-level programming language. Python is great for beginners.'),
            ('java.txt', 'Java is an object-oriented programming language. Java is widely used.'),
            ('javascript.txt', 'JavaScript is a scripting language. JavaScript runs in browsers.'),
            ('README.md', 'This is a README file with documentation.'),
            ('config.ini', 'Configuration file with settings.'),
            ('.hidden.txt', 'This file should be hidden.'),
            ('temp.tmp', 'Temporary file content.')
        ]
        
        for filename, content in files:
            self.create_test_file(filename, content)
        
        # Build index
        index_data = build_index(self.test_dir)
        
        # Verify indexing results
        self.assertIsNotNone(index_data)
        doc_store = index_data['document_store']
        
        # Should index supported files but skip hidden/temp files
        expected_files = ['python.txt', 'java.txt', 'javascript.txt', 'README.md', 'config.ini']
        actual_files = [os.path.basename(doc['filepath']) for doc in doc_store.values()]
        
        for expected_file in expected_files:
            self.assertIn(expected_file, actual_files)
        
        # Verify some expected tokens
        inverted_index = index_data['inverted_index']
        self.assertIn('python', inverted_index)
        self.assertIn('java', inverted_index)
        self.assertIn('javascript', inverted_index)
        self.assertIn('programming', inverted_index)
        self.assertIn('language', inverted_index)
        
        # Test save and load
        index_file = os.path.join(self.test_dir, 'integration_test.pkl')
        self.assertTrue(save_index(index_data, index_file))
        
        loaded_data = load_index(index_file)
        self.assertIsNotNone(loaded_data)
        self.assertEqual(loaded_data['inverted_index'], index_data['inverted_index'])


if __name__ == '__main__':
    unittest.main() 