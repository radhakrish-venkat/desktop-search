"""
Tests for the initialization module
"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from pkg.utils.initialization import (
    AppInitializer, 
    initialize_app, 
    reinitialize_app, 
    check_app_status
)


class TestAppInitializer:
    """Test the AppInitializer class"""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir()
            
            # Create some existing files to test removal
            certs_dir = project_path / "certs"
            certs_dir.mkdir()
            (certs_dir / "key.pem").write_text("test key")
            (certs_dir / "cert.pem").write_text("test cert")
            
            data_dir = project_path / "data"
            data_dir.mkdir()
            chroma_db_dir = data_dir / "chroma_db"
            chroma_db_dir.mkdir()
            (chroma_db_dir / "test.db").write_text("test db")
            
            (data_dir / "directories.json").write_text('{"directories": []}')
            (data_dir / "index_metadata.json").write_text('{"test": "metadata"}')
            (data_dir / "index.pkl").write_text("test index")
            
            yield project_path
    
    def test_initializer_creation(self, temp_project):
        """Test AppInitializer creation with custom project root"""
        initializer = AppInitializer(str(temp_project))
        
        assert initializer.project_root == temp_project
        assert initializer.certs_dir == temp_project / "certs"
        assert initializer.data_dir == temp_project / "data"
        assert initializer.chroma_db_dir == temp_project / "data" / "chroma_db"
    
    def test_initializer_default_path(self):
        """Test AppInitializer creation with default project root"""
        initializer = AppInitializer()
        
        # Should use the path relative to the initialization.py file
        expected_path = Path(__file__).parent.parent / "pkg" / "utils" / "initialization.py"
        assert initializer.project_root == expected_path.parent.parent.parent
    
    def test_check_environment(self, temp_project):
        """Test environment status checking"""
        initializer = AppInitializer(str(temp_project))
        status = initializer.check_environment()
        
        assert status["certs"]["key_exists"] is True
        assert status["certs"]["cert_exists"] is True
        assert status["database"]["data_dir_exists"] is True
        assert status["database"]["chroma_db_exists"] is True
        assert status["database"]["has_data"] is True
        assert status["directories"]["config_exists"] is True
    
    def test_check_environment_empty(self):
        """Test environment status checking with empty project"""
        with tempfile.TemporaryDirectory() as temp_dir:
            initializer = AppInitializer(temp_dir)
            status = initializer.check_environment()
            
            assert status["certs"]["key_exists"] is False
            assert status["certs"]["cert_exists"] is False
            assert status["database"]["data_dir_exists"] is False
            assert status["database"]["chroma_db_exists"] is False
            assert status["database"]["has_data"] is False
            assert status["directories"]["config_exists"] is False
    
    @patch('subprocess.run')
    def test_check_and_create_certs_success(self, mock_run, temp_project):
        """Test successful certificate creation"""
        # Mock subprocess.run to actually create the files
        def mock_run_side_effect(*args, **kwargs):
            # Create the certs directory if it doesn't exist
            certs_dir = temp_project / "certs"
            certs_dir.mkdir(exist_ok=True)
            
            # Create the key and cert files
            if "genrsa" in args:
                (certs_dir / "key.pem").write_text("mocked private key")
            elif "req" in args:
                (certs_dir / "cert.pem").write_text("mocked certificate")
            
            return MagicMock()
        
        mock_run.side_effect = mock_run_side_effect
        
        initializer = AppInitializer(str(temp_project))
        
        # Remove existing certs first
        shutil.rmtree(initializer.certs_dir)
        
        result = initializer._check_and_create_certs()
        
        assert result is True
        assert (initializer.certs_dir / "key.pem").exists()
        assert (initializer.certs_dir / "cert.pem").exists()
        assert mock_run.call_count == 2  # genrsa and req commands
    
    @patch('subprocess.run')
    def test_check_and_create_certs_openssl_missing(self, mock_run, temp_project):
        """Test certificate creation when OpenSSL is missing"""
        mock_run.side_effect = FileNotFoundError()
        
        initializer = AppInitializer(str(temp_project))
        
        # Remove existing certs first
        shutil.rmtree(initializer.certs_dir)
        
        result = initializer._check_and_create_certs()
        
        assert result is False
    
    def test_check_and_create_database(self, temp_project):
        """Test database directory creation"""
        initializer = AppInitializer(str(temp_project))
        
        # Remove existing database
        shutil.rmtree(initializer.chroma_db_dir)
        
        result = initializer._check_and_create_database()
        
        assert result is True
        assert initializer.data_dir.exists()
        assert initializer.chroma_db_dir.exists()
    
    def test_check_and_create_directories(self, temp_project):
        """Test directories.json creation"""
        initializer = AppInitializer(str(temp_project))
        
        # Remove existing directories.json
        (initializer.data_dir / "directories.json").unlink()
        
        result = initializer._check_and_create_directories()
        
        assert result is True
        assert (initializer.data_dir / "directories.json").exists()
        
        # Check content
        content = (initializer.data_dir / "directories.json").read_text()
        assert '"directories": []' in content
    
    @patch('os.getenv')
    def test_check_and_create_api_keys(self, mock_getenv, temp_project):
        """Test API key checking"""
        mock_getenv.side_effect = lambda key, default="": {
            "API_KEY": "test_api_key",
            "JWT_SECRET_KEY": "test_jwt_secret"
        }.get(key, default)
        
        initializer = AppInitializer(str(temp_project))
        result = initializer._check_and_create_api_keys()
        
        assert result is True
    
    @patch('os.getenv')
    def test_check_and_create_api_keys_missing(self, mock_getenv, temp_project):
        """Test API key checking when keys are missing"""
        mock_getenv.return_value = ""
        
        initializer = AppInitializer(str(temp_project))
        result = initializer._check_and_create_api_keys()
        
        # Should still return True in development mode
        assert result is True
    
    @patch('subprocess.run')
    def test_initialize_all_success(self, mock_run, temp_project):
        """Test successful full initialization"""
        # Mock subprocess.run to actually create the files
        def mock_run_side_effect(*args, **kwargs):
            # Create the certs directory if it doesn't exist
            certs_dir = temp_project / "certs"
            certs_dir.mkdir(exist_ok=True)
            
            # Create the key and cert files
            if "genrsa" in args:
                (certs_dir / "key.pem").write_text("mocked private key")
            elif "req" in args:
                (certs_dir / "cert.pem").write_text("mocked certificate")
            
            return MagicMock()
        
        mock_run.side_effect = mock_run_side_effect
        
        # Remove all existing components
        shutil.rmtree(temp_project / "certs")
        shutil.rmtree(temp_project / "data")
        
        initializer = AppInitializer(str(temp_project))
        result = initializer.initialize_all()
        
        assert result is True
        assert (temp_project / "certs" / "key.pem").exists()
        assert (temp_project / "certs" / "cert.pem").exists()
        assert (temp_project / "data" / "chroma_db").exists()
        assert (temp_project / "data" / "directories.json").exists()
    
    def test_remove_existing_components(self, temp_project):
        """Test removal of existing components"""
        initializer = AppInitializer(str(temp_project))
        
        # Verify components exist before removal
        assert (temp_project / "certs" / "key.pem").exists()
        assert (temp_project / "data" / "chroma_db").exists()
        assert (temp_project / "data" / "directories.json").exists()
        
        result = initializer._remove_existing_components()
        
        assert result is True
        assert not (temp_project / "certs").exists()
        assert not (temp_project / "data" / "chroma_db").exists()
        assert not (temp_project / "data" / "directories.json").exists()
        assert not (temp_project / "data" / "index_metadata.json").exists()
        assert not (temp_project / "data" / "index.pkl").exists()
    
    @patch('subprocess.run')
    def test_reinitialize_all_success(self, mock_run, temp_project):
        """Test successful reinitialization"""
        # Mock subprocess.run to actually create the files
        def mock_run_side_effect(*args, **kwargs):
            # Create the certs directory if it doesn't exist
            certs_dir = temp_project / "certs"
            certs_dir.mkdir(exist_ok=True)
            
            # Create the key and cert files
            if "genrsa" in args:
                (certs_dir / "key.pem").write_text("mocked private key")
            elif "req" in args:
                (certs_dir / "cert.pem").write_text("mocked certificate")
            
            return MagicMock()
        
        mock_run.side_effect = mock_run_side_effect
        
        initializer = AppInitializer(str(temp_project))
        result = initializer.reinitialize_all()
        
        assert result is True
        
        # Verify components were recreated
        assert (temp_project / "certs" / "key.pem").exists()
        assert (temp_project / "certs" / "cert.pem").exists()
        assert (temp_project / "data" / "chroma_db").exists()
        assert (temp_project / "data" / "directories.json").exists()


class TestConvenienceFunctions:
    """Test the convenience functions"""
    
    def test_initialize_app(self):
        """Test initialize_app convenience function"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('subprocess.run') as mock_run:
                # Mock subprocess.run to actually create the files
                def mock_run_side_effect(*args, **kwargs):
                    # Create the certs directory if it doesn't exist
                    certs_dir = Path(temp_dir) / "certs"
                    certs_dir.mkdir(exist_ok=True)
                    
                    # Create the key and cert files
                    if "genrsa" in args:
                        (certs_dir / "key.pem").write_text("mocked private key")
                    elif "req" in args:
                        (certs_dir / "cert.pem").write_text("mocked certificate")
                    
                    return MagicMock()
                
                mock_run.side_effect = mock_run_side_effect
                
                result = initialize_app(temp_dir)
                assert result is True
    
    def test_reinitialize_app(self):
        """Test reinitialize_app convenience function"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_project = Path(temp_dir) / "test_project"
            test_project.mkdir()
            (test_project / "certs").mkdir()
            (test_project / "data").mkdir()
            
            with patch('subprocess.run') as mock_run:
                # Mock subprocess.run to actually create the files
                def mock_run_side_effect(*args, **kwargs):
                    # Create the certs directory if it doesn't exist
                    certs_dir = test_project / "certs"
                    certs_dir.mkdir(exist_ok=True)
                    
                    # Create the key and cert files
                    if "genrsa" in args:
                        (certs_dir / "key.pem").write_text("mocked private key")
                    elif "req" in args:
                        (certs_dir / "cert.pem").write_text("mocked certificate")
                    
                    return MagicMock()
                
                mock_run.side_effect = mock_run_side_effect
                
                result = reinitialize_app(str(test_project))
                assert result is True
    
    def test_check_app_status(self):
        """Test check_app_status convenience function"""
        with tempfile.TemporaryDirectory() as temp_dir:
            status = check_app_status(temp_dir)
            
            assert isinstance(status, dict)
            assert "certs" in status
            assert "database" in status
            assert "api_keys" in status
            assert "directories" in status


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_initialization_with_permission_error(self):
        """Test initialization when permission errors occur"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Make directory read-only to cause permission errors
            os.chmod(temp_dir, 0o444)
            
            initializer = AppInitializer(temp_dir)
            result = initializer.initialize_all()
            
            assert result is False
    
    def test_reinitialization_with_io_error(self):
        """Test reinitialization when IO errors occur"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_project = Path(temp_dir) / "test_project"
            test_project.mkdir()
            
            # Create a file that can't be deleted and put it in a location that will be removed
            protected_file = test_project / "certs" / "protected.txt"
            protected_file.parent.mkdir()
            protected_file.write_text("protected")
            os.chmod(protected_file, 0o444)
            
            initializer = AppInitializer(str(test_project))
            result = initializer.reinitialize_all()
            
            assert result is False 