import pytest
import os
import tempfile
from unittest.mock import Mock, patch

# Test Google Drive utilities
def test_google_drive_import():
    """Test that Google Drive modules can be imported."""
    try:
        from pkg.utils.google_drive import GoogleDriveClient, GOOGLE_DRIVE_AVAILABLE, setup_google_drive_credentials
        from pkg.indexer.google_drive import build_google_drive_index, merge_indices, search_google_drive
        assert True  # Import successful
    except ImportError as e:
        pytest.skip(f"Google Drive dependencies not available: {e}")

def test_google_drive_availability():
    """Test Google Drive availability check."""
    try:
        from pkg.utils.google_drive import GOOGLE_DRIVE_AVAILABLE
        # Should be False if dependencies are not installed
        assert isinstance(GOOGLE_DRIVE_AVAILABLE, bool)
    except ImportError:
        pytest.skip("Google Drive module not available")

def test_setup_credentials_function():
    """Test credentials setup function signature."""
    try:
        from pkg.utils.google_drive import setup_google_drive_credentials
        
        # Test with non-existent file
        result = setup_google_drive_credentials("/non/existent/path.json")
        assert isinstance(result, bool)
        
    except ImportError:
        pytest.skip("Google Drive module not available")

def test_merge_indices_function():
    """Test merge indices function with mock data."""
    try:
        from pkg.indexer.google_drive import merge_indices
        
        # Mock local index
        local_index = {
            'inverted_index': {'test': {'doc1'}, 'local': {'doc1'}},
            'document_store': {
                'doc1': {'filepath': '/local/file.txt', 'text': 'local content'}
            },
            'stats': {'total_files': 1, 'skipped_files': 0}
        }
        
        # Mock Google Drive index
        gdrive_index = {
            'inverted_index': {'test': {'doc2'}, 'gdrive': {'doc2'}},
            'document_store': {
                'doc2': {'filepath': 'gdrive://123', 'text': 'gdrive content'}
            },
            'stats': {'total_files': 1, 'skipped_files': 0}
        }
        
        # Test merge
        merged = merge_indices(local_index, gdrive_index)
        
        assert merged is not None
        assert 'inverted_index' in merged
        assert 'document_store' in merged
        assert 'stats' in merged
        assert merged['source'] == 'hybrid'
        
        # Check that both documents are included
        assert len(merged['document_store']) == 2
        assert 'doc1' in merged['document_store']
        assert 'doc2' in merged['document_store']
        
        # Check that tokens are merged
        assert 'test' in merged['inverted_index']
        assert len(merged['inverted_index']['test']) == 2  # Both doc1 and doc2
        
    except ImportError:
        pytest.skip("Google Drive module not available")

def test_merge_indices_with_empty():
    """Test merge indices with empty indices."""
    try:
        from pkg.indexer.google_drive import merge_indices
        
        # Test with None values
        result = merge_indices(None, None)
        assert result is None
        
        # Test with empty dict
        result = merge_indices({}, {})
        assert result is not None
        
    except ImportError:
        pytest.skip("Google Drive module not available")

@patch('pkg.utils.google_drive.GOOGLE_DRIVE_AVAILABLE', False)
def test_google_drive_unavailable():
    """Test behavior when Google Drive is not available."""
    try:
        from pkg.indexer.google_drive import build_google_drive_index, search_google_drive
        
        # Test that functions return None/empty when not available
        result = build_google_drive_index()
        assert result is None
        
        result = search_google_drive("test")
        assert result == []
        
    except ImportError:
        pytest.skip("Google Drive module not available")

def test_google_drive_client_initialization():
    """Test Google Drive client initialization (without actual auth)."""
    try:
        from pkg.utils.google_drive import GoogleDriveClient
        
        # This should raise an error since we don't have credentials
        with pytest.raises((FileNotFoundError, ImportError)):
            client = GoogleDriveClient()
            
    except ImportError:
        pytest.skip("Google Drive module not available")

if __name__ == '__main__':
    pytest.main([__file__]) 