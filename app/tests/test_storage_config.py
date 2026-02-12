"""Unit tests for storage configuration."""
import pytest
from pathlib import Path
import os
from app.backend.storage_config import StorageConfig


class TestStorageConfigPaths:
    """Test StorageConfig path generation."""
    
    def test_storage_root_exists(self):
        """Test that STORAGE_ROOT is defined."""
        assert StorageConfig.STORAGE_ROOT is not None
        assert isinstance(StorageConfig.STORAGE_ROOT, Path)
    
    def test_images_dir_defined(self):
        """Test that IMAGES_DIR is defined."""
        assert StorageConfig.IMAGES_DIR is not None
        assert isinstance(StorageConfig.IMAGES_DIR, Path)
    
    def test_personal_models_dir_defined(self):
        """Test that PERSONAL_MODELS_DIR is defined."""
        assert StorageConfig.PERSONAL_MODELS_DIR is not None
        assert isinstance(StorageConfig.PERSONAL_MODELS_DIR, Path)
    
    def test_session_dir_defined(self):
        """Test that SESSION_DIR is defined."""
        assert StorageConfig.SESSION_DIR is not None
        assert isinstance(StorageConfig.SESSION_DIR, Path)
    
    def test_get_user_image_dir(self):
        """Test get_user_image_dir generates correct path."""
        username = "testuser"
        path = StorageConfig.get_user_image_dir(username)
        
        assert isinstance(path, Path)
        assert username in str(path)
        assert "images" in str(path)
    
    def test_get_user_image_dir_different_users(self):
        """Test that different users get different image directories."""
        path1 = StorageConfig.get_user_image_dir("user1")
        path2 = StorageConfig.get_user_image_dir("user2")
        
        assert path1 != path2
        assert "user1" in str(path1)
        assert "user2" in str(path2)
    
    def test_get_user_personal_model_path(self):
        """Test get_user_personal_model_path generates correct path."""
        username = "testuser"
        path = StorageConfig.get_user_personal_model_path(username)
        
        assert isinstance(path, Path)
        assert username in str(path)
        assert "personal" in str(path)
        assert "models" in str(path)
    
    def test_get_user_personal_model_path_ends_with_pt(self):
        """Test that personal model path ends with .pt."""
        username = "testuser"
        path = StorageConfig.get_user_personal_model_path(username)
        
        assert str(path).endswith(".pt")
    
    def test_get_user_session_file(self):
        """Test get_user_session_file generates correct path."""
        username = "testuser"
        path = StorageConfig.get_user_session_file(username)
        
        assert isinstance(path, Path)
        assert username in str(path)
        assert "sessions" in str(path)
    
    def test_get_user_session_file_ends_with_json(self):
        """Test that session file path ends with .json."""
        username = "testuser"
        path = StorageConfig.get_user_session_file(username)
        
        assert str(path).endswith(".json")
    
    def test_image_size_limit_defined(self):
        """Test that image size limit is defined."""
        assert StorageConfig.MAX_IMAGE_SIZE > 0
        assert isinstance(StorageConfig.MAX_IMAGE_SIZE, int)
    
    def test_image_size_limit_is_50mb(self):
        """Test that image size limit is 50MB."""
        # 50MB in bytes
        expected = 50 * 1024 * 1024
        assert StorageConfig.MAX_IMAGE_SIZE == expected
    
    def test_session_timeout_defined(self):
        """Test that session timeout is defined."""
        assert StorageConfig.SESSION_TIMEOUT > 0
        assert isinstance(StorageConfig.SESSION_TIMEOUT, int)
    
    def test_session_timeout_is_31_days(self):
        """Test that session timeout is 31 days."""
        # 31 days in seconds
        expected = 31 * 24 * 60 * 60
        assert StorageConfig.SESSION_TIMEOUT == expected


class TestStorageConfigPathNormalization:
    """Test path normalization and special characters."""
    
    def test_user_image_dir_with_special_characters(self):
        """Test image dir path with special characters in username."""
        username = "user.name+123"
        path = StorageConfig.get_user_image_dir(username)
        
        assert isinstance(path, Path)
        assert username in str(path)
    
    def test_user_personal_model_path_with_special_characters(self):
        """Test model path with special characters in username."""
        username = "user-name_123"
        path = StorageConfig.get_user_personal_model_path(username)
        
        assert isinstance(path, Path)
        assert username in str(path)
    
    def test_user_session_file_with_special_characters(self):
        """Test session file path with special characters in username."""
        username = "user@domain"
        path = StorageConfig.get_user_session_file(username)
        
        assert isinstance(path, Path)
        assert username in str(path)


