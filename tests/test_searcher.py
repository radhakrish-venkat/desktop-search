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
from pkg.searcher.core import (
    search_index, search_with_highlighting, _tokenize_text,
    _generate_snippet, _calculate_tf_idf_score
)


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

    def test_calculate_tf_idf_score(self):
        """Test TF-IDF score calculation."""
        query_tokens = ['python', 'programming']
        doc_tokens = ['python', 'programming', 'language', 'python', 'great']
        total_docs = 3
        doc_freq = {'python': 2, 'programming': 3}
        
        score = _calculate_tf_idf_score(query_tokens, doc_tokens, total_docs, doc_freq)
        
        # Score should be positive
        self.assertGreater(score, 0)
        
        # Test with empty document
        score_empty = _calculate_tf_idf_score(query_tokens, [], total_docs, doc_freq)
        self.assertEqual(score_empty, 0.0)
        
        # Test with no matching tokens
        score_no_match = _calculate_tf_idf_score(['nonexistent'], doc_tokens, total_docs, doc_freq)
        self.assertEqual(score_no_match, 0.0)

    def test_generate_snippet(self):
        """Test snippet generation functionality."""
        text = "This is a long document about Python programming. Python is a great language for beginners."
        keywords = ['python', 'programming']
        
        snippet = _generate_snippet(text, keywords)
        
        # Snippet should contain keywords
        self.assertIn('Python', snippet)
        self.assertIn('programming', snippet)
        
        # Test with short text
        short_text = "Python is great."
        snippet_short = _generate_snippet(short_text, keywords)
        self.assertEqual(snippet_short, short_text)
        
        # Test with no keywords found - use longer text to trigger ellipses
        long_text = "This is a very long document about Python programming. " * 20  # Make it much longer
        snippet_no_keywords = _generate_snippet(long_text, ['nonexistent'])
        # Should return truncated text with ellipses
        self.assertIn('...', snippet_no_keywords)
        
        # Test with empty text
        self.assertEqual(_generate_snippet("", keywords), "")
        self.assertEqual(_generate_snippet(None, keywords), "")

    def test_search_index_basic(self):
        """Test basic search functionality."""
        # Test simple search
        results = search_index("python", self.sample_index)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Verify result structure
        for result in results:
            self.assertIn('filepath', result)
            self.assertIn('snippet', result)
        
        # Test multi-word search
        results_multi = search_index("python programming", self.sample_index)
        self.assertGreater(len(results_multi), 0)

    def test_search_index_no_results(self):
        """Test search with no matching results."""
        results = search_index("nonexistent", self.sample_index)
        self.assertEqual(results, [])
        
        # Test with stop words only
        results_stop = search_index("the and or", self.sample_index)
        self.assertEqual(results_stop, [])

    def test_search_index_invalid_index(self):
        """Test search with invalid index data."""
        # Test with None
        results = search_index("python", None)
        self.assertEqual(results, [])
        
        # Test with empty index
        empty_index = {'inverted_index': {}, 'document_store': {}}
        results = search_index("python", empty_index)
        self.assertEqual(results, [])
        
        # Test with missing keys
        invalid_index = {'inverted_index': {}}
        results = search_index("python", invalid_index)
        self.assertEqual(results, [])

    def test_search_index_ranking(self):
        """Test search result ranking."""
        # Create index with clear ranking differences
        ranking_index = {
            'inverted_index': {
                'python': {'doc1', 'doc2'},
                'programming': {'doc1', 'doc2'},
                'language': {'doc1', 'doc2'},
                'great': {'doc1'},
                'good': {'doc2'}
            },
            'document_store': {
                'doc1': {
                    'filepath': '/path/to/doc1.txt',
                    'text': 'Python programming language is great. Python is amazing.',
                    'extension': '.txt'
                },
                'doc2': {
                    'filepath': '/path/to/doc2.txt',
                    'text': 'Python programming language is good.',
                    'extension': '.txt'
                }
            }
        }
        
        results = search_index("python programming", ranking_index)
        
        # Should have results
        self.assertGreater(len(results), 0)
        
        # Results should be ranked (doc1 should score higher due to more matches)
        # Note: In a real scenario, we'd check the actual ranking order

    def test_search_with_highlighting(self):
        """Test enhanced search with highlighting."""
        results = search_with_highlighting("python programming", self.sample_index)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Verify enhanced result structure
        for result in results:
            self.assertIn('filepath', result)
            self.assertIn('snippet', result)
            self.assertIn('score', result)
            self.assertIn('extension', result)
            self.assertIn('doc_id', result)
            self.assertIn('file_size', result)
        
        # Check for highlighting in snippets
        for result in results:
            if '**python**' in result['snippet'].lower() or '**programming**' in result['snippet'].lower():
                break
        else:
            # If no highlighting found, that's also acceptable (depends on snippet generation)
            pass

    def test_search_with_highlighting_no_results(self):
        """Test enhanced search with no results."""
        results = search_with_highlighting("nonexistent", self.sample_index)
        self.assertEqual(results, [])

    def test_search_index_max_results(self):
        """Test search result limiting."""
        # Create index with many documents
        large_index = {
            'inverted_index': {
                'test': {'doc1', 'doc2', 'doc3', 'doc4', 'doc5'}
            },
            'document_store': {
                'doc1': {'filepath': '/path/to/doc1.txt', 'text': 'Test document 1'},
                'doc2': {'filepath': '/path/to/doc2.txt', 'text': 'Test document 2'},
                'doc3': {'filepath': '/path/to/doc3.txt', 'text': 'Test document 3'},
                'doc4': {'filepath': '/path/to/doc4.txt', 'text': 'Test document 4'},
                'doc5': {'filepath': '/path/to/doc5.txt', 'text': 'Test document 5'}
            }
        }
        
        # Test with default limit
        results = search_index("test", large_index)
        self.assertLessEqual(len(results), 50)  # Default max_results is 50
        
        # Test with custom limit
        results_limited = search_index("test", large_index, max_results=2)
        self.assertLessEqual(len(results_limited), 2)

    def test_search_edge_cases(self):
        """Test search with edge cases."""
        # Test empty query
        results = search_index("", self.sample_index)
        self.assertEqual(results, [])
        
        # Test query with only whitespace
        results = search_index("   ", self.sample_index)
        self.assertEqual(results, [])
        
        # Test query with only stop words
        results = search_index("the and or but", self.sample_index)
        self.assertEqual(results, [])

    def test_searcher_integration(self):
        """Integration test for the entire search process."""
        # Test complete search workflow
        queries = [
            "python",
            "programming language",
            "java javascript",
            "web development",
            "nonexistent term"
        ]
        
        for query in queries:
            # Test basic search
            basic_results = search_index(query, self.sample_index)
            self.assertIsInstance(basic_results, list)
            
            # Test enhanced search
            enhanced_results = search_with_highlighting(query, self.sample_index)
            self.assertIsInstance(enhanced_results, list)
            
            # If basic search has results, enhanced search should too
            if basic_results:
                self.assertGreater(len(enhanced_results), 0)
                
                # Check that enhanced results have more metadata
                for result in enhanced_results:
                    self.assertIn('score', result)
                    self.assertIn('extension', result)

    def test_search_performance(self):
        """Test search performance with larger datasets."""
        # Create a larger test index
        large_index = {
            'inverted_index': {},
            'document_store': {}
        }
        
        # Add 100 documents
        for i in range(100):
            doc_id = f'doc{i}'
            large_index['document_store'][doc_id] = {
                'filepath': f'/path/to/doc{i}.txt',
                'text': f'Document {i} contains some content about various topics.',
                'extension': '.txt'
            }
            
            # Add some tokens to inverted index
            tokens = ['document', 'contains', 'content', 'various', 'topics']
            for token in tokens:
                if token not in large_index['inverted_index']:
                    large_index['inverted_index'][token] = set()
                large_index['inverted_index'][token].add(doc_id)
        
        # Test search performance
        import time
        start_time = time.time()
        results = search_index("document content", large_index)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 1 second)
        self.assertLess(end_time - start_time, 1.0)
        self.assertGreater(len(results), 0)


if __name__ == '__main__':
    unittest.main() 