import os
import re
import sys
import logging
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

# Import our file parsing utility
from pkg.file_parsers.parsers import get_text_from_file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File patterns to skip (same as in core.py)
SKIP_PATTERNS = [
    r'\.git/',
    r'node_modules/',
    r'\.DS_Store$',
    r'\.pyc$',
    r'\.log$',
    r'\.tmp$',
    r'\.cache/',
    r'__pycache__/',
    r'\.vscode/',
    r'\.idea/'
]

# Chunk size for document splitting (in characters)
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

class SemanticIndexer:
    """Semantic indexer using ChromaDB and sentence-transformers."""
    
    def __init__(self, persist_directory: str = "./chroma_db", model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the semantic indexer.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            model_name: Sentence transformer model name
        """
        self.persist_directory = persist_directory
        self.model_name = model_name
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="desktop_search",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Load sentence transformer model
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded sentence transformer model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer model: {e}")
            raise
    
    def _should_skip_file(self, filepath: str) -> bool:
        """Check if file should be skipped based on patterns."""
        for pattern in SKIP_PATTERNS:
            if re.search(pattern, filepath, re.IGNORECASE):
                return True
        return False
    
    def _chunk_text(self, text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks in characters
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # If this isn't the last chunk, try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 100 characters of the chunk
                search_start = max(start, end - 100)
                sentence_end = text.rfind('.', search_start, end)
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position, accounting for overlap
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _extract_metadata(self, filepath: str, chunk_index: int, total_chunks: int) -> Dict[str, Any]:
        """Extract metadata for a document chunk."""
        return {
            "filepath": filepath,
            "filename": os.path.basename(filepath),
            "extension": os.path.splitext(filepath)[1].lower(),
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "file_size": os.path.getsize(filepath) if os.path.exists(filepath) else 0
        }
    
    def build_semantic_index(self, directory_path: str, progress_callback=None) -> Optional[Dict[str, Any]]:
        """
        Build semantic index for the specified directory.
        Args:
            directory_path: Path to directory to index
            progress_callback: Optional function(processed_files, total_files, filepath)
        Returns:
            Dictionary with indexing statistics
        """
        if not os.path.isdir(directory_path):
            logger.error(f"Directory not found at {directory_path}")
            return None
        logger.info(f"Starting semantic indexing of directory: {directory_path}")
        # Clear existing collection by deleting all documents
        try:
            all_docs = self.collection.get()
            if all_docs and all_docs.get('ids'):
                self.collection.delete(ids=all_docs['ids'])
        except Exception as e:
            logger.info(f"Collection was empty or could not be cleared: {e}")
        processed_files = 0
        skipped_files = 0
        total_chunks = 0
        # Count total files to process
        all_files = []
        for root, dirs, files in os.walk(directory_path):
            dirs[:] = [d for d in dirs if not self._should_skip_file(os.path.join(root, d))]
            for filename in files:
                filepath = os.path.join(root, filename)
                if not self._should_skip_file(filepath):
                    all_files.append(filepath)
        total_files = len(all_files)
        for filepath in all_files:
            try:
                extracted_text, file_ext = get_text_from_file(filepath)
                if extracted_text and extracted_text.strip():
                    chunks = self._chunk_text(extracted_text)
                    if chunks:
                        documents = []
                        metadatas = []
                        ids = []
                        for i, chunk in enumerate(chunks):
                            chunk_id = f"{filepath}_{i}"
                            metadata = self._extract_metadata(filepath, i, len(chunks))
                            metadata['fulltext'] = chunk
                            documents.append(chunk)
                            metadatas.append(metadata)
                            ids.append(chunk_id)
                        self.collection.add(
                            documents=documents,
                            metadatas=metadatas,
                            ids=ids
                        )
                        total_chunks += len(chunks)
                        processed_files += 1
                else:
                    skipped_files += 1
            except Exception as e:
                logger.error(f"Error processing file {filepath}: {e}")
                skipped_files += 1
            if progress_callback:
                progress_callback(processed_files, total_files, filepath)
        return {
            'stats': {
                'total_files': total_files,
                'new_files': processed_files,
                'modified_files': 0,
                'deleted_files': 0,
                'skipped_files': skipped_files,
                'total_chunks': total_chunks,
                'indexing_type': 'semantic'
            }
        }
    
    def semantic_search(self, query: str, n_results: int = 10, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Perform semantic search on the indexed documents.
        
        Args:
            query: Search query
            n_results: Number of results to return
            threshold: Similarity threshold (0-1)
            
        Returns:
            List of search results with metadata
        """
        try:
            # Query the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Process results
            search_results = []
            
            documents = results.get('documents', [])
            if results and documents and documents[0]:
                metadatas = results.get('metadatas', [[]]) or [[]]
                distances = results.get('distances', [[]]) or [[]]
                for i, (doc, metadata, distance) in enumerate(zip(
                    documents[0],  # type: ignore
                    metadatas[0],  # type: ignore
                    distances[0]  # type: ignore
                )):
                    # Convert distance to similarity score (ChromaDB uses cosine distance)
                    similarity = 1 - distance
                    
                    if similarity >= threshold:
                        search_results.append({
                            'filepath': metadata['filepath'],
                            'filename': metadata['filename'],
                            'extension': metadata['extension'],
                            'chunk_index': metadata['chunk_index'],
                            'total_chunks': metadata['total_chunks'],
                            'snippet': doc,
                            'similarity': similarity,
                            'file_size': metadata['file_size']
                        })
            
            # Sort by similarity score
            search_results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            return []
    
    def hybrid_search(self, query: str, n_results: int = 10, semantic_weight: float = 0.7) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic and keyword matching.
        
        Args:
            query: Search query
            n_results: Number of results to return
            semantic_weight: Weight for semantic similarity (0-1)
            
        Returns:
            List of search results with combined scores
        """
        # Get semantic results
        semantic_results = self.semantic_search(query, n_results * 2, threshold=0.1)
        
        # Simple keyword matching (you could enhance this with TF-IDF)
        query_terms = query.lower().split()
        keyword_results = []
        
        for result in semantic_results:
            text_lower = result['snippet'].lower()
            keyword_matches = sum(1 for term in query_terms if term in text_lower)
            keyword_score = keyword_matches / len(query_terms) if query_terms else 0
            
            # Combine scores
            combined_score = (semantic_weight * result['similarity'] + 
                            (1 - semantic_weight) * keyword_score)
            
            keyword_results.append({
                **result,
                'keyword_score': keyword_score,
                'combined_score': combined_score
            })
        
        # Sort by combined score
        keyword_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return keyword_results[:n_results]
    
    def keyword_search(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform keyword (substring) search over all stored chunks in ChromaDB.
        """
        results = []
        all_docs = self.collection.get()
        if not all_docs or not all_docs.get('metadatas'):
            return []
        documents = all_docs.get('documents') or []
        metadatas = all_docs.get('metadatas') or []
        for doc, meta in zip(documents, metadatas):
            fulltext = meta.get('fulltext', '')
            if not isinstance(fulltext, str):
                continue
            if query.lower() in fulltext.lower():
                if isinstance(meta, dict):
                    result = meta.copy()
                else:
                    result = dict(meta)
                result['snippet'] = fulltext
                results.append(result)
        return results[:n_results]
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the ChromaDB collection."""
        try:
            count = self.collection.count()
            return {
                'total_chunks': count,
                'model_name': self.model_name,
                'persist_directory': self.persist_directory
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def delete_index(self) -> bool:
        """Delete the entire index."""
        try:
            # Get all document IDs and delete them
            all_docs = self.collection.get()
            if all_docs and all_docs.get('ids'):
                self.collection.delete(ids=all_docs['ids'])
            logger.info("Semantic index deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting semantic index: {e}")
            return False


# Convenience functions for backward compatibility
def build_semantic_index(directory_path: str, persist_directory: str = "./chroma_db") -> Optional[Dict[str, Any]]:
    """Build semantic index for a directory."""
    indexer = SemanticIndexer(persist_directory)
    return indexer.build_semantic_index(directory_path)

def semantic_search(query: str, persist_directory: str = "./chroma_db", n_results: int = 10) -> List[Dict[str, Any]]:
    """Perform semantic search."""
    indexer = SemanticIndexer(persist_directory)
    return indexer.semantic_search(query, n_results)

def hybrid_search(query: str, persist_directory: str = "./chroma_db", n_results: int = 10) -> List[Dict[str, Any]]:
    """Perform hybrid search."""
    indexer = SemanticIndexer(persist_directory)
    return indexer.hybrid_search(query, n_results)


# Test function for standalone testing
if __name__ == '__main__':
    print("--- Running semantic indexer standalone tests ---")
    
    # Create test directory
    test_dir = "test_semantic_data"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create test files with semantic content
    test_files = [
        ("ai_article.txt", "Artificial intelligence is transforming the way we work and live. Machine learning algorithms are becoming more sophisticated."),
        ("ml_tutorial.txt", "Machine learning is a subset of artificial intelligence. It involves training models on data to make predictions."),
        ("data_science.txt", "Data science combines statistics, programming, and domain expertise. It's used to extract insights from data."),
        ("programming_basics.txt", "Programming is the process of writing instructions for computers. It involves logic and problem-solving skills."),
        ("web_development.txt", "Web development involves creating websites and web applications. It uses technologies like HTML, CSS, and JavaScript.")
    ]
    
    for filename, content in test_files:
        with open(os.path.join(test_dir, filename), "w", encoding="utf-8") as f:
            f.write(content)
    
    try:
        # Test semantic indexing
        print("Building semantic index...")
        indexer = SemanticIndexer(persist_directory="./test_chroma_db")
        stats = indexer.build_semantic_index(test_dir)
        
        if stats:
            print(f"✅ Index built successfully: {stats['stats']}")
            
            # Test semantic search
            print("\nTesting semantic search...")
            results = indexer.semantic_search("artificial intelligence", n_results=3)
            
            print(f"Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['filename']} (similarity: {result['similarity']:.3f})")
                print(f"   Snippet: {result['snippet'][:100]}...")
            
            # Test hybrid search
            print("\nTesting hybrid search...")
            hybrid_results = indexer.hybrid_search("machine learning", n_results=3)
            
            print(f"Found {len(hybrid_results)} results:")
            for i, result in enumerate(hybrid_results, 1):
                print(f"{i}. {result['filename']} (combined score: {result['combined_score']:.3f})")
                print(f"   Snippet: {result['snippet'][:100]}...")
            
            # Test collection stats
            print(f"\nCollection stats: {indexer.get_collection_stats()}")
            
        else:
            print("❌ Failed to build index")
            
    finally:
        # Clean up
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
        shutil.rmtree("./test_chroma_db", ignore_errors=True)
        print("\nTest complete.") 