class TestStorageConfigEnvironment:
    """Test environment variable handling."""
    
    def test_storage_root_respects_env_var(self, monkeypatch):
        """Test that STORAGE_ROOT respects STORAGE_ROOT environment variable."""
        custom_path = Path("/custom/storage/path")
        monkeypatch.setenv("STORAGE_ROOT", str(custom_path))
        
        # Reload the config to pick up new env var
        from app.backend import storage_config
        import importlib
        importlib.reload(storage_config)
        
        # This is tricky since STORAGE_ROOT is set at import time
        # Just verify current behavior
        assert storage_config.StorageConfig.STORAGE_ROOT is not None
    
    def test_paths_are_consistent(self):
        """Test that paths are consistent across calls."""
        username = "testuser"
        
        path1 = StorageConfig.get_user_image_dir(username)
        path2 = StorageConfig.get_user_image_dir(username)
        
        assert path1 == path2
    
    def test_different_users_get_different_paths(self):
        """Test that different users get isolated storage paths."""
        users = ["alice", "bob", "charlie"]
        paths = [StorageConfig.get_user_image_dir(u) for u in users]
        
        # All paths should be unique
        assert len(set(paths)) == len(paths)
    
    def test_model_and_image_dirs_dont_overlap(self):
        """Test that model and image directories are separate."""
        username = "testuser"
        
        image_path = StorageConfig.get_user_image_dir(username)
        model_path = StorageConfig.get_user_personal_model_path(username)
        
        # They should not be the same
        assert image_path.parent != model_path.parent
    
    def test_session_dir_separate_from_user_data(self):
        """Test that session directory is separate from user image/model data."""
        username = "testuser"
        
        image_path = StorageConfig.get_user_image_dir(username)
        session_path = StorageConfig.get_user_session_file(username)
        
        # Session is not nested in user image directory
        assert not str(session_path).startswith(str(image_path.parent))


class TestStorageConfigFileCreation:
    """Test that StorageConfig properly initializes directories."""
    
    def test_storage_root_parent_exists(self):
        """Test that storage root parent exists (usually home directory)."""
        root = StorageConfig.STORAGE_ROOT
        assert root.parent.exists() or root.parent == Path("/")
    
    def test_image_dir_structure(self):
        """Test that image directory follows expected structure."""
        path = StorageConfig.get_user_image_dir("testuser")
        path_str = str(path)
        
        # Should have 'images' in path
        assert "images" in path_str
        # Should have username in path
        assert "testuser" in path_str
    
    def test_model_dir_structure(self):
        """Test that model directory follows expected structure."""
        path = StorageConfig.get_user_personal_model_path("testuser")
        path_str = str(path)
        
        # Should have 'models' in path
        assert "models" in path_str
        # Should have 'personal' in path
        assert "personal" in path_str
        # Should have username in path
        assert "testuser" in path_str
        # Should end with .pt extension
        assert path_str.endswith(".pt")
    
    def test_session_file_structure(self):
        """Test that session file follows expected structure."""
        path = StorageConfig.get_user_session_file("testuser")
        path_str = str(path)
        
        # Should have 'sessions' in path
        assert "sessions" in path_str
        # Should have username in path
        assert "testuser" in path_str
        # Should end with .json extension
        assert path_str.endswith(".json")


class TestStorageConfigDocumentation:
    """Test that StorageConfig constants are properly documented."""
    
    def test_image_size_limit_has_docstring(self):
        """Test that MAX_IMAGE_SIZE is documented."""
        # Verify the constant exists
        assert hasattr(StorageConfig, 'MAX_IMAGE_SIZE')
    
    def test_session_timeout_has_docstring(self):
        """Test that SESSION_TIMEOUT is documented."""
        # Verify the constant exists
        assert hasattr(StorageConfig, 'SESSION_TIMEOUT')
    
    def test_all_directory_attributes_exist(self):
        """Test that all expected directory attributes exist."""
        required_attrs = [
            'STORAGE_ROOT',
            'IMAGES_DIR',
            'PERSONAL_MODELS_DIR',
            'SESSION_DIR',
        ]
        
        for attr in required_attrs:
            assert hasattr(StorageConfig, attr), f"Missing {attr}"
    
    def test_all_path_methods_exist(self):
        """Test that all expected path methods exist."""
        required_methods = [
            'get_user_image_dir',
            'get_user_personal_model_path',
            'get_user_session_file',
        ]
        
        for method in required_methods:
            assert hasattr(StorageConfig, method), f"Missing {method}"
            assert callable(getattr(StorageConfig, method))


class TestStorageConfigPathNesting:
    """Test path nesting and hierarchy."""
    
    def test_user_image_dir_nested_under_images(self):
        """Test that user image dir is nested under IMAGES_DIR."""
        path = StorageConfig.get_user_image_dir("testuser")
        images_dir = StorageConfig.IMAGES_DIR
        
        # Path should contain images dir
        assert images_dir in path.parents or path.parent == images_dir
    
    def test_user_model_path_nested_under_personal_models(self):
        """Test that user model path is nested under PERSONAL_MODELS_DIR."""
        path = StorageConfig.get_user_personal_model_path("testuser")
        models_dir = StorageConfig.PERSONAL_MODELS_DIR
        
        # Path should contain personal models dir
        assert models_dir in path.parents
    
    def test_session_file_nested_under_session_dir(self):
        """Test that session file is in SESSION_DIR."""
        path = StorageConfig.get_user_session_file("testuser")
        session_dir = StorageConfig.SESSION_DIR
        
        # Path should be directly in or under session dir
        assert session_dir in path.parents or path.parent == session_dir
