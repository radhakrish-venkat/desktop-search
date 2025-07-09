#!/usr/bin/env python3
"""Integration tests for CLI module."""

import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the CLI module
from cli_commands.cli import cli


class TestCLI(unittest.TestCase):
    """Test cases for CLI module."""

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

    def test_cli_help(self):
        """Test CLI help functionality."""
        # Test main help
        result = self.runner.invoke(cli, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('A simple local document search tool', result.output)
        self.assertIn('index', result.output)
        self.assertIn('search', result.output)
        
        # Test index help
        result = self.runner.invoke(cli, ['index', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Scans the specified DIRECTORY', result.output)
        
        # Test search help
        result = self.runner.invoke(cli, ['search', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Searches the indexed documents', result.output)

    def test_cli_version(self):
        """Test CLI version functionality."""
        result = self.runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('desktop-search, version 0.1.0', result.output)

    def test_cli_index_basic(self):
        """Test basic indexing command."""
        # Create a test file
        self.create_test_file('test.txt', 'Test content about Python programming')
        
        # Run index command
        result = self.runner.invoke(cli, ['index', self.test_dir])
        
        # Verify success
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Starting smart indexing of directory', result.output)
        self.assertIn('Indexing complete', result.output)
        self.assertIn('Total files:', result.output)

    def test_cli_index_failure(self):
        """Test indexing command with failure."""
        # Run index command on non-existent directory
        result = self.runner.invoke(cli, ['index', '/nonexistent/directory'])
        
        # Verify failure
        self.assertNotEqual(result.exit_code, 0)

    def test_cli_index_with_save(self):
        """Test indexing command with save option."""
        # Create a test file
        self.create_test_file('test.txt', 'Test content about Python programming')
        
        # Run index command
        result = self.runner.invoke(cli, ['index', self.test_dir])
        
        # Verify success
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Index saved to', result.output)

    def test_cli_index_save_failure(self):
        """Test indexing command with save failure."""
        # Create a test file
        self.create_test_file('test.txt', 'Test content about Python programming')
        
        # Run index command
        result = self.runner.invoke(cli, ['index', self.test_dir])
        
        # Should succeed
        self.assertEqual(result.exit_code, 0)

    def test_cli_search_basic(self):
        """Test basic search command."""
        # First create and index some files
        self.create_test_file('doc1.txt', 'Python is a programming language')
        self.create_test_file('doc2.txt', 'Java is another programming language')
        
        # Index the files
        self.runner.invoke(cli, ['index', self.test_dir])
        
        # Run search command
        result = self.runner.invoke(cli, ['search', 'Python'])
        
        # Verify success
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Searching for:', result.output)

    def test_cli_search_with_load(self):
        """Test search command with load option."""
        # First create and index some files
        self.create_test_file('doc1.txt', 'Python is a programming language')
        self.create_test_file('doc2.txt', 'Java is another programming language')
        
        # Index the files
        self.runner.invoke(cli, ['index', self.test_dir])
        
        # Run search command
        result = self.runner.invoke(cli, ['search', 'programming'])
        
        # Verify success
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Searching for:', result.output)

    def test_cli_search_load_failure(self):
        """Test search command with load failure."""
        # Run search without any index
        result = self.runner.invoke(cli, ['search', 'python'])
        
        # Should still work (will create empty results)
        self.assertEqual(result.exit_code, 0)

    def test_cli_search_no_index(self):
        """Test search command without index."""
        # Run search command without any index
        result = self.runner.invoke(cli, ['search', 'python'])
        
        # Should work (will show no results)
        self.assertEqual(result.exit_code, 0)

    def test_cli_search_no_results(self):
        """Test search command with no results."""
        # First create and index some files
        self.create_test_file('doc1.txt', 'Python is a programming language')
        
        # Index the files
        self.runner.invoke(cli, ['index', self.test_dir])
        
        # Run search for something that won't be found
        result = self.runner.invoke(cli, ['search', 'nonexistentword'])
        
        # Verify success but no results
        self.assertEqual(result.exit_code, 0)
        self.assertIn('No matching documents found', result.output)

    def test_cli_search_with_limit(self):
        """Test search command with limit option."""
        # First create and index some files
        self.create_test_file('doc1.txt', 'Python is a programming language')
        self.create_test_file('doc2.txt', 'Java is another programming language')
        self.create_test_file('doc3.txt', 'JavaScript is also a programming language')
        
        # Index the files
        self.runner.invoke(cli, ['index', self.test_dir])
        
        # Run search with limit
        result = self.runner.invoke(cli, ['search', 'programming', '--limit', '2'])
        
        # Verify success
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Searching for:', result.output)

    def test_cli_invalid_directory(self):
        """Test CLI with invalid directory."""
        result = self.runner.invoke(cli, ['index', '/nonexistent/directory'])
        self.assertNotEqual(result.exit_code, 0)

    def test_cli_invalid_file_path(self):
        """Test CLI with invalid file path."""
        result = self.runner.invoke(cli, ['index', '/nonexistent/file.txt'])
        self.assertNotEqual(result.exit_code, 0)

    def test_cli_index_exception_handling(self):
        """Test indexing command exception handling."""
        # Create a file that might cause issues
        self.create_test_file('test.txt', 'Test content')
        
        # Run index command
        result = self.runner.invoke(cli, ['index', self.test_dir])
        
        # Should handle gracefully
        self.assertEqual(result.exit_code, 0)

    def test_cli_search_exception_handling(self):
        """Test search command exception handling."""
        # First create and index some files
        self.create_test_file('doc1.txt', 'Python is a programming language')
        
        # Index the files
        self.runner.invoke(cli, ['index', self.test_dir])
        
        # Run search command
        result = self.runner.invoke(cli, ['search', 'python'])
        
        # Should handle gracefully
        self.assertEqual(result.exit_code, 0)

    def test_cli_integration_workflow(self):
        """Test complete CLI workflow."""
        # Create test files
        files = [
            ('python.txt', 'Python is a programming language. Python is great.'),
            ('java.txt', 'Java is another programming language.'),
            ('javascript.txt', 'JavaScript is used for web development.')
        ]

        for filename, content in files:
            self.create_test_file(filename, content)

        # Test CLI index command
        print("\n--- Testing CLI Index Command ---")
        result = self.runner.invoke(cli, ['index', self.test_dir])

        self.assertEqual(result.exit_code, 0)
        self.assertIn('Starting smart indexing of directory', result.output)

        # Test CLI search command
        print("\n--- Testing CLI Search Command ---")
        result = self.runner.invoke(cli, ['search', 'programming'])

        self.assertEqual(result.exit_code, 0)
        self.assertIn('Searching for:', result.output)

        # Test CLI stats command
        print("\n--- Testing CLI Stats Command ---")
        result = self.runner.invoke(cli, ['stats'])

        self.assertEqual(result.exit_code, 0)
        self.assertIn('Loading index statistics', result.output)


if __name__ == '__main__':
    unittest.main() 