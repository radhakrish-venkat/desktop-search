"""
Enhanced Search Router - Hybrid Search with Notebook-style Q&A
Provides comprehensive search capabilities with local LLM integration
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, List, Optional, Any
import logging
import uuid
from datetime import datetime
from pydantic import BaseModel, Field

# Import enhanced search functionality
from pkg.indexer.enhanced_hybrid_search import EnhancedHybridSearch, SearchResult, QASession
from pkg.llm.local_llm import LocalLLMManager, LLMConfig

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/enhanced-search", tags=["enhanced-search"])

# Request/Response Models
class EnhancedIndexRequest(BaseModel):
    """Request model for enhanced indexing"""
    directory_path: str = Field(..., description="Directory to index")
    clear_existing: bool = Field(default=True, description="Clear existing index")
    chunk_size: int = Field(default=1000, description="Chunk size in characters")
    chunk_overlap: int = Field(default=200, description="Chunk overlap")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Embedding model")
    enable_llm: bool = Field(default=True, description="Enable LLM integration")

class HybridSearchRequest(BaseModel):
    """Request model for hybrid search"""
    query: str = Field(..., description="Search query")
    n_results: int = Field(default=10, description="Number of results")
    semantic_weight: float = Field(default=0.7, description="Weight for semantic search")
    keyword_weight: float = Field(default=0.3, description="Weight for keyword search")
    include_metadata: bool = Field(default=True, description="Include metadata in results")

class QuestionRequest(BaseModel):
    """Request model for Q&A"""
    question: str = Field(..., description="Question to ask")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation context")
    max_context_results: int = Field(default=5, description="Maximum results to use as context")
    include_sources: bool = Field(default=True, description="Include source documents")

class QASessionRequest(BaseModel):
    """Request model for Q&A session management"""
    session_id: str = Field(..., description="Session ID")

class EnhancedSearchResponse(BaseModel):
    """Response model for enhanced search operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# Global search instance
_enhanced_search: Optional[EnhancedHybridSearch] = None

def get_enhanced_search() -> EnhancedHybridSearch:
    """Get or create enhanced search instance"""
    global _enhanced_search
    if _enhanced_search is None:
        try:
            _enhanced_search = EnhancedHybridSearch(
                persist_directory="./enhanced_search_db",
                embedding_model="all-MiniLM-L6-v2",
                enable_llm=True
            )
        except Exception as e:
            logger.error(f"Failed to initialize enhanced search: {e}")
            raise HTTPException(status_code=500, detail="Enhanced search not available")
    return _enhanced_search

