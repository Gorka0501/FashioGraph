"""Unit tests for session manager."""
import pytest
import json
import time
from pathlib import Path
from app.backend.session_manager import SessionManager, get_session_manager


@pytest.fixture
def session_manager():
    """Create a session manager for testing."""
    manager = SessionManager(session_timeout=31*24*60*60)
    # Clean up any existing sessions from previous tests
    manager.clear_all_sessions()
    return manager


class TestSessionManager:
    """Test SessionManager functionality."""
    
    def test_session_manager_initialization(self):
        """Test that session manager initializes correctly."""
        manager = SessionManager()
        # Initialization loads sessions from disk if they exist, so we just check attributes
        assert manager.session_timeout == (31 * 24 * 60 * 60)
        assert isinstance(manager.sessions, dict)
        assert manager.logged_in_user is None or isinstance(manager.logged_in_user, str)
    
    def test_login_creates_session(self, session_manager):
        """Test that login creates a session."""
        username = "testuser"
        data = {"user_id": 1, "token": "test_token"}
        
        session = session_manager.login(username, data)
        
        assert session is not None
        assert session["username"] == username
        assert session["data"] == data
        assert session["is_active"] is True
    
    def test_login_session_contains_required_fields(self, session_manager):
        """Test that session contains all required fields."""
        username = "testuser"
        data = {"user_id": 1, "token": "test_token"}
        
        session = session_manager.login(username, data)
        
        assert session["username"] == username
        assert session["is_active"] is True
        assert "logged_in_at" in session
        assert "expires_at" in session
        assert "last_accessed" in session
        assert session["data"]["user_id"] == 1
        assert session["data"]["token"] == "test_token"
    
    def test_login_auto_logs_out_previous_user(self, session_manager):
        """Test that login of new user logs out previous user."""
        user1 = "user1"
        user2 = "user2"
        
        session_manager.login(user1, {"user_id": 1, "token": "token1"})
        assert session_manager.logged_in_user == user1
        
        session_manager.login(user2, {"user_id": 2, "token": "token2"})
        assert session_manager.logged_in_user == user2
        
        # User1 should be logged out
        assert not session_manager.is_logged_in(user1)
        assert session_manager.is_logged_in(user2)
    
    def test_logout_destroys_session(self, session_manager):
        """Test that logout destroys session."""
        username = "testuser"
        session_manager.login(username, {"user_id": 1, "token": "test_token"})
        
        assert session_manager.is_logged_in(username)
        
        session_manager.logout(username)
        
        assert not session_manager.is_logged_in(username)
        assert session_manager.logged_in_user is None
    
    def test_is_logged_in_returns_false_for_nonexistent_user(self, session_manager):
        """Test that is_logged_in returns False for non-existent user."""
        assert not session_manager.is_logged_in("nonexistent")
    
    def test_get_logged_in_user_single_user(self, session_manager):
        """Test that get_logged_in_users returns current user."""
        username = "testuser"
        session_manager.login(username, {"user_id": 1, "token": "token"})
        
        logged_in = session_manager.get_logged_in_users()
        assert username in logged_in
        assert len(logged_in) == 1
    
    def test_get_logged_in_user_none_when_no_user(self, session_manager):
        """Test that get_logged_in_users returns empty set when no user."""
        logged_in = session_manager.get_logged_in_users()
        assert logged_in == set()
    
    def test_session_expiry(self):
        """Test that session expires after timeout."""
        username = "testuser"
        manager = SessionManager(session_timeout=1)
        
        manager.login(username, {"user_id": 1, "token": "token"})
        assert manager.is_logged_in(username)
        
        time.sleep(2)
        assert not manager.is_logged_in(username)
    
    def test_multiple_login_attempts_overwrite_session(self, session_manager):
        """Test that multiple logins overwrite previous session."""
        username = "testuser"
        
        session1 = session_manager.login(username, {"user_id": 1, "token": "token1"})
        logged_in_at_1 = session1["logged_in_at"]
        
        time.sleep(0.1)
        
        session2 = session_manager.login(username, {"user_id": 2, "token": "token2"})
        logged_in_at_2 = session2["logged_in_at"]
        
        assert logged_in_at_1 != logged_in_at_2
        assert session_manager.get_logged_in_users() == {username}
    
    def test_session_file_format(self, session_manager):
        """Test that session file has correct JSON structure."""
        username = "testuser"
        data = {"user_id": 123, "token": "jwt_token_xyz"}
        
        session_manager.login(username, data)
        
        session = session_manager.get_session(username)
        
        assert isinstance(session, dict)
        assert session["username"] == username
        assert isinstance(session["logged_in_at"], str)
        assert isinstance(session["expires_at"], str)
        assert isinstance(session["data"], dict)
        assert session["data"]["user_id"] == 123
        assert session["data"]["token"] == "jwt_token_xyz"
    
    def test_logout_nonexistent_user_doesnt_error(self, session_manager):
        """Test that logout of non-existent user doesn't raise error."""
        result = session_manager.logout("nonexistent")
        assert result is True
    
    def test_cleanup_expired_sessions(self):
        """Test that get_session returns None for expired sessions."""
        username = "testuser"
        manager = SessionManager(session_timeout=1)
        
        manager.login(username, {"user_id": 1, "token": "token"})
        time.sleep(2)
        
        session = manager.get_session(username)
        assert session is None


