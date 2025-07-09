"""
Searcher router for searching indexed documents
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import os
import time

# Import core functionality
from pkg.searcher.core import search_index
from pkg.indexer.semantic import SemanticIndexer
from pkg.indexer.semantic_hybrid import HybridSemanticIndexer
from pkg.indexer.google_drive import search_google_drive
from pkg.indexer.core import load_index

from api.models import (
    SearchRequest, SearchResponse, SearchResult, APIResponse
)
from api.config import settings

router = APIRouter()

def convert_result_types(result: dict) -> dict:
    """Convert result values to proper types for SearchResult"""
    score = result.get('score')
    if score is not None:
        try:
            score = float(score)
        except (ValueError, TypeError):
            score = None
    
    file_size = result.get('file_size')
    if file_size is not None:
        try:
            file_size = int(file_size)
        except (ValueError, TypeError):
            file_size = None
    
    return {
        'filepath': result.get('filepath', ''),
        'filename': os.path.basename(result.get('filepath', '')),
        'snippet': result.get('snippet', ''),
        'score': score,
        'file_type': result.get('file_type'),
        'file_size': file_size,
        'last_modified': result.get('last_modified')
    }

def get_default_index_path(directory: str) -> str:
    """Get the default index file path for a directory"""
    # Use data folder for all index files - everything in one organized location
    directory_name = os.path.basename(directory.rstrip('/'))
    return os.path.join(settings.DEFAULT_DATA_PATH, f"{directory_name}_index.pkl")

@router.post("/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest):
    """
    Search indexed documents (global index only)
    """
    try:
        start_time = time.time()
        # Determine search type and perform search
        if request.search_type.value == "semantic":
            indexer = SemanticIndexer(
                persist_directory=settings.DEFAULT_CHROMA_DB_PATH,
                model_name=settings.DEFAULT_MODEL
            )
            results = indexer.semantic_search(
                query=request.query,
                n_results=request.limit,
                threshold=request.threshold
            )
            search_results = [SearchResult(**convert_result_types(result)) for result in results]
        elif request.search_type.value == "hybrid":
            indexer = HybridSemanticIndexer(
                persist_directory=settings.DEFAULT_CHROMA_DB_PATH,
                model_name=settings.DEFAULT_MODEL
            )
            results = indexer.hybrid_search(
                query=request.query,
                n_results=request.limit,
                semantic_weight=0.7
            )
            search_results = [SearchResult(**convert_result_types(result)) for result in results]
        else:
            # Keyword search using ChromaDB
            indexer = SemanticIndexer(
                persist_directory=settings.DEFAULT_CHROMA_DB_PATH,
                model_name=settings.DEFAULT_MODEL
            )
            results = indexer.keyword_search(
                query=request.query,
                n_results=request.limit
            )
            search_results = [SearchResult(**convert_result_types(result)) for result in results]
        end_time = time.time()
        search_time_ms = (end_time - start_time) * 1000
        return SearchResponse(
            query=request.query,
            search_type=request.search_type,
            results=search_results,
            total_results=len(search_results),
            search_time_ms=search_time_ms
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/gdrive", response_model=SearchResponse)
async def search_gdrive_endpoint(request: SearchRequest):
    """
    Search Google Drive files
    """
    try:
        start_time = time.time()
        
        # Search Google Drive
        raw_results = search_google_drive(
            query=request.query,
            folder_id=None,  # Could be added to request model
            limit=request.limit
        )
        
        # Convert results to SearchResult format
        search_results = []
        for result in raw_results:
            search_results.append(SearchResult(
                filepath=result.get('filepath', ''),
                filename=result.get('filename', ''),
                snippet=result.get('snippet', ''),
                score=result.get('score'),
                file_type=result.get('file_type'),
                file_size=result.get('file_size'),
                last_modified=result.get('last_modified')
            ))
        
        end_time = time.time()
        search_time_ms = (end_time - start_time) * 1000
        
        return SearchResponse(
            query=request.query,
            search_type=request.search_type,
            results=search_results,
            total_results=len(search_results),
            search_time_ms=search_time_ms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Drive search failed: {str(e)}")

@router.get("/suggestions", response_model=APIResponse)
async def get_search_suggestions(query: str, limit: int = 5):
    """
    Get search suggestions based on partial query
    """
    try:
        # This is a placeholder - in a real implementation, you'd want to
        # build suggestions based on indexed content
        suggestions = [
            f"{query} document",
            f"{query} file",
            f"{query} report",
            f"{query} analysis",
            f"{query} data"
        ][:limit]
        
        return APIResponse(
            success=True,
            message="Search suggestions retrieved",
            data={"suggestions": suggestions}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}") 