@router.post("/index", response_model=EnhancedSearchResponse)
async def index_documents_enhanced(request: EnhancedIndexRequest, background_tasks: BackgroundTasks):
    """
    Index documents using enhanced hybrid search system
    """
    try:
        search = get_enhanced_search()
        
        # Update search configuration if needed
        if request.chunk_size != search.chunk_size or request.chunk_overlap != search.chunk_overlap:
            logger.info("Recreating search instance with new configuration")
            global _enhanced_search
            _enhanced_search.cleanup()
            _enhanced_search = EnhancedHybridSearch(
                persist_directory="./enhanced_search_db",
                embedding_model=request.embedding_model,
                chunk_size=request.chunk_size,
                chunk_overlap=request.chunk_overlap,
                enable_llm=request.enable_llm
            )
            search = _enhanced_search
        
        # Index documents
        stats = search.index_documents(
            directory_path=request.directory_path,
            clear_existing=request.clear_existing
        )
        
        return EnhancedSearchResponse(
            success=True,
            message=f"Successfully indexed {stats['processed_files']} files with {stats['total_chunks']} chunks",
            data={
                "statistics": stats,
                "configuration": {
                    "chunk_size": request.chunk_size,
                    "chunk_overlap": request.chunk_overlap,
                    "embedding_model": request.embedding_model,
                    "enable_llm": request.enable_llm
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Enhanced indexing error: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing error: {str(e)}")

@router.post("/search", response_model=EnhancedSearchResponse)
async def hybrid_search_enhanced(request: HybridSearchRequest):
    """
    Perform hybrid search combining semantic and keyword search
    """
    try:
        search = get_enhanced_search()
        
        # Perform hybrid search
        results = search.hybrid_search(
            query=request.query,
            n_results=request.n_results,
            semantic_weight=request.semantic_weight,
            keyword_weight=request.keyword_weight
        )
        
        # Prepare response data
        response_data = {
            "query": request.query,
            "total_results": len(results),
            "results": []
        }
        
        for result in results:
            result_data = {
                "content": result.content,
                "filepath": result.filepath,
                "filename": result.filename,
                "file_type": result.file_type,
                "chunk_index": result.chunk_index,
                "total_chunks": result.total_chunks,
                "score": result.score,
                "search_type": result.search_type
            }
            
            if request.include_metadata:
                result_data["metadata"] = result.metadata
            
            response_data["results"].append(result_data)
        
        return EnhancedSearchResponse(
            success=True,
            message=f"Found {len(results)} results for query: {request.query}",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Enhanced search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@router.post("/ask", response_model=EnhancedSearchResponse)
async def ask_question_enhanced(request: QuestionRequest):
    """
    Ask a question and get AI-powered answer with context
    """
    try:
        search = get_enhanced_search()
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Ask question
        answer_data = search.ask_question(
            question=request.question,
            session_id=session_id
        )
        
        # Prepare response
        response_data = {
            "question": request.question,
            "answer": answer_data.get('answer', ''),
            "session_id": session_id,
            "sources": answer_data.get('sources', []),
            "context_used": answer_data.get('context_used', ''),
            "search_results_count": len(answer_data.get('search_results', []))
        }
        
        if request.include_sources and answer_data.get('search_results'):
            response_data["search_results"] = answer_data['search_results'][:request.max_context_results]
        
        return EnhancedSearchResponse(
            success=True,
            message="Question answered successfully",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Q&A error: {e}")
        raise HTTPException(status_code=500, detail=f"Q&A error: {str(e)}")

@router.get("/session/{session_id}", response_model=EnhancedSearchResponse)
async def get_qa_session(session_id: str):
    """
    Get Q&A session history
    """
    try:
        search = get_enhanced_search()
        
        qa_session = search.get_qa_session(session_id)
        
        if not qa_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return EnhancedSearchResponse(
            success=True,
            message=f"Retrieved Q&A session: {session_id}",
            data={
                "session_id": qa_session.session_id,
                "created_at": qa_session.created_at.isoformat(),
                "total_questions": len(qa_session.questions),
                "total_tokens": qa_session.total_tokens,
                "questions": qa_session.questions,
                "context_history": qa_session.context_history
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Q&A session: {e}")
        raise HTTPException(status_code=500, detail=f"Session error: {str(e)}")

@router.delete("/session/{session_id}")
async def delete_qa_session(session_id: str):
    """
    Delete Q&A session
    """
    try:
        search = get_enhanced_search()
        
        # Delete from database
        search.qa_db.execute("DELETE FROM qa_questions WHERE session_id = ?", (session_id,))
        search.qa_db.execute("DELETE FROM qa_sessions WHERE session_id = ?", (session_id,))
        search.qa_db.commit()
        
        return EnhancedSearchResponse(
            success=True,
            message=f"Deleted Q&A session: {session_id}"
        )
        
    except Exception as e:
        logger.error(f"Error deleting Q&A session: {e}")
        raise HTTPException(status_code=500, detail=f"Delete error: {str(e)}")

@router.get("/sessions", response_model=EnhancedSearchResponse)
async def list_qa_sessions():
    """
    List all Q&A sessions
    """
    try:
        search = get_enhanced_search()
        
        sessions = search.qa_db.execute("""
            SELECT s.session_id, s.created_at, s.total_tokens,
                   COUNT(q.id) as question_count
            FROM qa_sessions s
            LEFT JOIN qa_questions q ON s.session_id = q.session_id
            GROUP BY s.session_id
            ORDER BY s.created_at DESC
        """).fetchall()
        
        session_list = []
        for session in sessions:
            session_list.append({
                "session_id": session['session_id'],
                "created_at": session['created_at'],
                "total_tokens": session['total_tokens'],
                "question_count": session['question_count']
            })
        
        return EnhancedSearchResponse(
            success=True,
            message=f"Retrieved {len(session_list)} Q&A sessions",
            data={"sessions": session_list}
        )
        
    except Exception as e:
        logger.error(f"Error listing Q&A sessions: {e}")
        raise HTTPException(status_code=500, detail=f"List error: {str(e)}")

@router.get("/semantic-search", response_model=EnhancedSearchResponse)
async def semantic_search_only(query: str, n_results: int = 10):
    """
    Perform semantic search only
    """
    try:
        search = get_enhanced_search()
        
        results = search._semantic_search(query, n_results)
        
        response_data = {
            "query": query,
            "search_type": "semantic",
            "total_results": len(results),
            "results": [{
                "content": result.content,
                "filepath": result.filepath,
                "filename": result.filename,
                "file_type": result.file_type,
                "score": result.score,
                "metadata": result.metadata
            } for result in results]
        }
        
        return EnhancedSearchResponse(
            success=True,
            message=f"Semantic search found {len(results)} results",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        raise HTTPException(status_code=500, detail=f"Semantic search error: {str(e)}")

@router.get("/keyword-search", response_model=EnhancedSearchResponse)
async def keyword_search_only(query: str, n_results: int = 10):
    """
    Perform keyword search only
    """
    try:
        search = get_enhanced_search()
        
        results = search._keyword_search(query, n_results)
        
        response_data = {
            "query": query,
            "search_type": "keyword",
            "total_results": len(results),
            "results": [{
                "content": result.content,
                "filepath": result.filepath,
                "filename": result.filename,
                "file_type": result.file_type,
                "score": result.score,
                "metadata": result.metadata
            } for result in results]
        }
        
        return EnhancedSearchResponse(
            success=True,
            message=f"Keyword search found {len(results)} results",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Keyword search error: {e}")
        raise HTTPException(status_code=500, detail=f"Keyword search error: {str(e)}")

@router.get("/stats", response_model=EnhancedSearchResponse)
async def get_enhanced_search_stats():
    """
    Get enhanced search system statistics
    """
    try:
        search = get_enhanced_search()
        
        stats = search.get_stats()
        
        return EnhancedSearchResponse(
            success=True,
            message="Enhanced search statistics retrieved",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Error getting enhanced search stats: {e}")
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

@router.post("/clear-index")
async def clear_enhanced_index():
    """
    Clear the enhanced search index
    """
    try:
        search = get_enhanced_search()
        
        search._clear_indexes()
        
        return EnhancedSearchResponse(
            success=True,
            message="Enhanced search index cleared"
        )
        
    except Exception as e:
        logger.error(f"Error clearing enhanced search index: {e}")
        raise HTTPException(status_code=500, detail=f"Clear error: {str(e)}")

@router.get("/health", response_model=EnhancedSearchResponse)
async def enhanced_search_health():
    """
    Check enhanced search system health
    """
    try:
        search = get_enhanced_search()
        
        # Basic health checks
        health_data = {
            "status": "healthy",
            "vector_store": "available",
            "keyword_index": "available",
            "qa_database": "available",
            "llm_integration": "available" if search.enable_llm else "disabled"
        }
        
        # Test vector store
        try:
            count = search.vector_collection.count()
            health_data["vector_documents"] = count
        except Exception:
            health_data["vector_store"] = "error"
            health_data["status"] = "degraded"
        
        # Test keyword index
        try:
            with search.keyword_index.searcher() as searcher:
                doc_count = searcher.doc_count()
                health_data["keyword_documents"] = doc_count
        except Exception:
            health_data["keyword_index"] = "error"
            health_data["status"] = "degraded"
        
        # Test LLM if enabled
        if search.enable_llm and search.llm_manager:
            try:
                provider_status = search.llm_manager.get_provider_status()
                health_data["llm_provider"] = provider_status.get("active_provider", "unknown")
            except Exception:
                health_data["llm_integration"] = "error"
                health_data["status"] = "degraded"
        
        return EnhancedSearchResponse(
            success=True,
            message="Enhanced search system health check completed",
            data=health_data
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return EnhancedSearchResponse(
            success=False,
            message="Health check failed",
            data={"status": "unhealthy", "error": str(e)}
        ) 