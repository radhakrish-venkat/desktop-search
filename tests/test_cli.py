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
from cmd.cli import cli


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
        self.assertIn('desktop-search version 0.1.0', result.output)

    @patch('cmd.cli.build_index')
    def test_cli_index_basic(self, mock_build_index):
        """Test basic indexing command."""
        # Mock successful index building
        mock_index_data = {
            'document_store': {
                'doc1': {'filepath': '/test/doc1.txt', 'text': 'Test content'}
            },
            'inverted_index': {'test': {'doc1'}},
            'indexed_directory': self.test_dir,
            'stats': {'total_documents': 1}
        }
        mock_build_index.return_value = mock_index_data
        
        # Create a test file
        self.create_test_file('test.txt', 'Test content')
        
        # Run index command
        result = self.runner.invoke(cli, ['index', self.test_dir])
        
        # Verify success
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Starting indexing of directory', result.output)
        self.assertIn('Indexing complete', result.output)
        self.assertIn('Indexed 1 documents', result.output)
        
        # Verify build_index was called
        mock_build_index.assert_called_once_with(self.test_dir)

    @patch('cmd.cli.build_index')
    def test_cli_index_failure(self, mock_build_index):
        """Test indexing command with failure."""
        # Mock failed index building
        mock_build_index.return_value = None
        
        # Create a test file
        self.create_test_file('test.txt', 'Test content')
        
        # Run index command
        result = self.runner.invoke(cli, ['index', self.test_dir])
        
        # Verify failure
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('Error: Failed to build index', result.output)

    @patch('cmd.cli.build_index')
    @patch('cmd.cli.save_index')
    def test_cli_index_with_save(self, mock_save_index, mock_build_index):
        """Test indexing command with save option."""
        # Mock successful index building and saving
        mock_index_data = {
            'document_store': {'doc1': {'filepath': '/test/doc1.txt', 'text': 'Test'}},
            'inverted_index': {'test': {'doc1'}},
            'indexed_directory': self.test_dir,
            'stats': {'total_documents': 1}
        }
        mock_build_index.return_value = mock_index_data
        mock_save_index.return_value = True
        
        # Create a test file
        self.create_test_file('test.txt', 'Test content')
        
        # Run index command with save
        index_file = os.path.join(self.test_dir, 'test_index.pkl')
        result = self.runner.invoke(cli, ['index', self.test_dir, '--save', index_file])
        
        # Verify success
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Index saved to', result.output)
        
        # Verify save_index was called
        mock_save_index.assert_called_once_with(mock_index_data, index_file)

    @patch('cmd.cli.build_index')
    @patch('cmd.cli.save_index')
    def test_cli_index_save_failure(self, mock_save_index, mock_build_index):
        """Test indexing command with save failure."""
        # Mock successful index building but failed saving
        mock_index_data = {
            'document_store': {'doc1': {'filepath': '/test/doc1.txt', 'text': 'Test'}},
            'inverted_index': {'test': {'doc1'}},
            'indexed_directory': self.test_dir,
            'stats': {'total_documents': 1}
        }
        mock_build_index.return_value = mock_index_data
        mock_save_index.return_value = False
        
        # Create a test file
        self.create_test_file('test.txt', 'Test content')
        
        # Run index command with save
        index_file = os.path.join(self.test_dir, 'test_index.pkl')
        result = self.runner.invoke(cli, ['index', self.test_dir, '--save', index_file])
        
        # Should still succeed but with warning
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Warning: Failed to save index', result.output)

    @patch('cmd.cli.search_index')
    def test_cli_search_basic(self, mock_search_index):
        """Test basic search command."""
        # Mock search results
        mock_results = [
            {'filepath': '/test/doc1.txt', 'snippet': 'Test content with python'},
            {'filepath': '/test/doc2.txt', 'snippet': 'Another document about python'}
        ]
        mock_search_index.return_value = mock_results
        
        # Mock context with index data
        mock_context = MagicMock()
        mock_context.obj = {
            'document_store': {'doc1': {'filepath': '/test/doc1.txt', 'text': 'Test'}},
            'inverted_index': {'python': {'doc1'}}
        }
        
        with patch('click.get_current_context', return_value=mock_context):
            # Run search command
            result = self.runner.invoke(cli, ['search', 'python'])
            
            # Verify success
            self.assertEqual(result.exit_code, 0)
            self.assertIn('Searching for: \'python\'', result.output)
            self.assertIn('Search Results (2 found)', result.output)
            self.assertIn('doc1.txt', result.output)
            self.assertIn('doc2.txt', result.output)

    @patch('cmd.cli.load_index')
    def test_cli_search_with_load(self, mock_load_index):
        """Test search command with load option."""
        # Mock loaded index data
        mock_index_data = {
            'document_store': {'doc1': {'filepath': '/test/doc1.txt', 'text': 'Test'}},
            'inverted_index': {'python': {'doc1'}}
        }
        mock_load_index.return_value = mock_index_data
        
        # Mock search results
        with patch('cmd.cli.search_index', return_value=[{'filepath': '/test/doc1.txt', 'snippet': 'Test'}]):
            # Run search command with load
            index_file = os.path.join(self.test_dir, 'test_index.pkl')
            result = self.runner.invoke(cli, ['search', 'python', '--load', index_file])
            
            # Verify success
            self.assertEqual(result.exit_code, 0)
            self.assertIn('Searching for: \'python\'', result.output)
            
            # Verify load_index was called
            mock_load_index.assert_called_once_with(index_file)

    @patch('cmd.cli.load_index')
    def test_cli_search_load_failure(self, mock_load_index):
        """Test search command with load failure."""
        # Mock failed index loading
        mock_load_index.return_value = None
        
        # Run search command with load
        index_file = os.path.join(self.test_dir, 'test_index.pkl')
        result = self.runner.invoke(cli, ['search', 'python', '--load', index_file])
        
        # Verify failure
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('Error: Could not load index from', result.output)

    def test_cli_search_no_index(self):
        """Test search command without index."""
        # Run search command without any index
        result = self.runner.invoke(cli, ['search', 'python'])
        
        # Verify failure
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('Error: No index found', result.output)

    @patch('cmd.cli.search_index')
    def test_cli_search_no_results(self, mock_search_index):
        """Test search command with no results."""
        # Mock empty search results
        mock_search_index.return_value = []
        
        # Mock context with index data
        mock_context = MagicMock()
        mock_context.obj = {
            'document_store': {'doc1': {'filepath': '/test/doc1.txt', 'text': 'Test'}},
            'inverted_index': {'python': {'doc1'}}
        }
        
        with patch('click.get_current_context', return_value=mock_context):
            # Run search command
            result = self.runner.invoke(cli, ['search', 'nonexistent'])
            
            # Verify success but no results
            self.assertEqual(result.exit_code, 0)
            self.assertIn('No matching documents found', result.output)

    @patch('cmd.cli.search_index')
    def test_cli_search_with_limit(self, mock_search_index):
        """Test search command with result limit."""
        # Mock many search results
        mock_results = [
            {'filepath': f'/test/doc{i}.txt', 'snippet': f'Test content {i}'}
            for i in range(15)
        ]
        mock_search_index.return_value = mock_results
        
        # Mock context with index data
        mock_context = MagicMock()
        mock_context.obj = {
            'document_store': {'doc1': {'filepath': '/test/doc1.txt', 'text': 'Test'}},
            'inverted_index': {'python': {'doc1'}}
        }
        
        with patch('click.get_current_context', return_value=mock_context):
            # Run search command with limit
            result = self.runner.invoke(cli, ['search', 'python', '--limit', '5'])
            
            # Verify success with limited results
            self.assertEqual(result.exit_code, 0)
            self.assertIn('Search Results (15 found)', result.output)
            self.assertIn('... and 10 more results', result.output)

    def test_cli_invalid_directory(self):
        """Test indexing with invalid directory."""
        # Run index command with non-existent directory
        result = self.runner.invoke(cli, ['index', '/nonexistent/directory'])
        
        # Verify failure
        self.assertNotEqual(result.exit_code, 0)

    def test_cli_invalid_file_path(self):
        """Test indexing with invalid file path."""
        # Run index command with file instead of directory
        test_file = self.create_test_file('test.txt', 'Test content')
        result = self.runner.invoke(cli, ['index', test_file])
        
        # Verify failure
        self.assertNotEqual(result.exit_code, 0)

    @patch('cmd.cli.build_index')
    def test_cli_index_exception_handling(self, mock_build_index):
        """Test indexing command exception handling."""
        # Mock exception during index building
        mock_build_index.side_effect = Exception("Test exception")
        
        # Create a test file
        self.create_test_file('test.txt', 'Test content')
        
        # Run index command
        result = self.runner.invoke(cli, ['index', self.test_dir])
        
        # Verify failure
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('Error during indexing', result.output)

    @patch('cmd.cli.search_index')
    def test_cli_search_exception_handling(self, mock_search_index):
        """Test search command exception handling."""
        # Mock exception during search
        mock_search_index.side_effect = Exception("Test exception")
        
        # Mock context with index data
        mock_context = MagicMock()
        mock_context.obj = {
            'document_store': {'doc1': {'filepath': '/test/doc1.txt', 'text': 'Test'}},
            'inverted_index': {'python': {'doc1'}}
        }
        
        with patch('click.get_current_context', return_value=mock_context):
            # Run search command
            result = self.runner.invoke(cli, ['search', 'python'])
            
            # Verify failure
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn('Error during search', result.output)

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
        
        # Mock the entire workflow
        with patch('cmd.cli.build_index') as mock_build, \
             patch('cmd.cli.search_index') as mock_search, \
             patch('cmd.cli.save_index') as mock_save, \
             patch('cmd.cli.load_index') as mock_load:
            
            # Mock index building
            mock_index_data = {
                'document_store': {
                    'doc1': {'filepath': os.path.join(self.test_dir, 'python.txt'), 'text': 'Python is a programming language'},
                    'doc2': {'filepath': os.path.join(self.test_dir, 'java.txt'), 'text': 'Java is another programming language'},
                    'doc3': {'filepath': os.path.join(self.test_dir, 'javascript.txt'), 'text': 'JavaScript is used for web development'}
                },
                'inverted_index': {
                    'python': {'doc1'},
                    'java': {'doc2'},
                    'javascript': {'doc3'},
                    'programming': {'doc1', 'doc2'},
                    'language': {'doc1', 'doc2'},
                    'web': {'doc3'},
                    'development': {'doc3'}
                },
                'indexed_directory': self.test_dir,
                'stats': {'total_documents': 3}
            }
            mock_build.return_value = mock_index_data
            mock_save.return_value = True
            mock_load.return_value = mock_index_data
            
            # Mock search results
            mock_search.return_value = [
                {'filepath': os.path.join(self.test_dir, 'python.txt'), 'snippet': 'Python is a programming language'}
            ]
            
            # Test index command
            index_file = os.path.join(self.test_dir, 'test_index.pkl')
            result = self.runner.invoke(cli, ['index', self.test_dir, '--save', index_file])
            self.assertEqual(result.exit_code, 0)
            
            # Test search command with load
            result = self.runner.invoke(cli, ['search', 'python', '--load', index_file])
            self.assertEqual(result.exit_code, 0)
            
            # Verify all mocks were called
            mock_build.assert_called_once()
            mock_save.assert_called_once()
            mock_load.assert_called_once()
            mock_search.assert_called_once()


if __name__ == '__main__':
    unittest.main() 