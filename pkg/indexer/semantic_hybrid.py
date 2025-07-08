import os
import re
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from collections import defaultdict
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

# Import our file parsing utilities
from pkg.file_parsers.parsers import get_text_from_file
from pkg.utils.google_drive import GoogleDriveClient, GOOGLE_DRIVE_AVAILABLE

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

class HybridSemanticIndexer:
    """
    Hybrid semantic indexer that supports both local files and Google Drive files.
    Uses ChromaDB for vector storage and sentence-transformers for embeddings.
    """
    
    def __init__(self, persist_directory: str = "./chroma_db", model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the hybrid semantic indexer.
        
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
            name="hybrid_desktop_search",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Load sentence transformer model
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded sentence transformer model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer model: {e}")
            raise
        
        # Initialize Google Drive client if available
        self.gdrive_client = None
        if GOOGLE_DRIVE_AVAILABLE:
            try:
                self.gdrive_client = GoogleDriveClient()
                logger.info("Google Drive client initialized successfully")
            except Exception as e:
                logger.warning(f"Could not initialize Google Drive client: {e}")
    
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
    
    def _extract_local_metadata(self, filepath: str, chunk_index: int, total_chunks: int) -> Dict[str, Any]:
        """Extract metadata for a local document chunk."""
        return {
            "filepath": filepath,
            "filename": os.path.basename(filepath),
            "extension": os.path.splitext(filepath)[1].lower(),
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "file_size": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
            "source": "local"
        }
    
    def _extract_gdrive_metadata(self, file_info: Dict[str, Any], chunk_index: int, total_chunks: int) -> Dict[str, Any]:
        """Extract metadata for a Google Drive document chunk."""
        return {
            "filepath": f"gdrive://{file_info.get('id')}",
            "filename": file_info.get('name', 'Unknown'),
            "mime_type": file_info.get('mimeType', ''),
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "file_size": file_info.get('size', '0'),
            "modified_time": file_info.get('modifiedTime', ''),
            "source": "google_drive"
        }
    
    def _index_local_files(self, directory_path: str) -> Tuple[int, int, int]:
        """
        Index local files in the specified directory.
        
        Args:
            directory_path: Path to directory to index
            
        Returns:
            Tuple of (processed_files, skipped_files, total_chunks)
        """
        if not os.path.isdir(directory_path):
            logger.error(f"Directory not found at {directory_path}")
            return 0, 0, 0
        
        processed_files = 0
        skipped_files = 0
        total_chunks = 0
        
        logger.info(f"Indexing local files in: {directory_path}")
        
        for root, dirs, files in os.walk(directory_path):
            # Skip directories that match our patterns
            dirs[:] = [d for d in dirs if not self._should_skip_file(os.path.join(root, d))]
            
            for filename in files:
                filepath = os.path.join(root, filename)
                
                # Skip files that match our patterns
                if self._should_skip_file(filepath):
                    skipped_files += 1
                    continue
                
                try:
                    extracted_text, file_ext = get_text_from_file(filepath)
                    
                    if extracted_text and extracted_text.strip():
                        # Chunk the text
                        chunks = self._chunk_text(extracted_text)
                        
                        if chunks:
                            # Prepare data for ChromaDB
                            documents = []
                            metadatas = []
                            ids = []
                            
                            for i, chunk in enumerate(chunks):
                                chunk_id = f"local_{filepath}_{i}"
                                metadata = self._extract_local_metadata(filepath, i, len(chunks))
                                
                                documents.append(chunk)
                                metadatas.append(metadata)
                                ids.append(chunk_id)
                            
                            # Add to ChromaDB collection
                            self.collection.add(
                                documents=documents,
                                metadatas=metadatas,
                                ids=ids
                            )
                            
                            total_chunks += len(chunks)
                            processed_files += 1
                            
                            if processed_files % 50 == 0:
                                logger.info(f"Processed {processed_files} local files...")
                                
                except Exception as e:
                    logger.warning(f"Error processing local file {filepath}: {e}")
                    skipped_files += 1
                    continue
        
        return processed_files, skipped_files, total_chunks
    
    def _index_gdrive_files(self, folder_id: Optional[str] = None, query: Optional[str] = None) -> Tuple[int, int, int]:
        """
        Index Google Drive files.
        
        Args:
            folder_id: Google Drive folder ID to index (None for root)
            query: Additional query to filter files
            
        Returns:
            Tuple of (processed_files, skipped_files, total_chunks)
        """
        if not self.gdrive_client:
            logger.error("Google Drive client not available")
            return 0, 0, 0
        
        processed_files = 0
        skipped_files = 0
        total_chunks = 0
        
        logger.info(f"Indexing Google Drive files (folder_id: {folder_id or 'root'})")
        
        try:
            files = self.gdrive_client.list_files(folder_id=folder_id, query=query)
            
            for file_info in files:
                file_id = file_info.get('id')
                file_name = file_info.get('name', 'Unknown')
                
                try:
                    # Get file content
                    content = self.gdrive_client.get_file_content(file_id)
                    
                    if content and content.strip():
                        # Chunk the text
                        chunks = self._chunk_text(content)
                        
                        if chunks:
                            # Prepare data for ChromaDB
                            documents = []
                            metadatas = []
                            ids = []
                            
                            for i, chunk in enumerate(chunks):
                                chunk_id = f"gdrive_{file_id}_{i}"
                                metadata = self._extract_gdrive_metadata(file_info, i, len(chunks))
                                
                                documents.append(chunk)
                                metadatas.append(metadata)
                                ids.append(chunk_id)
                            
                            # Add to ChromaDB collection
                            self.collection.add(
                                documents=documents,
                                metadatas=metadatas,
                                ids=ids
                            )
                            
                            total_chunks += len(chunks)
                            processed_files += 1
                            
                            if processed_files % 50 == 0:
                                logger.info(f"Processed {processed_files} Google Drive files...")
                        else:
                            skipped_files += 1
                    else:
                        skipped_files += 1
                        logger.debug(f"Skipped Google Drive file with no content: {file_name}")
                        
                except Exception as e:
                    logger.warning(f"Error processing Google Drive file {file_name}: {e}")
                    skipped_files += 1
                    continue
                    
        except Exception as e:
            logger.error(f"Error accessing Google Drive: {e}")
            return 0, 0, 0
        
        return processed_files, skipped_files, total_chunks
    
    def build_hybrid_semantic_index(self, 
                                  local_directory: Optional[str] = None,
                                  gdrive_folder_id: Optional[str] = None,
                                  gdrive_query: Optional[str] = None,
                                  clear_existing: bool = True) -> Optional[Dict[str, Any]]:
        """
        Build hybrid semantic index for both local and Google Drive files.
        
        Args:
            local_directory: Path to local directory to index (None to skip local files)
            gdrive_folder_id: Google Drive folder ID to index (None to skip Google Drive)
            gdrive_query: Additional query to filter Google Drive files
            clear_existing: Whether to clear existing index before building
            
        Returns:
            Dictionary with indexing statistics
        """
        logger.info("Starting hybrid semantic indexing")
        
        # Clear existing collection if requested
        if clear_existing:
            try:
                all_docs = self.collection.get()
                if all_docs and all_docs.get('ids'):
                    self.collection.delete(ids=all_docs['ids'])
                    logger.info("Cleared existing semantic index")
            except Exception as e:
                logger.info(f"Collection was empty or could not be cleared: {e}")
        
        total_processed_files = 0
        total_skipped_files = 0
        total_chunks = 0
        
        # Index local files
        if local_directory:
            local_processed, local_skipped, local_chunks = self._index_local_files(local_directory)
            total_processed_files += local_processed
            total_skipped_files += local_skipped
            total_chunks += local_chunks
        
        # Index Google Drive files
        if gdrive_folder_id or gdrive_query:
            gdrive_processed, gdrive_skipped, gdrive_chunks = self._index_gdrive_files(
                folder_id=gdrive_folder_id, 
                query=gdrive_query
            )
            total_processed_files += gdrive_processed
            total_skipped_files += gdrive_skipped
            total_chunks += gdrive_chunks
        
        logger.info(f"Hybrid semantic indexing complete!")
        logger.info(f"Total files processed: {total_processed_files}")
        logger.info(f"Total chunks created: {total_chunks}")
        logger.info(f"Total files skipped: {total_skipped_files}")
        
        return {
            'stats': {
                'total_files': total_processed_files,
                'total_chunks': total_chunks,
                'skipped_files': total_skipped_files,
                'local_directory': local_directory,
                'gdrive_folder_id': gdrive_folder_id,
                'gdrive_query': gdrive_query,
                'model_name': self.model_name,
                'persist_directory': self.persist_directory
            }
        }
    
    def semantic_search(self, query: str, n_results: int = 10, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Perform semantic search on the hybrid index.
        
        Args:
            query: Search query
            n_results: Number of results to return
            threshold: Similarity threshold (0-1)
            
        Returns:
            List of search results
        """
        try:
            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=['metadatas', 'distances', 'documents']
            )
            
            if not results or not results.get('ids') or not results['ids'][0]:
                return []
            
            # Process results
            search_results = []
            for i, doc_id in enumerate(results['ids'][0]):
                distance = results['distances'][0][i]
                similarity = 1 - distance  # Convert distance to similarity
                
                if similarity >= threshold:
                    metadata = results['metadatas'][0][i]
                    document = results['documents'][0][i]
                    
                    result = {
                        'id': doc_id,
                        'similarity': similarity,
                        'snippet': document[:200] + "..." if len(document) > 200 else document,
                        **metadata
                    }
                    search_results.append(result)
            
            # Sort by similarity (highest first)
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
            List of search results
        """
        try:
            # Get semantic results
            semantic_results = self.semantic_search(query, n_results=n_results * 2, threshold=0.1)
            
            # Simple keyword matching (can be enhanced with TF-IDF)
            keyword_results = []
            query_lower = query.lower()
            
            # Get all documents for keyword matching
            all_docs = self.collection.get()
            if all_docs and all_docs.get('documents'):
                for i, doc in enumerate(all_docs['documents']):
                    if query_lower in doc.lower():
                        metadata = all_docs['metadatas'][i]
                        keyword_score = doc.lower().count(query_lower) / len(doc)
                        
                        keyword_results.append({
                            'id': all_docs['ids'][i],
                            'keyword_score': keyword_score,
                            'snippet': doc[:200] + "..." if len(doc) > 200 else doc,
                            **metadata
                        })
            
            # Sort keyword results by score
            keyword_results.sort(key=lambda x: x['keyword_score'], reverse=True)
            keyword_results = keyword_results[:n_results]
            
            # Combine results
            combined_results = {}
            
            # Add semantic results
            for result in semantic_results:
                combined_results[result['id']] = {
                    **result,
                    'combined_score': result['similarity'] * semantic_weight
                }
            
            # Add keyword results
            for result in keyword_results:
                if result['id'] in combined_results:
                    # Combine scores
                    combined_results[result['id']]['combined_score'] += result['keyword_score'] * (1 - semantic_weight)
                else:
                    combined_results[result['id']] = {
                        **result,
                        'combined_score': result['keyword_score'] * (1 - semantic_weight)
                    }
            
            # Sort by combined score and return top results
            final_results = list(combined_results.values())
            final_results.sort(key=lambda x: x['combined_score'], reverse=True)
            
            return final_results[:n_results]
            
        except Exception as e:
            logger.error(f"Error during hybrid search: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the ChromaDB collection."""
        try:
            all_docs = self.collection.get()
            
            if not all_docs or not all_docs.get('ids'):
                return {
                    'total_chunks': 0,
                    'model_name': self.model_name,
                    'persist_directory': self.persist_directory
                }
            
            # Count by source
            local_count = 0
            gdrive_count = 0
            
            for metadata in all_docs['metadatas']:
                if metadata.get('source') == 'local':
                    local_count += 1
                elif metadata.get('source') == 'google_drive':
                    gdrive_count += 1
            
            return {
                'total_chunks': len(all_docs['ids']),
                'local_chunks': local_count,
                'gdrive_chunks': gdrive_count,
                'model_name': self.model_name,
                'persist_directory': self.persist_directory
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def delete_index(self) -> bool:
        """Delete the entire semantic index."""
        try:
            all_docs = self.collection.get()
            if all_docs and all_docs.get('ids'):
                self.collection.delete(ids=all_docs['ids'])
                logger.info("Semantic index deleted successfully")
                return True
            else:
                logger.info("No documents to delete")
                return True
        except Exception as e:
            logger.error(f"Error deleting semantic index: {e}")
            return False


# Convenience functions
def build_hybrid_semantic_index(local_directory: Optional[str] = None,
                               gdrive_folder_id: Optional[str] = None,
                               gdrive_query: Optional[str] = None,
                               persist_directory: str = "./chroma_db",
                               model_name: str = "all-MiniLM-L6-v2") -> Optional[Dict[str, Any]]:
    """Build hybrid semantic index for both local and Google Drive files."""
    indexer = HybridSemanticIndexer(persist_directory=persist_directory, model_name=model_name)
    return indexer.build_hybrid_semantic_index(
        local_directory=local_directory,
        gdrive_folder_id=gdrive_folder_id,
        gdrive_query=gdrive_query
    )

def hybrid_semantic_search(query: str, 
                          persist_directory: str = "./chroma_db",
                          n_results: int = 10,
                          threshold: float = 0.3) -> List[Dict[str, Any]]:
    """Perform semantic search on the hybrid index."""
    indexer = HybridSemanticIndexer(persist_directory=persist_directory)
    return indexer.semantic_search(query, n_results=n_results, threshold=threshold)

def hybrid_search(query: str,
                 persist_directory: str = "./chroma_db",
                 n_results: int = 10,
                 semantic_weight: float = 0.7) -> List[Dict[str, Any]]:
    """Perform hybrid search on the hybrid index."""
    indexer = HybridSemanticIndexer(persist_directory=persist_directory)
    return indexer.hybrid_search(query, n_results=n_results, semantic_weight=semantic_weight) 