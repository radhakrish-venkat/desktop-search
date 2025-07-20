"""
Enhanced Hybrid Search System with Notebook-style Q&A
Combines keyword search (BM25), semantic search, and local LLM integration
"""

import os
import re
import logging
import sqlite3
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict
import threading
from pathlib import Path

# Vector search and embeddings
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

# Keyword search
from whoosh.index import create_in
from whoosh.fields import Schema, ID, TEXT, NUMERIC, STORED
from whoosh.qparser import QueryParser
from whoosh.analysis import StandardAnalyzer

# LLM integration
from pkg.llm.local_llm import LocalLLMManager, LLMConfig

# Enhanced file parsing
from pkg.file_parsers.enhanced_parsers import EnhancedDocumentParser, DocumentMetadata

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Enhanced search result with metadata"""
    content: str
    filepath: str
    filename: str
    file_type: str
    chunk_index: int
    total_chunks: int
    score: float
    search_type: str  # 'keyword', 'semantic', 'hybrid'
    metadata: Dict[str, Any]
    context: Optional[str] = None

@dataclass
class QASession:
    """Q&A session for notebook-style interaction"""
    session_id: str
    created_at: datetime
    questions: List[Dict[str, Any]]
    context_history: List[str]
    total_tokens: int = 0
    
    def add_question(self, question: str, answer: str, search_results: List[SearchResult], tokens_used: int):
        """Add a question-answer pair to the session"""
        self.questions.append({
            'question': question,
            'answer': answer,
            'search_results': [asdict(result) for result in search_results],
            'timestamp': datetime.now().isoformat(),
            'tokens_used': tokens_used
        })
        self.total_tokens += tokens_used
        
        # Add context from search results
        context_parts = []
        for result in search_results[:3]:  # Top 3 results for context
            context_parts.append(f"File: {result.filename}\nContent: {result.content[:200]}...")
        self.context_history.extend(context_parts)

class EnhancedHybridSearch:
    """
    Enhanced hybrid search system with notebook-style Q&A
    """
    
    def __init__(self, 
                 persist_directory: str = "./enhanced_search_db",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 enable_llm: bool = True):
        """
        Initialize the enhanced hybrid search system
        
        Args:
            persist_directory: Directory to persist search data
            embedding_model: Sentence transformer model name
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            enable_llm: Whether to enable LLM integration
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.enable_llm = enable_llm
        
        # Initialize components
        self._init_vector_store()
        self._init_keyword_index()
        self._init_qa_database()
        self._init_embeddings()
        self._init_llm()
        self._init_document_parser()
        
        # Thread safety
        self.lock = threading.RLock()
        
        logger.info("Enhanced hybrid search system initialized")
    
    def _init_vector_store(self):
        """Initialize ChromaDB vector store"""
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.persist_directory / "chroma"),
                settings=Settings(anonymized_telemetry=False)
            )
            
            self.vector_collection = self.chroma_client.get_or_create_collection(
                name="enhanced_search",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Vector store initialized")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def _init_keyword_index(self):
        """Initialize Whoosh keyword search index"""
        try:
            index_dir = self.persist_directory / "whoosh_index"
            index_dir.mkdir(exist_ok=True)
            
            # Define schema
            schema = Schema(
                filepath=ID(stored=True),
                filename=TEXT(stored=True),
                content=TEXT(stored=True),
                file_type=TEXT(stored=True),
                chunk_index=NUMERIC(stored=True),
                total_chunks=NUMERIC(stored=True),
                metadata=STORED
            )
            
            # Create or open index
            if not os.path.exists(str(index_dir / "segments")):
                self.keyword_index = create_in(str(index_dir), schema)
            else:
                from whoosh.index import open_dir
                self.keyword_index = open_dir(str(index_dir))
            
            logger.info("Keyword search index initialized")
        except Exception as e:
            logger.error(f"Failed to initialize keyword index: {e}")
            raise
    
    def _init_qa_database(self):
        """Initialize SQLite database for Q&A sessions"""
        try:
            db_path = self.persist_directory / "qa_sessions.db"
            self.qa_db = sqlite3.connect(str(db_path))
            self.qa_db.row_factory = sqlite3.Row
            
            # Create tables
            self.qa_db.execute("""
                CREATE TABLE IF NOT EXISTS qa_sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    total_tokens INTEGER DEFAULT 0
                )
            """)
            
            self.qa_db.execute("""
                CREATE TABLE IF NOT EXISTS qa_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    search_results TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    tokens_used INTEGER DEFAULT 0,
                    FOREIGN KEY (session_id) REFERENCES qa_sessions (session_id)
                )
            """)
            
            self.qa_db.commit()
            logger.info("Q&A database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Q&A database: {e}")
            raise
    
    def _init_embeddings(self):
        """Initialize sentence transformer model"""
        try:
            self.embedding_model = SentenceTransformer(self.embedding_model)
            logger.info(f"Embedding model loaded: {self.embedding_model}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _init_llm(self):
        """Initialize local LLM manager"""
        if self.enable_llm:
            try:
                config = LLMConfig(
                    llm_model="phi3",
                    llm_max_tokens=2048,
                    llm_temperature=0.7,
                    embedding_model="all-MiniLM-L6-v2"
                )
                self.llm_manager = LocalLLMManager(config)
                logger.info("Local LLM manager initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM manager: {e}")
                self.enable_llm = False
        else:
            self.llm_manager = None
    
    def _init_document_parser(self):
        """Initialize enhanced document parser"""
        self.document_parser = EnhancedDocumentParser(
            enable_ocr=True,
            enable_unstructured=True
        )
    
    def index_documents(self, directory_path: str, clear_existing: bool = True) -> Dict[str, Any]:
        """
        Index documents from directory with enhanced processing
        
        Args:
            directory_path: Path to directory to index
            clear_existing: Whether to clear existing index
            
        Returns:
            Indexing statistics
        """
        with self.lock:
            if clear_existing:
                self._clear_indexes()
            
            stats = {
                'processed_files': 0,
                'skipped_files': 0,
                'total_chunks': 0,
                'errors': [],
                'start_time': datetime.now()
            }
            
            logger.info(f"Starting enhanced indexing of: {directory_path}")
            
            # Process files
            for root, dirs, files in os.walk(directory_path):
                # Skip system directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
                
                for filename in files:
                    filepath = os.path.join(root, filename)
                    
                    try:
                        # Parse document
                        content, metadata = self.document_parser.parse_document(filepath)
                        
                        if content and metadata:
                            # Chunk content
                            chunks = self._chunk_text(content)
                            
                            # Index chunks
                            for i, chunk in enumerate(chunks):
                                self._index_chunk(chunk, filepath, metadata, i, len(chunks))
                            
                            stats['processed_files'] += 1
                            stats['total_chunks'] += len(chunks)
                            
                            logger.debug(f"Indexed {filename}: {len(chunks)} chunks")
                        else:
                            stats['skipped_files'] += 1
                            
                    except Exception as e:
                        error_msg = f"Error processing {filepath}: {e}"
                        stats['errors'].append(error_msg)
                        logger.error(error_msg)
            
            stats['end_time'] = datetime.now()
            stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()
            
            logger.info(f"Indexing completed: {stats['processed_files']} files, {stats['total_chunks']} chunks")
            return stats
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                search_start = max(start, end - 100)
                sentence_end = text.rfind('.', search_start, end)
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _index_chunk(self, chunk: str, filepath: str, metadata: DocumentMetadata, chunk_index: int, total_chunks: int):
        """Index a single chunk in both vector and keyword stores"""
        chunk_id = f"{filepath}_{chunk_index}"
        
        # Index in vector store
        try:
            embedding = self.embedding_model.encode([chunk])[0].tolist()
            
            self.vector_collection.add(
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[{
                    'filepath': filepath,
                    'filename': metadata.filename,
                    'file_type': metadata.file_type,
                    'chunk_index': chunk_index,
                    'total_chunks': total_chunks,
                    'file_size': metadata.file_size,
                    'language': metadata.language,
                    'has_code': metadata.has_code,
                    'has_tables': metadata.has_tables,
                    'has_images': metadata.has_images
                }],
                ids=[chunk_id]
            )
        except Exception as e:
            logger.error(f"Failed to index chunk in vector store: {e}")
        
        # Index in keyword store
        try:
            writer = self.keyword_index.writer()
            writer.add_document(
                filepath=filepath,
                filename=metadata.filename,
                content=chunk,
                file_type=metadata.file_type,
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                metadata=json.dumps(metadata.to_dict())
            )
            writer.commit()
        except Exception as e:
            logger.error(f"Failed to index chunk in keyword store: {e}")
    
    def hybrid_search(self, query: str, n_results: int = 10, 
                     semantic_weight: float = 0.7, 
                     keyword_weight: float = 0.3) -> List[SearchResult]:
        """
        Perform hybrid search combining semantic and keyword search
        
        Args:
            query: Search query
            n_results: Number of results to return
            semantic_weight: Weight for semantic search results
            keyword_weight: Weight for keyword search results
            
        Returns:
            List of search results
        """
        with self.lock:
            # Perform semantic search
            semantic_results = self._semantic_search(query, n_results * 2)
            
            # Perform keyword search
            keyword_results = self._keyword_search(query, n_results * 2)
            
            # Combine and rank results
            combined_results = self._combine_results(
                semantic_results, keyword_results, 
                semantic_weight, keyword_weight
            )
            
            # Return top results
            return combined_results[:n_results]
    
    def _semantic_search(self, query: str, n_results: int) -> List[SearchResult]:
        """Perform semantic search using embeddings"""
        try:
            query_embedding = self.embedding_model.encode([query])[0].tolist()
            
            results = self.vector_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            search_results = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0], 
                results['metadatas'][0], 
                results['distances'][0]
            )):
                # Convert distance to similarity score
                score = 1.0 - distance
                
                search_results.append(SearchResult(
                    content=doc,
                    filepath=metadata['filepath'],
                    filename=metadata['filename'],
                    file_type=metadata['file_type'],
                    chunk_index=metadata['chunk_index'],
                    total_chunks=metadata['total_chunks'],
                    score=score,
                    search_type='semantic',
                    metadata=metadata
                ))
            
            return search_results
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def _keyword_search(self, query: str, n_results: int) -> List[SearchResult]:
        """Perform keyword search using BM25"""
        try:
            with self.keyword_index.searcher() as searcher:
                query_parser = QueryParser("content", self.keyword_index.schema)
                q = query_parser.parse(query)
                
                results = searcher.search(q, limit=n_results)
                
                search_results = []
                for result in results:
                    search_results.append(SearchResult(
                        content=result['content'],
                        filepath=result['filepath'],
                        filename=result['filename'],
                        file_type=result['file_type'],
                        chunk_index=result['chunk_index'],
                        total_chunks=result['total_chunks'],
                        score=result.score,
                        search_type='keyword',
                        metadata=json.loads(result['metadata'])
                    ))
                
                return search_results
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []
    
    def _combine_results(self, semantic_results: List[SearchResult], 
                        keyword_results: List[SearchResult],
                        semantic_weight: float, keyword_weight: float) -> List[SearchResult]:
        """Combine and rank search results"""
        # Create lookup for results by filepath and chunk
        result_lookup = {}
        
        # Add semantic results
        for result in semantic_results:
            key = (result.filepath, result.chunk_index)
            result_lookup[key] = result
        
        # Combine with keyword results
        for result in keyword_results:
            key = (result.filepath, result.chunk_index)
            if key in result_lookup:
                # Combine scores
                existing = result_lookup[key]
                combined_score = (existing.score * semantic_weight + 
                                result.score * keyword_weight)
                existing.score = combined_score
                existing.search_type = 'hybrid'
            else:
                result_lookup[key] = result
        
        # Sort by combined score
        combined_results = list(result_lookup.values())
        combined_results.sort(key=lambda x: x.score, reverse=True)
        
        return combined_results
    
    def ask_question(self, question: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Ask a question and get AI-powered answer with context
        
        Args:
            question: The question to ask
            session_id: Optional session ID for conversation context
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        if not self.enable_llm or not self.llm_manager:
            return {
                'answer': 'LLM integration not available',
                'sources': [],
                'session_id': session_id,
                'error': 'LLM not enabled'
            }
        
        try:
            # Search for relevant documents
            search_results = self.hybrid_search(question, n_results=5)
            
            if not search_results:
                return {
                    'answer': 'No relevant documents found to answer your question.',
                    'sources': [],
                    'session_id': session_id,
                    'search_results': []
                }
            
            # Prepare context for LLM
            context = self._prepare_context(search_results)
            
            # Generate answer using LLM
            answer = self.llm_manager.answer_question(question, search_results)
            
            # Save to Q&A session if session_id provided
            if session_id:
                self._save_qa_session(session_id, question, answer, search_results)
            
            return {
                'answer': answer,
                'sources': [result.filepath for result in search_results],
                'session_id': session_id,
                'search_results': [asdict(result) for result in search_results],
                'context_used': context[:500] + "..." if len(context) > 500 else context
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                'answer': f'Error generating answer: {str(e)}',
                'sources': [],
                'session_id': session_id,
                'error': str(e)
            }
    
    def _prepare_context(self, search_results: List[SearchResult]) -> str:
        """Prepare context from search results for LLM"""
        context_parts = []
        
        for i, result in enumerate(search_results[:3]):  # Top 3 results
            context_parts.append(f"Document {i+1} ({result.filename}):\n{result.content}")
        
        return "\n\n".join(context_parts)
    
    def _save_qa_session(self, session_id: str, question: str, answer: str, search_results: List[SearchResult]):
        """Save Q&A interaction to database"""
        try:
            # Create session if it doesn't exist
            self.qa_db.execute(
                "INSERT OR IGNORE INTO qa_sessions (session_id, created_at) VALUES (?, ?)",
                (session_id, datetime.now().isoformat())
            )
            
            # Save question
            self.qa_db.execute(
                """INSERT INTO qa_questions 
                   (session_id, question, answer, search_results, timestamp, tokens_used)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (session_id, question, answer, json.dumps([asdict(r) for r in search_results]), 
                 datetime.now().isoformat(), 0)  # TODO: track actual token usage
            )
            
            self.qa_db.commit()
        except Exception as e:
            logger.error(f"Failed to save Q&A session: {e}")
    
    def get_qa_session(self, session_id: str) -> Optional[QASession]:
        """Get Q&A session history"""
        try:
            # Get session info
            session_row = self.qa_db.execute(
                "SELECT * FROM qa_sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            
            if not session_row:
                return None
            
            # Get questions
            questions = self.qa_db.execute(
                "SELECT * FROM qa_questions WHERE session_id = ? ORDER BY timestamp",
                (session_id,)
            ).fetchall()
            
            qa_session = QASession(
                session_id=session_id,
                created_at=datetime.fromisoformat(session_row['created_at']),
                questions=[],
                context_history=[],
                total_tokens=session_row['total_tokens']
            )
            
            for q in questions:
                qa_session.questions.append({
                    'question': q['question'],
                    'answer': q['answer'],
                    'search_results': json.loads(q['search_results']),
                    'timestamp': q['timestamp'],
                    'tokens_used': q['tokens_used']
                })
            
            return qa_session
            
        except Exception as e:
            logger.error(f"Failed to get Q&A session: {e}")
            return None
    
    def _clear_indexes(self):
        """Clear all indexes"""
        try:
            # Clear vector store
            self.vector_collection.delete(where={})
            
            # Clear keyword index
            writer = self.keyword_index.writer()
            writer.delete_by_query(None)
            writer.commit()
            
            logger.info("Indexes cleared")
        except Exception as e:
            logger.error(f"Failed to clear indexes: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search system statistics"""
        try:
            # Vector store stats
            vector_count = self.vector_collection.count()
            
            # Keyword index stats
            with self.keyword_index.searcher() as searcher:
                keyword_count = searcher.doc_count()
            
            # Q&A session stats
            session_count = self.qa_db.execute("SELECT COUNT(*) FROM qa_sessions").fetchone()[0]
            question_count = self.qa_db.execute("SELECT COUNT(*) FROM qa_questions").fetchone()[0]
            
            return {
                'vector_documents': vector_count,
                'keyword_documents': keyword_count,
                'qa_sessions': session_count,
                'total_questions': question_count,
                'embedding_model': str(self.embedding_model),
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap,
                'llm_enabled': self.enable_llm
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {'error': str(e)}
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'qa_db'):
                self.qa_db.close()
            if hasattr(self, 'llm_manager'):
                self.llm_manager.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Convenience functions
def create_enhanced_search(persist_directory: str = "./enhanced_search_db",
                          embedding_model: str = "all-MiniLM-L6-v2",
                          enable_llm: bool = True) -> EnhancedHybridSearch:
    """Create an enhanced hybrid search instance"""
    return EnhancedHybridSearch(
        persist_directory=persist_directory,
        embedding_model=embedding_model,
        enable_llm=enable_llm
    )

def enhanced_hybrid_search(query: str, 
                          persist_directory: str = "./enhanced_search_db",
                          n_results: int = 10) -> List[SearchResult]:
    """Convenience function for hybrid search"""
    search = create_enhanced_search(persist_directory)
    return search.hybrid_search(query, n_results) 