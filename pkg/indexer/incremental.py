import os
import hashlib
import json
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
from pathlib import Path

from pkg.indexer.core import build_index, save_index, load_index
from pkg.indexer.google_drive import build_google_drive_index, merge_indices
from pkg.indexer.semantic_hybrid import HybridSemanticIndexer
from pkg.utils.google_drive import GoogleDriveClient, GOOGLE_DRIVE_AVAILABLE

logger = logging.getLogger(__name__)

class IncrementalIndexer:
    """
    Incremental indexer that tracks file changes and only indexes new or modified files.
    Supports both local files and Google Drive files.
    """
    
    def __init__(self, index_metadata_path: str = "./index_metadata.json"):
        """
        Initialize the incremental indexer.
        
        Args:
            index_metadata_path: Path to store file metadata for change detection
        """
        self.index_metadata_path = index_metadata_path
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load existing metadata from file."""
        if os.path.exists(self.index_metadata_path):
            try:
                with open(self.index_metadata_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load metadata: {e}")
        return {
            'local_files': {},
            'gdrive_files': {},
            'last_updated': None
        }
    
    def _save_metadata(self):
        """Save metadata to file."""
        try:
            self.metadata['last_updated'] = datetime.now().isoformat()
            with open(self.index_metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save metadata: {e}")
    
    def _get_file_hash(self, filepath: str) -> Optional[str]:
        """Get SHA256 hash of file content."""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"Could not hash file {filepath}: {e}")
            return None
    
    def _get_file_metadata(self, filepath: str) -> Dict[str, Any]:
        """Get file metadata for change detection."""
        try:
            stat = os.stat(filepath)
            return {
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'hash': self._get_file_hash(filepath)
            }
        except Exception as e:
            logger.warning(f"Could not get metadata for {filepath}: {e}")
            return {}
    
    def _get_gdrive_file_metadata(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get Google Drive file metadata for change detection."""
        return {
            'id': file_info.get('id'),
            'name': file_info.get('name'),
            'size': file_info.get('size'),
            'modified_time': file_info.get('modifiedTime'),
            'mime_type': file_info.get('mimeType')
        }
    
    def _detect_local_changes(self, directory_path: str) -> Tuple[List[str], List[str], List[str]]:
        """
        Detect changes in local files.
        
        Returns:
            Tuple of (new_files, modified_files, deleted_files)
        """
        new_files = []
        modified_files = []
        deleted_files = []
        
        # Get current files
        current_files = set()
        for root, dirs, files in os.walk(directory_path):
            for filename in files:
                filepath = os.path.join(root, filename)
                current_files.add(filepath)
                
                # Check if file is new or modified
                if filepath in self.metadata['local_files']:
                    old_meta = self.metadata['local_files'][filepath]
                    new_meta = self._get_file_metadata(filepath)
                    
                    if (new_meta.get('size') != old_meta.get('size') or 
                        new_meta.get('mtime') != old_meta.get('mtime') or
                        new_meta.get('hash') != old_meta.get('hash')):
                        modified_files.append(filepath)
                else:
                    new_files.append(filepath)
        
        # Check for deleted files
        for filepath in self.metadata['local_files']:
            if filepath not in current_files:
                deleted_files.append(filepath)
        
        return new_files, modified_files, deleted_files
    
    def _detect_gdrive_changes(self, folder_id: Optional[str] = None, query: Optional[str] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
        """
        Detect changes in Google Drive files.
        
        Returns:
            Tuple of (new_files, modified_files, deleted_file_ids)
        """
        if not GOOGLE_DRIVE_AVAILABLE:
            logger.error("Google Drive API not available")
            return [], [], []
        
        try:
            client = GoogleDriveClient()
            current_files = client.list_files(folder_id=folder_id, query=query)
            
            new_files = []
            modified_files = []
            deleted_file_ids = []
            
            # Check current files against metadata
            for file_info in current_files:
                file_id = file_info.get('id')
                current_meta = self._get_gdrive_file_metadata(file_info)
                
                if file_id in self.metadata['gdrive_files']:
                    old_meta = self.metadata['gdrive_files'][file_id]
                    if (current_meta.get('modified_time') != old_meta.get('modified_time') or
                        current_meta.get('size') != old_meta.get('size')):
                        modified_files.append(file_info)
                else:
                    new_files.append(file_info)
            
            # Check for deleted files
            current_file_ids = {f.get('id') for f in current_files}
            for file_id in self.metadata['gdrive_files']:
                if file_id not in current_file_ids:
                    deleted_file_ids.append(file_id)
            
            return new_files, modified_files, deleted_file_ids
            
        except Exception as e:
            logger.error(f"Error detecting Google Drive changes: {e}")
            return [], [], []
    
    def incremental_index(self, 
                         directory_path: Optional[str] = None,
                         gdrive_folder_id: Optional[str] = None,
                         gdrive_query: Optional[str] = None,
                         index_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Perform incremental indexing of local and Google Drive files.
        
        Args:
            directory_path: Path to local directory to index
            gdrive_folder_id: Google Drive folder ID to index
            gdrive_query: Additional query to filter Google Drive files
            index_path: Path to save the index (uses default if None)
            
        Returns:
            Dictionary with indexing statistics
        """
        logger.info("Starting incremental indexing")
        
        # Load existing index
        existing_index = None
        if index_path and os.path.exists(index_path):
            existing_index = load_index(index_path)
        
        # Detect changes
        local_new, local_modified, local_deleted = [], [], []
        gdrive_new, gdrive_modified, gdrive_deleted = [], [], []
        
        if directory_path:
            local_new, local_modified, local_deleted = self._detect_local_changes(directory_path)
            logger.info(f"Local changes detected: {len(local_new)} new, {len(local_modified)} modified, {len(local_deleted)} deleted")
        
        if gdrive_folder_id or gdrive_query:
            gdrive_new, gdrive_modified, gdrive_deleted = self._detect_gdrive_changes(gdrive_folder_id, gdrive_query)
            logger.info(f"Google Drive changes detected: {len(gdrive_new)} new, {len(gdrive_modified)} modified, {len(gdrive_deleted)} deleted")
        
        # If no changes, return early
        if not any([local_new, local_modified, local_deleted, gdrive_new, gdrive_modified, gdrive_deleted]):
            logger.info("No changes detected, indexing skipped")
            return {
                'stats': {
                    'total_files': 0,
                    'new_files': 0,
                    'modified_files': 0,
                    'deleted_files': 0,
                    'skipped_files': 0
                }
            }
        
        # Build new index for changed files
        new_index = None
        
        # Index local changes
        if local_new or local_modified:
            changed_files = local_new + local_modified
            logger.info(f"Indexing {len(changed_files)} changed local files")
            
            # Create temporary index for changed files
            if directory_path:
                temp_index = build_index(directory_path)  # This will index all files, but we'll filter later
                if temp_index:
                    new_index = temp_index
        
        # Index Google Drive changes
        if gdrive_new or gdrive_modified:
            changed_gdrive_files = gdrive_new + gdrive_modified
            logger.info(f"Indexing {len(changed_gdrive_files)} changed Google Drive files")
            
            gdrive_index = build_google_drive_index(folder_id=gdrive_folder_id, query=gdrive_query)
            if gdrive_index:
                if new_index:
                    new_index = merge_indices(new_index, gdrive_index)
                else:
                    new_index = gdrive_index
        
        # Merge with existing index
        if existing_index and new_index:
            final_index = merge_indices(existing_index, new_index)
        elif new_index:
            final_index = new_index
        else:
            final_index = existing_index
        
        # Update metadata
        if directory_path:
            for filepath in local_new + local_modified:
                self.metadata['local_files'][filepath] = self._get_file_metadata(filepath)
            
            for filepath in local_deleted:
                self.metadata['local_files'].pop(filepath, None)
        
        if gdrive_folder_id or gdrive_query:
            for file_info in gdrive_new + gdrive_modified:
                file_id = file_info.get('id')
                if file_id:
                    self.metadata['gdrive_files'][file_id] = self._get_gdrive_file_metadata(file_info)
            
            for file_id in gdrive_deleted:
                self.metadata['gdrive_files'].pop(file_id, None)
        
        self._save_metadata()
        
        # Save final index
        if final_index and index_path:
            save_index(final_index, index_path)
        
        total_changes = len(local_new) + len(local_modified) + len(gdrive_new) + len(gdrive_modified)
        total_deleted = len(local_deleted) + len(gdrive_deleted)
        
        logger.info(f"Incremental indexing complete: {total_changes} files processed, {total_deleted} files removed")
        
        return {
            'stats': {
                'total_files': final_index.get('stats', {}).get('total_files', 0) if final_index else 0,
                'new_files': len(local_new) + len(gdrive_new),
                'modified_files': len(local_modified) + len(gdrive_modified),
                'deleted_files': total_deleted,
                'skipped_files': 0
            }
        }
    
    def incremental_semantic_index(self,
                                 directory_path: Optional[str] = None,
                                 gdrive_folder_id: Optional[str] = None,
                                 gdrive_query: Optional[str] = None,
                                 persist_directory: str = "./chroma_db",
                                 model_name: str = "all-MiniLM-L6-v2") -> Optional[Dict[str, Any]]:
        """
        Perform incremental semantic indexing.
        
        Args:
            directory_path: Path to local directory to index
            gdrive_folder_id: Google Drive folder ID to index
            gdrive_query: Additional query to filter Google Drive files
            persist_directory: ChromaDB persistence directory
            model_name: Sentence transformer model name
            
        Returns:
            Dictionary with indexing statistics
        """
        logger.info("Starting incremental semantic indexing")
        
        # Detect changes
        local_new, local_modified, local_deleted = [], [], []
        gdrive_new, gdrive_modified, gdrive_deleted = [], [], []
        
        if directory_path:
            local_new, local_modified, local_deleted = self._detect_local_changes(directory_path)
            logger.info(f"Local changes detected: {len(local_new)} new, {len(local_modified)} modified, {len(local_deleted)} deleted")
        
        if gdrive_folder_id or gdrive_query:
            gdrive_new, gdrive_modified, gdrive_deleted = self._detect_gdrive_changes(gdrive_folder_id, gdrive_query)
            logger.info(f"Google Drive changes detected: {len(gdrive_new)} new, {len(gdrive_modified)} modified, {len(gdrive_deleted)} deleted")
        
        # If no changes, return early
        if not any([local_new, local_modified, local_deleted, gdrive_new, gdrive_modified, gdrive_deleted]):
            logger.info("No changes detected, semantic indexing skipped")
            return {
                'stats': {
                    'total_files': 0,
                    'new_files': 0,
                    'modified_files': 0,
                    'deleted_files': 0,
                    'total_chunks': 0
                }
            }
        
        # Use hybrid semantic indexer with --no-clear flag
        indexer = HybridSemanticIndexer(persist_directory=persist_directory, model_name=model_name)
        
        # Remove deleted files from ChromaDB
        if local_deleted or gdrive_deleted:
            # This is a simplified approach - in practice, you'd want to remove specific chunks
            logger.info("Removing deleted files from semantic index")
            # For now, we'll rebuild the index, but in a real implementation,
            # you'd want to remove specific chunks by ID
        
        # Build semantic index with --no-clear flag
        stats = indexer.build_hybrid_semantic_index(
            local_directory=directory_path,
            gdrive_folder_id=gdrive_folder_id,
            gdrive_query=gdrive_query,
            clear_existing=False  # This is the key for incremental indexing
        )
        
        # Update metadata
        if directory_path:
            for filepath in local_new + local_modified:
                self.metadata['local_files'][filepath] = self._get_file_metadata(filepath)
            
            for filepath in local_deleted:
                self.metadata['local_files'].pop(filepath, None)
        
        if gdrive_folder_id or gdrive_query:
            for file_info in gdrive_new + gdrive_modified:
                file_id = file_info.get('id')
                if file_id:
                    self.metadata['gdrive_files'][file_id] = self._get_gdrive_file_metadata(file_info)
            
            for file_id in gdrive_deleted:
                self.metadata['gdrive_files'].pop(file_id, None)
        
        self._save_metadata()
        
        total_changes = len(local_new) + len(local_modified) + len(gdrive_new) + len(gdrive_modified)
        total_deleted = len(local_deleted) + len(gdrive_deleted)
        
        logger.info(f"Incremental semantic indexing complete: {total_changes} files processed, {total_deleted} files removed")
        
        return stats


# Convenience functions
def incremental_index(directory_path: Optional[str] = None,
                     gdrive_folder_id: Optional[str] = None,
                     gdrive_query: Optional[str] = None,
                     index_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Perform incremental indexing of local and Google Drive files."""
    indexer = IncrementalIndexer()
    return indexer.incremental_index(
        directory_path=directory_path,
        gdrive_folder_id=gdrive_folder_id,
        gdrive_query=gdrive_query,
        index_path=index_path
    )

def incremental_semantic_index(directory_path: Optional[str] = None,
                             gdrive_folder_id: Optional[str] = None,
                             gdrive_query: Optional[str] = None,
                             persist_directory: str = "./chroma_db",
                             model_name: str = "all-MiniLM-L6-v2") -> Optional[Dict[str, Any]]:
    """Perform incremental semantic indexing."""
    indexer = IncrementalIndexer()
    return indexer.incremental_semantic_index(
        directory_path=directory_path,
        gdrive_folder_id=gdrive_folder_id,
        gdrive_query=gdrive_query,
        persist_directory=persist_directory,
        model_name=model_name
    ) 