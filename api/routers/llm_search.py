"""
LLM-Enhanced Search API Endpoints
Provides ChatGPT-like search enhancement capabilities using local models
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from pkg.llm.local_llm import get_llm_manager, LLMConfig, EmbeddingModel, LLMModel
from pkg.indexer.semantic import SemanticIndexer

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["LLM Enhanced Search"])

class SearchRequest(BaseModel):
    query: str
    max_results: int = 10
    use_llm: bool = True
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None

class QuestionRequest(BaseModel):
    question: str
    query: str
    max_results: int = 10
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None

class SummaryRequest(BaseModel):
    query: str
    max_results: int = 10
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None

class ModelConfigRequest(BaseModel):
    llm_model: str
    embedding_model: str
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.7
    llm_top_p: float = 0.9

class SearchResponse(BaseModel):
    enhanced: bool
    query: str
    llm_response: Optional[str] = None
    results: List[Dict[str, Any]]
    provider: Optional[str] = None
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
    message: Optional[str] = None

class QuestionResponse(BaseModel):
    answered: bool
    question: str
    answer: str
    provider: Optional[str] = None
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
    sources: List[str]
    message: Optional[str] = None

class SummaryResponse(BaseModel):
    summarized: bool
    summary: str
    provider: Optional[str] = None
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
    result_count: int
    message: Optional[str] = None

class ModelStatusResponse(BaseModel):
    active_provider: Optional[str]
    available_providers: List[Dict[str, Any]]
    detected_providers: List[str]
    embedding_model: Dict[str, Any]
    llm_model: Optional[str]

class ModelConfigResponse(BaseModel):
    success: bool
    message: str
    config: Optional[Dict[str, Any]] = None

class PerformanceStatsResponse(BaseModel):
    total_requests: int
    cache_hits: int
    cache_hit_rate: float
    average_response_time: float
    total_response_time: float

@router.get("/status", response_model=ModelStatusResponse)
async def get_llm_status():
    """Get the status of LLM providers and models"""
    try:
        llm_manager = get_llm_manager()
        status = llm_manager.get_provider_status()
        return ModelStatusResponse(**status)
    except Exception as e:
        logger.error(f"Error getting LLM status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting LLM status: {str(e)}")

@router.post("/config", response_model=ModelConfigResponse)
async def configure_models(request: ModelConfigRequest):
    """Configure LLM and embedding models"""
    try:
        llm_manager = get_llm_manager()
        
        # Update configuration
        config = LLMConfig(
            llm_model=request.llm_model,
            embedding_model=request.embedding_model,
            llm_max_tokens=request.llm_max_tokens,
            llm_temperature=request.llm_temperature,
            llm_top_p=request.llm_top_p
        )
        
        # Reinitialize with new config
        llm_manager.config = config
        llm_manager.embedding_manager.config = config
        
        # Reload embedding model
        embedding_loaded = llm_manager.embedding_manager.load_embedding_model()
        
        # Detect and set active provider
        available_providers = llm_manager.detect_providers()
        provider_set = False
        if available_providers:
            provider_set = llm_manager.set_active_provider(available_providers[0])
        
        return ModelConfigResponse(
            success=True,
            message=f"Configuration updated. Embedding model loaded: {embedding_loaded}, Active provider: {available_providers[0] if available_providers else 'None'}",
            config={
                "llm_model": request.llm_model,
                "embedding_model": request.embedding_model,
                "llm_max_tokens": request.llm_max_tokens,
                "llm_temperature": request.llm_temperature,
                "llm_top_p": request.llm_top_p
            }
        )
        
    except Exception as e:
        logger.error(f"Error configuring models: {e}")
        raise HTTPException(status_code=500, detail=f"Error configuring models: {str(e)}")

@router.post("/search", response_model=SearchResponse)
async def enhanced_search(request: SearchRequest):
    """Enhanced search with LLM-generated insights"""
    try:
        llm_manager = get_llm_manager()
        
        # Configure models if specified
        if request.llm_model or request.embedding_model:
            config = llm_manager.config
            if request.llm_model:
                config.llm_model = request.llm_model
            if request.embedding_model:
                config.embedding_model = request.embedding_model
            llm_manager.config = config
            llm_manager.embedding_manager.config = config
        
        # Perform search
        indexer = SemanticIndexer(
            persist_directory='data/chroma_db',
            model_name='all-MiniLM-L6-v2'
        )
        search_results = indexer.semantic_search(request.query, n_results=request.max_results)
        
        if not request.use_llm:
            return SearchResponse(
                enhanced=False,
                query=request.query,
                results=search_results,
                message="LLM enhancement disabled"
            )
        
        # Enhance with LLM
        enhanced_result = llm_manager.enhance_search_results(request.query, search_results)
        
        # Ensure all required fields are present
        if 'query' not in enhanced_result:
            enhanced_result['query'] = request.query
        
        return SearchResponse(**enhanced_result)
        
    except Exception as e:
        logger.error(f"Error in enhanced search: {e}")
        raise HTTPException(status_code=500, detail=f"Error in enhanced search: {str(e)}")

@router.post("/question", response_model=QuestionResponse)
async def answer_question(request: QuestionRequest):
    """Answer a specific question based on search results"""
    try:
        llm_manager = get_llm_manager()
        
        # Configure models if specified
        if request.llm_model or request.embedding_model:
            config = llm_manager.config
            if request.llm_model:
                config.llm_model = request.llm_model
            if request.embedding_model:
                config.embedding_model = request.embedding_model
            llm_manager.config = config
            llm_manager.embedding_manager.config = config
        
        # Perform search
        indexer = SemanticIndexer(
            persist_directory='data/chroma_db',
            model_name='all-MiniLM-L6-v2'
        )
        search_results = indexer.semantic_search(request.query, n_results=request.max_results)
        
        # Answer question
        answer_result = llm_manager.answer_question(request.question, search_results)
        
        return QuestionResponse(**answer_result)
        
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")

@router.post("/summary", response_model=SummaryResponse)
async def generate_summary(request: SummaryRequest):
    """Generate a summary of search results"""
    try:
        llm_manager = get_llm_manager()
        
        # Configure models if specified
        if request.llm_model or request.embedding_model:
            config = llm_manager.config
            if request.llm_model:
                config.llm_model = request.llm_model
            if request.embedding_model:
                config.embedding_model = request.embedding_model
            llm_manager.config = config
            llm_manager.embedding_manager.config = config
        
        # Perform search
        indexer = SemanticIndexer(
            persist_directory='data/chroma_db',
            model_name='all-MiniLM-L6-v2'
        )
        search_results = indexer.semantic_search(request.query, n_results=request.max_results)
        
        # Generate summary
        summary_result = llm_manager.generate_summary(search_results)
        
        return SummaryResponse(**summary_result)
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@router.get("/models/available")
async def get_available_models():
    """Get available LLM and embedding models"""
    try:
        return {
            "llm_models": [
                {"name": "phi3", "description": "Fast, efficient model good for reasoning"},
                {"name": "mistral", "description": "Powerful model for complex tasks"},
                {"name": "llama2", "description": "General purpose model"},
                {"name": "codellama", "description": "Code-focused model"}
            ],
            "embedding_models": [
                {"name": "bge-small-en", "description": "High quality English embeddings"},
                {"name": "nomic-embed-text", "description": "Good multilingual support"},
                {"name": "all-MiniLM-L6-v2", "description": "Fast general purpose embeddings"}
            ]
        }
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting available models: {str(e)}")

@router.get("/providers/available")
async def get_available_providers():
    """Get available LLM providers"""
    try:
        llm_manager = get_llm_manager()
        detected = llm_manager.detect_providers()
        
        providers = []
        for provider_name in detected:
            if provider_name == "ollama":
                provider_info = {
                    "name": "ollama",
                    "description": "Local LLM server with easy model management",
                    "url": "https://ollama.ai",
                    "models": ["phi3", "mistral", "llama2", "codellama"]
                }
                providers.append(provider_info)
        
        return {
            "detected_providers": detected,
            "providers": providers
        }
    except Exception as e:
        logger.error(f"Error getting available providers: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting available providers: {str(e)}")

@router.get("/performance/stats", response_model=PerformanceStatsResponse)
async def get_performance_stats():
    """Get LLM performance statistics"""
    try:
        llm_manager = get_llm_manager()
        stats = llm_manager.get_performance_stats()
        return PerformanceStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting performance stats: {str(e)}")

@router.post("/performance/clear")
async def clear_performance_stats():
    """Clear LLM performance statistics"""
    try:
        llm_manager = get_llm_manager()
        llm_manager.clear_performance_stats()
        return {"success": True, "message": "Performance statistics cleared"}
    except Exception as e:
        logger.error(f"Error clearing performance stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing performance stats: {str(e)}")

@router.post("/performance/optimize")
async def optimize_performance():
    """Apply performance optimizations to the current setup"""
    try:
        llm_manager = get_llm_manager()
        
        # Apply optimizations
        optimizations = []
        
        # Check if GPU is available and enable it
        if llm_manager.config.use_gpu:
            optimizations.append("GPU acceleration enabled")
        
        # Enable caching if not already enabled
        if not llm_manager.config.cache_responses:
            llm_manager.config.cache_responses = True
            optimizations.append("Response caching enabled")
        
        # Optimize concurrent requests
        if llm_manager.config.max_concurrent_requests < 8:
            llm_manager.config.max_concurrent_requests = 8
            optimizations.append("Concurrent requests increased to 8")
        
        # Update provider configurations
        for provider in llm_manager.providers.values():
            if hasattr(provider, '_configure_model_performance'):
                provider._configure_model_performance()
                optimizations.append(f"Model performance configured for {type(provider).__name__}")
        
        return {
            "success": True,
            "message": "Performance optimizations applied",
            "optimizations": optimizations
        }
        
    except Exception as e:
        logger.error(f"Error optimizing performance: {e}")
        raise HTTPException(status_code=500, detail=f"Error optimizing performance: {str(e)}") 