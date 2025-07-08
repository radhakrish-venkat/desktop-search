#!/usr/bin/env python3
"""Unit tests for the semantic indexer module."""

import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from pkg.indexer.semantic import SemanticIndexer, build_semantic_index, semantic_search, hybrid_search


class TestSemanticIndexer(unittest.TestCase):
    """Test cases for the SemanticIndexer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.chroma_dir = tempfile.mkdtemp()
        self.test_files = []

    def tearDown(self):
        """Clean up test fixtures."""
        for filepath in self.test_files:
            if os.path.exists(filepath):
                os.remove(filepath)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree(self.chroma_dir, ignore_errors=True)

    def create_test_file(self, filename: str, content: str) -> str:
        """Helper to create a test file."""
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        self.test_files.append(filepath)
        return filepath

    @patch('pkg.indexer.semantic.SentenceTransformer')
    @patch('pkg.indexer.semantic.chromadb')
    def test_semantic_indexer_initialization(self, mock_chromadb, mock_sentence_transformer):
        """Test SemanticIndexer initialization."""
        # Mock ChromaDB components
        mock_client = Mock()
        mock_collection = Mock()
        mock_chromadb.PersistentClient.return_value = mock_client
        mock_client.get_or_create_collection.return_value = mock_collection
        # Mock collection.get() to return empty results
        mock_collection.get.return_value = {'ids': []}
        
        # Mock sentence transformer
        mock_model = Mock()
        mock_sentence_transformer.return_value = mock_model
        
        # Test initialization
        indexer = SemanticIndexer(persist_directory=self.chroma_dir, model_name="test-model")
        
        # Verify ChromaDB client was created (check path only)
        called_args, called_kwargs = mock_chromadb.PersistentClient.call_args
        self.assertEqual(called_kwargs['path'], self.chroma_dir)
        
        # Verify collection was created
        mock_client.get_or_create_collection.assert_called_once_with(
            name="desktop_search",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Verify sentence transformer was loaded
        mock_sentence_transformer.assert_called_once_with("test-model")
        
        # Verify attributes
        self.assertEqual(indexer.persist_directory, self.chroma_dir)
        self.assertEqual(indexer.model_name, "test-model")
        self.assertEqual(indexer.collection, mock_collection)
        self.assertEqual(indexer.model, mock_model)

    def test_should_skip_file(self):
        """Test file skipping logic."""
        indexer = SemanticIndexer(persist_directory=self.chroma_dir)
        
        # Test files that should be skipped
        skip_files = [
            ".git/config",
            "node_modules/package.json",
            ".DS_Store",
            "file.pyc",
            "temp.log",
            "cache/.tmp",
            "__pycache__/module.pyc",
            ".vscode/settings.json",
            ".idea/workspace.xml"
        ]
        
        for filepath in skip_files:
            self.assertTrue(indexer._should_skip_file(filepath), f"Should skip: {filepath}")
        
        # Test files that should not be skipped
        keep_files = [
            "document.txt",
            "file.pdf",
            "data.docx",
            "spreadsheet.xlsx",
            "presentation.pptx"
        ]
        
        for filepath in keep_files:
            self.assertFalse(indexer._should_skip_file(filepath), f"Should keep: {filepath}")

    def test_chunk_text(self):
        """Test text chunking functionality."""
        indexer = SemanticIndexer(persist_directory=self.chroma_dir)
        
        # Test short text (should not be chunked)
        short_text = "This is a short text."
        chunks = indexer._chunk_text(short_text, chunk_size=100)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], short_text)
        
        # Test long text (should be chunked)
        long_text = "This is a very long text. " * 50  # Much longer than chunk size
        chunks = indexer._chunk_text(long_text, chunk_size=100, overlap=20)
        
        self.assertGreater(len(chunks), 1)
        
        # Verify chunks don't exceed size limit
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 100)
        
        # Verify overlap (except for first chunk)
        for i in range(1, len(chunks)):
            # Check if there's some overlap between consecutive chunks
            prev_chunk_end = chunks[i-1][-20:]  # Last 20 chars of previous chunk
            curr_chunk_start = chunks[i][:20]   # First 20 chars of current chunk
            # There should be some common text due to overlap
            self.assertTrue(len(set(prev_chunk_end) & set(curr_chunk_start)) > 0)

    def test_extract_metadata(self):
        """Test metadata extraction."""
        indexer = SemanticIndexer(persist_directory=self.chroma_dir)
        
        # Create a test file
        test_file = self.create_test_file("test.txt", "content")
        
        metadata = indexer._extract_metadata(test_file, 0, 3)
        
        expected_keys = ["filepath", "filename", "extension", "chunk_index", "total_chunks", "file_size"]
        for key in expected_keys:
            self.assertIn(key, metadata)
        
        self.assertEqual(metadata["filepath"], test_file)
        self.assertEqual(metadata["filename"], "test.txt")
        self.assertEqual(metadata["extension"], ".txt")
        self.assertEqual(metadata["chunk_index"], 0)
        self.assertEqual(metadata["total_chunks"], 3)
        self.assertGreater(metadata["file_size"], 0)

    @patch('pkg.indexer.semantic.get_text_from_file')
    @patch('pkg.indexer.semantic.SentenceTransformer')
    @patch('pkg.indexer.semantic.chromadb')
    def test_build_semantic_index(self, mock_chromadb, mock_sentence_transformer, mock_get_text):
        """Test semantic index building."""
        # Mock ChromaDB components
        mock_client = Mock()
        mock_collection = Mock()
        mock_chromadb.PersistentClient.return_value = mock_client
        mock_client.get_or_create_collection.return_value = mock_collection
        # Mock collection.get() to return empty results
        mock_collection.get.return_value = {'ids': []}
        
        # Mock sentence transformer
        mock_model = Mock()
        mock_sentence_transformer.return_value = mock_model
        
        # Create test files
        self.create_test_file("doc1.txt", "Content about artificial intelligence")
        self.create_test_file("doc2.txt", "Content about machine learning")
        
        # Mock text extraction
        mock_get_text.side_effect = [
            ("Content about artificial intelligence", ".txt"),
            ("Content about machine learning", ".txt")
        ]
        
        # Test index building
        indexer = SemanticIndexer(persist_directory=self.chroma_dir)
        stats = indexer.build_semantic_index(self.test_dir)
        
        # Verify results
        self.assertIsNotNone(stats)
        self.assertIn('indexed_directory', stats)
        self.assertIn('stats', stats)
        self.assertEqual(stats['indexed_directory'], self.test_dir)
        self.assertEqual(stats['stats']['total_files'], 2)
        self.assertGreater(stats['stats']['total_chunks'], 0)
        
        # Verify collection was cleared and documents were added
        mock_collection.delete.assert_not_called()  # Should not be called since ids is empty
        self.assertGreater(mock_collection.add.call_count, 0)

    @patch('pkg.indexer.semantic.SentenceTransformer')
    @patch('pkg.indexer.semantic.chromadb')
    def test_semantic_search(self, mock_chromadb, mock_sentence_transformer):
        """Test semantic search functionality."""
        # Mock ChromaDB components
        mock_client = Mock()
        mock_collection = Mock()
        mock_chromadb.PersistentClient.return_value = mock_client
        mock_client.get_or_create_collection.return_value = mock_collection
        
        # Mock sentence transformer
        mock_model = Mock()
        mock_sentence_transformer.return_value = mock_model
        
        # Mock search results
        mock_collection.query.return_value = {
            'documents': [['Document content about AI', 'Another document about ML']],
            'metadatas': [[
                {'filepath': '/path/doc1.txt', 'filename': 'doc1.txt', 'extension': '.txt', 'chunk_index': 0, 'total_chunks': 1, 'file_size': 100},
                {'filepath': '/path/doc2.txt', 'filename': 'doc2.txt', 'extension': '.txt', 'chunk_index': 0, 'total_chunks': 1, 'file_size': 100}
            ]],
            'distances': [[0.1, 0.3]]  # Low distance = high similarity
        }
        
        # Test semantic search
        indexer = SemanticIndexer(persist_directory=self.chroma_dir)
        results = indexer.semantic_search("artificial intelligence", n_results=5, threshold=0.2)
        
        # Verify results
        self.assertEqual(len(results), 2)
        self.assertGreater(results[0]['similarity'], results[1]['similarity'])  # Should be sorted by similarity
        
        # Verify result structure
        for result in results:
            self.assertIn('filepath', result)
            self.assertIn('filename', result)
            self.assertIn('snippet', result)
            self.assertIn('similarity', result)
            self.assertGreaterEqual(result['similarity'], 0.2)  # Above threshold

    @patch('pkg.indexer.semantic.SentenceTransformer')
    @patch('pkg.indexer.semantic.chromadb')
    def test_hybrid_search(self, mock_chromadb, mock_sentence_transformer):
        """Test hybrid search functionality."""
        # Mock ChromaDB components
        mock_client = Mock()
        mock_collection = Mock()
        mock_chromadb.PersistentClient.return_value = mock_client
        mock_client.get_or_create_collection.return_value = mock_collection
        
        # Mock sentence transformer
        mock_model = Mock()
        mock_sentence_transformer.return_value = mock_model
        
        # Mock search results for semantic search
        mock_collection.query.return_value = {
            'documents': [['Document about artificial intelligence and machine learning']],
            'metadatas': [[
                {'filepath': '/path/doc1.txt', 'filename': 'doc1.txt', 'extension': '.txt', 'chunk_index': 0, 'total_chunks': 1, 'file_size': 100}
            ]],
            'distances': [[0.2]]
        }
        
        # Test hybrid search
        indexer = SemanticIndexer(persist_directory=self.chroma_dir)
        results = indexer.hybrid_search("artificial intelligence", n_results=5)
        
        # Verify results
        self.assertEqual(len(results), 1)
        
        # Verify result structure
        result = results[0]
        self.assertIn('filepath', result)
        self.assertIn('snippet', result)
        self.assertIn('similarity', result)
        self.assertIn('keyword_score', result)
        self.assertIn('combined_score', result)
        
        # Verify scores are reasonable
        self.assertGreaterEqual(result['similarity'], 0)
        self.assertLessEqual(result['similarity'], 1)
        self.assertGreaterEqual(result['keyword_score'], 0)
        self.assertLessEqual(result['keyword_score'], 1)
        self.assertGreaterEqual(result['combined_score'], 0)
        self.assertLessEqual(result['combined_score'], 1)

    @patch('pkg.indexer.semantic.SentenceTransformer')
    @patch('pkg.indexer.semantic.chromadb')
    def test_get_collection_stats(self, mock_chromadb, mock_sentence_transformer):
        """Test collection statistics retrieval."""
        # Mock ChromaDB components
        mock_client = Mock()
        mock_collection = Mock()
        mock_chromadb.PersistentClient.return_value = mock_client
        mock_client.get_or_create_collection.return_value = mock_collection
        
        # Mock sentence transformer
        mock_model = Mock()
        mock_sentence_transformer.return_value = mock_model
        
        # Mock collection count
        mock_collection.count.return_value = 150
        
        # Test stats retrieval
        indexer = SemanticIndexer(persist_directory=self.chroma_dir)
        stats = indexer.get_collection_stats()
        
        # Verify results
        self.assertIn('total_chunks', stats)
        self.assertIn('model_name', stats)
        self.assertIn('persist_directory', stats)
        self.assertEqual(stats['total_chunks'], 150)
        self.assertEqual(stats['model_name'], 'all-MiniLM-L6-v2')
        self.assertEqual(stats['persist_directory'], self.chroma_dir)

    @patch('pkg.indexer.semantic.SentenceTransformer')
    @patch('pkg.indexer.semantic.chromadb')
    def test_delete_index(self, mock_chromadb, mock_sentence_transformer):
        """Test index deletion."""
        # Mock ChromaDB components
        mock_client = Mock()
        mock_collection = Mock()
        mock_chromadb.PersistentClient.return_value = mock_client
        mock_client.get_or_create_collection.return_value = mock_collection
        # Mock collection.get() to return some ids
        mock_collection.get.return_value = {'ids': ['id1', 'id2']}
        
        # Mock sentence transformer
        mock_model = Mock()
        mock_sentence_transformer.return_value = mock_model
        
        # Test index deletion
        indexer = SemanticIndexer(persist_directory=self.chroma_dir)
        success = indexer.delete_index()
        
        # Verify deletion was called with ids
        mock_collection.delete.assert_called_once_with(ids=['id1', 'id2'])
        self.assertTrue(success)


class TestSemanticIndexerConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.chroma_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree(self.chroma_dir, ignore_errors=True)

    @patch('pkg.indexer.semantic.SemanticIndexer')
    def test_build_semantic_index_function(self, mock_indexer_class):
        """Test build_semantic_index convenience function."""
        # Mock indexer instance
        mock_indexer = Mock()
        mock_indexer_class.return_value = mock_indexer
        
        # Mock build_semantic_index method
        mock_indexer.build_semantic_index.return_value = {'stats': {'total_files': 5}}
        
        # Test function
        result = build_semantic_index(self.test_dir, self.chroma_dir)
        
        # Verify indexer was created and method was called
        mock_indexer_class.assert_called_once_with(self.chroma_dir)
        mock_indexer.build_semantic_index.assert_called_once_with(self.test_dir)
        self.assertEqual(result, {'stats': {'total_files': 5}})

    @patch('pkg.indexer.semantic.SemanticIndexer')
    def test_semantic_search_function(self, mock_indexer_class):
        """Test semantic_search convenience function."""
        # Mock indexer instance
        mock_indexer = Mock()
        mock_indexer_class.return_value = mock_indexer
        
        # Mock semantic_search method
        mock_results = [{'filepath': '/test.txt', 'similarity': 0.8}]
        mock_indexer.semantic_search.return_value = mock_results
        
        # Test function
        result = semantic_search("test query", self.chroma_dir, n_results=5)
        
        # Verify indexer was created and method was called
        mock_indexer_class.assert_called_once_with(self.chroma_dir)
        mock_indexer.semantic_search.assert_called_once_with("test query", 5)
        self.assertEqual(result, mock_results)

    @patch('pkg.indexer.semantic.SemanticIndexer')
    def test_hybrid_search_function(self, mock_indexer_class):
        """Test hybrid_search convenience function."""
        # Mock indexer instance
        mock_indexer = Mock()
        mock_indexer_class.return_value = mock_indexer
        
        # Mock hybrid_search method
        mock_results = [{'filepath': '/test.txt', 'combined_score': 0.9}]
        mock_indexer.hybrid_search.return_value = mock_results
        
        # Test function
        result = hybrid_search("test query", self.chroma_dir, n_results=5)
        
        # Verify indexer was created and method was called
        mock_indexer_class.assert_called_once_with(self.chroma_dir)
        mock_indexer.hybrid_search.assert_called_once_with("test query", 5)
        self.assertEqual(result, mock_results)


if __name__ == '__main__':
    unittest.main(verbosity=2) 