class TestSessionManagerEdgeCases:
    """Test edge cases and error handling."""
    
    def test_login_with_empty_data(self, session_manager):
        """Test login with empty session data."""
        username = "testuser"
        session = session_manager.login(username, {})
        
        assert session is not None
        assert session["data"] == {}
    
    def test_login_with_special_characters_in_username(self, session_manager):
        """Test login with special characters in username."""
        username = "test.user+123@example.com"
        session = session_manager.login(username, {"user_id": 1, "token": "token"})
        
        assert session["username"] == username
        assert session_manager.is_logged_in(username)
    
    def test_multiple_users_single_logged_in(self, session_manager):
        """Test that only one user can be logged in at a time."""
        user1 = "user1"
        user2 = "user2"
        user3 = "user3"
        
        session_manager.login(user1, {"user_id": 1, "token": "token1"})
        session_manager.login(user2, {"user_id": 2, "token": "token2"})
        session_manager.login(user3, {"user_id": 3, "token": "token3"})
        
        logged_in = session_manager.get_logged_in_users()
        assert len(logged_in) == 1
        assert user3 in logged_in
    
    def test_corrupted_session_file_handling(self, session_manager):
        """Test handling of corrupted session files on disk."""
        from app.backend.storage_config import StorageConfig
        
        # First create a session
        username = "testuser"
        session_manager.login(username, {"user_id": 1, "token": "token"})
        
        # Then logout to clear it from memory but leave the file
        session_manager.logout(username)
        
        # Create a new corrupted session file
        session_file = StorageConfig.get_user_session_file(username)
        session_file.write_text("invalid json {{{")
        
        # Now trying to load should fail gracefully
        session = session_manager.get_session(username)
        assert session is None
    
    def test_concurrent_logins_same_user(self, session_manager):
        """Test multiple logins for same user."""
        username = "testuser"
        
        session1 = session_manager.login(username, {"user_id": 1, "token": "token1"})
        session2 = session_manager.login(username, {"user_id": 1, "token": "token2"})
        
        assert session1 is not None
        assert session2 is not None
        
        current = session_manager.get_session(username)
        assert current["data"]["token"] == "token2"


class TestSessionTimings:
    """Test session timeout and timing functionality."""
    
    def test_default_session_timeout(self):
        """Test that default timeout is 31 days."""
        manager = SessionManager()
        expected_seconds = 31 * 24 * 60 * 60
        assert manager.session_timeout == expected_seconds
    
    def test_session_last_accessed_tracking(self, session_manager):
        """Test that last_accessed is updated on get_session."""
        username = "testuser"
        session_manager.login(username, {"user_id": 1, "token": "token"})
        
        session1 = session_manager.get_session(username)
        first_accessed = session1["last_accessed"]
        
        time.sleep(0.1)
        
        session2 = session_manager.get_session(username)
        second_accessed = session2["last_accessed"]
        
        assert first_accessed != second_accessed
