"""Pytest configuration and shared fixtures for backend tests."""
import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return {
        "database_url": "sqlite:///:memory:",
        "secret_key": "test-secret-key-do-not-use-in-production",
        "algorithm": "HS256",
        "access_token_expire_hours": 24
    }


@pytest.fixture
def mock_image_path(tmp_path):
    """Create a temporary image file path."""
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    return image_dir / "test_image.jpg"
