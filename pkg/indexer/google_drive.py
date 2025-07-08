import os
import logging
from typing import Dict, Set, List, Optional, Any
from collections import defaultdict

from pkg.utils.google_drive import GoogleDriveClient, GOOGLE_DRIVE_AVAILABLE

logger = logging.getLogger(__name__)

def build_google_drive_index(folder_id: Optional[str] = None, query: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Builds an index from Google Drive files.
    
    Args:
        folder_id: ID of the Google Drive folder to index (None for root)
        query: Additional query to filter files
        
    Returns:
        Dictionary containing inverted_index, document_store, and metadata,
        or None if an error occurs
    """
    if not GOOGLE_DRIVE_AVAILABLE:
        logger.error("Google Drive API not available")
        return None
    
    try:
        client = GoogleDriveClient()
        files = client.list_files(folder_id=folder_id, query=query)
        
        inverted_index: Dict[str, Set[str]] = defaultdict(set)
        document_store: Dict[str, Dict[str, str]] = {}
        doc_id_counter = 0
        processed_files = 0
        skipped_files = 0
        
        logger.info(f"Starting to index Google Drive files (folder_id: {folder_id})")
        
        for file_info in files:
            file_id = file_info.get('id')
            file_name = file_info.get('name', 'Unknown')
            mime_type = file_info.get('mimeType', '')
            file_size = file_info.get('size', '0')
            modified_time = file_info.get('modifiedTime', '')
            
            try:
                # Get file content
                content = client.get_file_content(file_id)
                
                if content and content.strip():
                    doc_id = f"gdrive_{doc_id_counter}"
                    document_store[doc_id] = {
                        'filepath': f"gdrive://{file_id}",
                        'filename': file_name,
                        'text': content,
                        'mime_type': mime_type,
                        'size': file_size,
                        'modified_time': modified_time,
                        'source': 'google_drive'
                    }
                    doc_id_counter += 1
                    
                    # Tokenize the text (using the same tokenization as local files)
                    from pkg.indexer.core import _tokenize_text
                    tokens = _tokenize_text(content)
                    
                    # Add tokens to inverted index
                    for token in tokens:
                        inverted_index[token].add(doc_id)
                    
                    processed_files += 1
                    
                    if processed_files % 50 == 0:
                        logger.info(f"Processed {processed_files} Google Drive files...")
                        
                else:
                    skipped_files += 1
                    logger.debug(f"Skipped file with no content: {file_name}")
                    
            except Exception as e:
                logger.warning(f"Error processing Google Drive file {file_name}: {e}")
                skipped_files += 1
                continue
        
        logger.info(f"Google Drive indexing complete. Processed {processed_files} files, skipped {skipped_files} files.")
        
        return {
            'inverted_index': dict(inverted_index),
            'document_store': document_store,
            'source': 'google_drive',
            'folder_id': folder_id,
            'query': query,
            'stats': {
                'total_files': processed_files,
                'skipped_files': skipped_files,
                'unique_tokens': len(inverted_index),
                'total_documents': len(document_store)
            }
        }
        
    except Exception as e:
        logger.error(f"Error building Google Drive index: {e}")
        return None


def merge_indices(local_index: Dict[str, Any], gdrive_index: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges a local file index with a Google Drive index.
    
    Args:
        local_index: Index data from local files
        gdrive_index: Index data from Google Drive files
        
    Returns:
        Merged index data
    """
    if not local_index or not gdrive_index:
        logger.warning("Cannot merge indices: one or both indices are empty")
        return local_index or gdrive_index
    
    merged_inverted_index = defaultdict(set)
    merged_document_store = {}
    
    # Merge inverted indices
    for token, doc_ids in local_index.get('inverted_index', {}).items():
        merged_inverted_index[token].update(doc_ids)
    
    for token, doc_ids in gdrive_index.get('inverted_index', {}).items():
        merged_inverted_index[token].update(doc_ids)
    
    # Merge document stores
    merged_document_store.update(local_index.get('document_store', {}))
    merged_document_store.update(gdrive_index.get('document_store', {}))
    
    # Merge stats
    local_stats = local_index.get('stats', {})
    gdrive_stats = gdrive_index.get('stats', {})
    
    merged_stats = {
        'total_files': local_stats.get('total_files', 0) + gdrive_stats.get('total_files', 0),
        'skipped_files': local_stats.get('skipped_files', 0) + gdrive_stats.get('skipped_files', 0),
        'unique_tokens': len(merged_inverted_index),
        'total_documents': len(merged_document_store),
        'local_files': local_stats.get('total_files', 0),
        'gdrive_files': gdrive_stats.get('total_files', 0)
    }
    
    return {
        'inverted_index': dict(merged_inverted_index),
        'document_store': merged_document_store,
        'source': 'hybrid',
        'local_directory': local_index.get('indexed_directory'),
        'gdrive_folder_id': gdrive_index.get('folder_id'),
        'stats': merged_stats
    }


def search_google_drive(query: str, folder_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search Google Drive files directly using Google Drive API.
    
    Args:
        query: Search query
        folder_id: ID of the folder to search in (None for all)
        limit: Maximum number of results
        
    Returns:
        List of search results
    """
    if not GOOGLE_DRIVE_AVAILABLE:
        logger.error("Google Drive API not available")
        return []
    
    try:
        client = GoogleDriveClient()
        matching_files = client.search_files(query, folder_id)
        
        results = []
        for file_info in matching_files[:limit]:
            file_id = file_info.get('id')
            file_name = file_info.get('name', 'Unknown')
            
            # Get file content for snippet
            content = client.get_file_content(file_id)
            if content:
                # Create a simple snippet (first 200 characters)
                snippet = content[:200] + "..." if len(content) > 200 else content
                
                results.append({
                    'filepath': f"gdrive://{file_id}",
                    'filename': file_name,
                    'snippet': snippet,
                    'source': 'google_drive',
                    'mime_type': file_info.get('mimeType', ''),
                    'size': file_info.get('size', '0'),
                    'modified_time': file_info.get('modifiedTime', '')
                })
        
        logger.info(f"Found {len(results)} Google Drive files matching query: {query}")
        return results
        
    except Exception as e:
        logger.error(f"Error searching Google Drive: {e}")
        return [] 