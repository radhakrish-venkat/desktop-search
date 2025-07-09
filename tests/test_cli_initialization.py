"""
Tests for CLI initialization commands
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from cli_commands.cli import cli


class TestCLIInitialization:
    """Test CLI initialization commands"""
    
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
            
            yield project_path
    
    @pytest.fixture
    def runner(self):
        """Create a Click test runner"""
        return CliRunner()
    
    def test_status_command_success(self, runner, temp_project):
        """Test status command with existing components"""
        with patch('pkg.utils.initialization.check_app_status') as mock_check:
            mock_check.return_value = {
                "certs": {"key_exists": True, "cert_exists": True},
                "database": {"data_dir_exists": True, "chroma_db_exists": True, "has_data": True},
                "api_keys": {"api_key_set": True, "jwt_secret_set": False},
                "directories": {"config_exists": True}
            }
            
            result = runner.invoke(cli, ['status'])
            
            assert result.exit_code == 0
            assert "✅ All components are ready!" in result.output
    
    def test_status_command_missing_components(self, runner, temp_project):
        """Test status command with missing components"""
        with patch('pkg.utils.initialization.check_app_status') as mock_check:
            mock_check.return_value = {
                "certs": {"key_exists": False, "cert_exists": False},
                "database": {"data_dir_exists": False, "chroma_db_exists": False, "has_data": False},
                "api_keys": {"api_key_set": False, "jwt_secret_set": False},
                "directories": {"config_exists": False}
            }
            
            result = runner.invoke(cli, ['status'])
            
            assert result.exit_code == 0
            assert "⚠️  Some components are missing or incomplete" in result.output
    
    def test_status_command_with_fix(self, runner, temp_project):
        """Test status command with --fix option"""
        with patch('pkg.utils.initialization.check_app_status') as mock_check:
            with patch('pkg.utils.initialization.initialize_app') as mock_init:
                mock_check.return_value = {
                    "certs": {"key_exists": False, "cert_exists": False},
                    "database": {"data_dir_exists": False, "chroma_db_exists": False, "has_data": False},
                    "api_keys": {"api_key_set": False, "jwt_secret_set": False},
                    "directories": {"config_exists": False}
                }
                mock_init.return_value = True
                
                result = runner.invoke(cli, ['status', '--fix'])
                
                assert result.exit_code == 0
                assert "🔧 Attempting to fix missing components..." in result.output
                assert "✅ Fixed successfully!" in result.output
                mock_init.assert_called_once()
    
    def test_status_command_with_reinitialize(self, runner, temp_project):
        """Test status command with --reinitialize option"""
        with patch('pkg.utils.initialization.check_app_status') as mock_check:
            with patch('pkg.utils.initialization.reinitialize_app') as mock_reinit:
                mock_check.return_value = {
                    "certs": {"key_exists": True, "cert_exists": True},
                    "database": {"data_dir_exists": True, "chroma_db_exists": True, "has_data": True},
                    "api_keys": {"api_key_set": True, "jwt_secret_set": True},
                    "directories": {"config_exists": True}
                }
                mock_reinit.return_value = True
                
                # Mock click.confirm to return True (user confirms)
                with patch('click.confirm', return_value=True):
                    result = runner.invoke(cli, ['status', '--reinitialize'])
                
                assert result.exit_code == 0
                assert "🔄 Reinitializing everything from scratch..." in result.output
                assert "✅ Reinitialization completed successfully!" in result.output
                mock_reinit.assert_called_once()
    
    def test_status_command_reinitialize_cancelled(self, runner, temp_project):
        """Test status command with --reinitialize option when user cancels"""
        with patch('pkg.utils.initialization.check_app_status') as mock_check:
            mock_check.return_value = {
                "certs": {"key_exists": True, "cert_exists": True},
                "database": {"data_dir_exists": True, "chroma_db_exists": True, "has_data": True},
                "api_keys": {"api_key_set": True, "jwt_secret_set": True},
                "directories": {"config_exists": True}
            }
            
            # Mock click.confirm to return False (user cancels)
            with patch('click.confirm', return_value=False):
                result = runner.invoke(cli, ['status', '--reinitialize'])
            
            assert result.exit_code == 1  # Abort exit code
            assert "❌ Reinitialization cancelled" in result.output
    
    def test_init_command_success(self, runner, temp_project):
        """Test init command success"""
        with patch('pkg.utils.initialization.initialize_app') as mock_init:
            mock_init.return_value = True
            
            result = runner.invoke(cli, ['init'])
            
            assert result.exit_code == 0
            assert "🚀 Initializing Desktop Search application..." in result.output
            assert "✅ Application initialized successfully!" in result.output
            mock_init.assert_called_once()
    
    def test_init_command_failure(self, runner, temp_project):
        """Test init command failure"""
        with patch('pkg.utils.initialization.initialize_app') as mock_init:
            mock_init.return_value = False
            
            result = runner.invoke(cli, ['init'])
            
            assert result.exit_code == 1  # Abort exit code
            assert "❌ Initialization failed!" in result.output
    
    def test_reinitialize_command_success(self, runner, temp_project):
        """Test reinitialize command success"""
        with patch('pkg.utils.initialization.reinitialize_app') as mock_reinit:
            mock_reinit.return_value = True
            
            # Mock click.confirm to return True (user confirms)
            with patch('click.confirm', return_value=True):
                result = runner.invoke(cli, ['reinitialize'])
            
            assert result.exit_code == 0
            assert "🔄 Reinitializing Desktop Search application from scratch..." in result.output
            assert "✅ Reinitialization completed successfully!" in result.output
            mock_reinit.assert_called_once()
    
    def test_reinitialize_command_with_force(self, runner, temp_project):
        """Test reinitialize command with --force option"""
        with patch('pkg.utils.initialization.reinitialize_app') as mock_reinit:
            mock_reinit.return_value = True
            
            result = runner.invoke(cli, ['reinitialize', '--force'])
            
            assert result.exit_code == 0
            assert "🔄 Reinitializing Desktop Search application from scratch..." in result.output
            assert "✅ Reinitialization completed successfully!" in result.output
            # Should not show confirmation prompt with --force
            assert "Are you sure you want to continue?" not in result.output
            mock_reinit.assert_called_once()
    
    def test_reinitialize_command_cancelled(self, runner, temp_project):
        """Test reinitialize command when user cancels"""
        with patch('pkg.utils.initialization.reinitialize_app') as mock_reinit:
            # Mock click.confirm to return False (user cancels)
            with patch('click.confirm', return_value=False):
                result = runner.invoke(cli, ['reinitialize'])
            
            assert result.exit_code == 1  # Abort exit code
            assert "❌ Reinitialization cancelled" in result.output
            mock_reinit.assert_not_called()
    
    def test_reinitialize_command_failure(self, runner, temp_project):
        """Test reinitialize command failure"""
        with patch('pkg.utils.initialization.reinitialize_app') as mock_reinit:
            mock_reinit.return_value = False
            
            # Mock click.confirm to return True (user confirms)
            with patch('click.confirm', return_value=True):
                result = runner.invoke(cli, ['reinitialize'])
            
            assert result.exit_code == 1  # Abort exit code
            assert "❌ Reinitialization failed!" in result.output
    
    def test_help_output(self, runner):
        """Test help output for initialization commands"""
        # Test main help
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "status" in result.output
        assert "init" in result.output
        assert "reinitialize" in result.output
        
        # Test status help
        result = runner.invoke(cli, ['status', '--help'])
        assert result.exit_code == 0
        assert "Check the status" in result.output
        assert "--fix" in result.output
        assert "--reinitialize" in result.output
        
        # Test init help
        result = runner.invoke(cli, ['init', '--help'])
        assert result.exit_code == 0
        assert "Initialize the Desktop Search application" in result.output
        
        # Test reinitialize help
        result = runner.invoke(cli, ['reinitialize', '--help'])
        assert result.exit_code == 0
        assert "Reinitialize the Desktop Search application from scratch" in result.output
        assert "--force" in result.output 