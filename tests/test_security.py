#!/usr/bin/env python3
"""Security tests for the desktop search application."""

import unittest
import os
import sys
import tempfile
import shutil
import json
import pickle
import logging
from unittest.mock import patch, MagicMock

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the modules to test
from pkg.indexer.core import save_index, load_index, _compute_index_integrity_hash, _validate_index_structure
from pkg.file_parsers.parsers import _validate_file_content, get_text_from_file
from pkg.utils.logging import setup_secure_logging, sanitize_path, log_file_operation, log_error_with_context


class TestSecurityFeatures(unittest.TestCase):
    """Test security features and protections."""

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

    def test_index_integrity_protection(self):
        """Test that index files have integrity protection."""
        # Create test index data
        index_data = {
            'inverted_index': {'test': {'doc1'}},
            'document_store': {'doc1': {'filepath': '/test/doc1.txt', 'text': 'test content'}},
            'indexed_directory': self.test_dir,
            'stats': {'total_files': 1, 'skipped_files': 0, 'unique_tokens': 1, 'total_documents': 1}
        }
        
        # Save index with integrity protection
        index_file = os.path.join(self.test_dir, 'test_index.pkl')
        self.assertTrue(save_index(index_data, index_file))
        
        # Verify integrity hash was added
        with open(index_file, 'rb') as f:
            saved_data = pickle.load(f)
        
        self.assertIn('_integrity_hash', saved_data)
        self.assertIsInstance(saved_data['_integrity_hash'], str)
        self.assertEqual(len(saved_data['_integrity_hash']), 64)  # SHA256 hash length
        
        # Load index and verify integrity
        loaded_data = load_index(index_file)
        self.assertIsNotNone(loaded_data)
        self.assertNotIn('_integrity_hash', loaded_data)  # Should be removed after verification

    def test_index_tampering_detection(self):
        """Test that tampered index files are detected."""
        # Create test index data
        index_data = {
            'inverted_index': {'test': {'doc1'}},
            'document_store': {'doc1': {'filepath': '/test/doc1.txt', 'text': 'test content'}},
            'indexed_directory': self.test_dir,
            'stats': {'total_files': 1, 'skipped_files': 0, 'unique_tokens': 1, 'total_documents': 1}
        }
        
        # Save index
        index_file = os.path.join(self.test_dir, 'test_index.pkl')
        self.assertTrue(save_index(index_data, index_file))
        
        # Tamper with the file by modifying content
        with open(index_file, 'rb') as f:
            tampered_data = pickle.load(f)
        
        # Modify the data
        tampered_data['document_store']['doc1']['text'] = 'tampered content'
        
        # Save tampered data
        with open(index_file, 'wb') as f:
            pickle.dump(tampered_data, f)
        
        # Try to load tampered index
        loaded_data = load_index(index_file)
        self.assertIsNone(loaded_data)  # Should fail integrity check

    def test_index_structure_validation(self):
        """Test that invalid index structures are rejected."""
        # Test missing required keys
        invalid_data = {
            'inverted_index': {'test': {'doc1'}},
            # Missing document_store, indexed_directory, stats
        }
        
        self.assertFalse(_validate_index_structure(invalid_data))
        
        # Test wrong data types
        invalid_data = {
            'inverted_index': 'not a dict',
            'document_store': {'doc1': {'filepath': '/test/doc1.txt', 'text': 'test content'}},
            'indexed_directory': self.test_dir,
            'stats': {'total_files': 1}
        }
        
        self.assertFalse(_validate_index_structure(invalid_data))

    def test_content_validation(self):
        """Test that suspicious content is detected and rejected."""
        # Test suspicious patterns
        suspicious_content = """
        <script>alert('xss')</script>
        <a href="javascript:alert('xss')">Click me</a>
        <iframe src="data:text/html,<script>alert('xss')</script>"></iframe>
        """
        
        self.assertFalse(_validate_file_content('/test/suspicious.html', suspicious_content))
        
        # Test safe content
        safe_content = """
        This is a normal document with no suspicious content.
        It contains regular text and formatting.
        """
        
        self.assertTrue(_validate_file_content('/test/safe.txt', safe_content))

    def test_file_processing_security(self):
        """Test that file processing includes security validation."""
        # Create a file with suspicious content
        suspicious_file = self.create_test_file('suspicious.txt', 
            '<script>alert("xss")</script>')
        
        # Process the file
        content, ext = get_text_from_file(suspicious_file)
        
        # Content should be rejected due to validation (returns empty string, not None)
        self.assertEqual(content, "")
        self.assertEqual(ext, '.txt')

    def test_secure_logging_sanitization(self):
        """Test that secure logging sanitizes sensitive information."""
        # Set up secure logging
        logger = setup_secure_logging('test_security', logging.INFO)
        
        # Test path sanitization
        home = os.path.expanduser('~')
        sensitive_path = os.path.join(home, 'secret', 'password.txt')
        sanitized = sanitize_path(sensitive_path)
        
        self.assertIn('~', sanitized)
        self.assertIn('[REDACTED]', sanitized)
        self.assertNotIn('secret', sanitized)
        self.assertNotIn('password', sanitized)

    def test_log_file_operation_sanitization(self):
        """Test that file operations are logged with sanitized paths."""
        # Set up secure logging
        logger = setup_secure_logging('test_file_ops', logging.INFO)
        
        # Test file operation logging
        home = os.path.expanduser('~')
        sensitive_file = os.path.join(home, 'secret', 'token.json')
        
        # Capture log output
        with self.assertLogs('test_file_ops', level='INFO') as log:
            log_file_operation('reading', sensitive_file, logger)
        
        # Check that sensitive information is redacted
        log_message = log.records[0].message
        self.assertIn('[REDACTED]', log_message)
        self.assertNotIn('secret', log_message)
        self.assertNotIn('token', log_message)

    def test_error_logging_sanitization(self):
        """Test that error logging doesn't expose sensitive information."""
        # Set up secure logging
        logger = setup_secure_logging('test_errors', logging.INFO)
        
        # Test error logging
        home = os.path.expanduser('~')
        sensitive_path = os.path.join(home, 'secret', 'password.txt')
        
        with self.assertLogs('test_errors', level='ERROR') as log:
            log_error_with_context(
                Exception("Test error"), 
                f"processing file {sensitive_path}", 
                logger
            )
        
        # Check that sensitive information is redacted
        log_message = log.records[0].message
        self.assertIn('[REDACTED]', log_message)
        self.assertNotIn('secret', log_message)
        self.assertNotIn('password', log_message)

    def test_integrity_hash_consistency(self):
        """Test that integrity hashes are consistent for same data."""
        index_data = {
            'inverted_index': {'test': {'doc1'}},
            'document_store': {'doc1': {'filepath': '/test/doc1.txt', 'text': 'test content'}},
            'indexed_directory': self.test_dir,
            'stats': {'total_files': 1, 'skipped_files': 0, 'unique_tokens': 1, 'total_documents': 1}
        }
        
        # Compute hash multiple times
        hash1 = _compute_index_integrity_hash(index_data)
        hash2 = _compute_index_integrity_hash(index_data)
        
        # Hashes should be identical
        self.assertEqual(hash1, hash2)
        
        # Hash should be different for different data
        index_data2 = index_data.copy()
        index_data2['stats']['total_files'] = 2
        hash3 = _compute_index_integrity_hash(index_data2)
        
        self.assertNotEqual(hash1, hash3)

    def test_legacy_index_loading(self):
        """Test that legacy index files without integrity hashes can still be loaded."""
        # Create legacy index data (without integrity hash)
        legacy_data = {
            'inverted_index': {'test': {'doc1'}},
            'document_store': {'doc1': {'filepath': '/test/doc1.txt', 'text': 'test content'}},
            'indexed_directory': self.test_dir,
            'stats': {'total_files': 1, 'skipped_files': 0, 'unique_tokens': 1, 'total_documents': 1}
        }
        
        # Save without integrity protection (simulating legacy file)
        index_file = os.path.join(self.test_dir, 'legacy_index.pkl')
        with open(index_file, 'wb') as f:
            pickle.dump(legacy_data, f)
        
        # Should be able to load legacy file (with warning)
        loaded_data = load_index(index_file)
        self.assertIsNotNone(loaded_data)
        self.assertEqual(loaded_data['stats']['total_files'], 1)


if __name__ == '__main__':
    unittest.main() 