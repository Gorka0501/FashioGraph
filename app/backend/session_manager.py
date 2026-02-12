"""
Session Management with Login/Logout
Handles user session storage, lifecycle, and authentication state.
"""

import json
import time
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import threading
import logging

from .storage_config import StorageConfig

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages user sessions with file-based persistence and login/logout."""

    def __init__(self, session_timeout: int = None):
        """Initialize session manager.

        Args:
            session_timeout: Session timeout in seconds (31 days default)
        """
        # 31 days = 2,678,400 seconds
        self.session_timeout = session_timeout or (31 * 24 * 60 * 60)
        self.sessions: Dict[str, Dict[str, Any]] = {}  # username -> session
        self.logged_in_user: Optional[str] = None  # Only ONE user logged in at a time
        self._load_all_sessions()

        # Start cleanup thread
        self._cleanup_thread = threading.Thread(daemon=True, target=self._cleanup_expired)
        self._cleanup_thread.start()

    def login(self, username: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Login a user - only ONE user can be logged in per device.
        
        If another user is logged in, they will be automatically logged out.

        Args:
            username: Username
            user_data: User data to store in session (token, user_id, etc.)

        Returns:
            Session data with creation time and expiry
        """
        # Logout any previously logged-in user
        if self.logged_in_user and self.logged_in_user != username:
            self.logout(self.logged_in_user)
            logger.info(f"Auto-logged out previous user: {self.logged_in_user}")
        
        session = {
            "username": username,
            "logged_in_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(seconds=self.session_timeout)).isoformat(),
            "data": user_data,
            "is_active": True,
        }

        self.sessions[username] = session
        self.logged_in_user = username
        self._save_session(username, session)
        logger.info(f"User logged in: {username}")
        return session

    def logout(self, username: str) -> bool:
        """Logout a user - destroy session.

        Args:
            username: Username

        Returns:
            True if successful
        """
        if self.logged_in_user == username:
            self.logged_in_user = None
        
        return self.destroy_session(username)

    def get_session(self, username: str) -> Optional[Dict[str, Any]]:
        """Get session for a user if logged in and not expired.

        Args:
            username: Username

        Returns:
            Session data if valid and not expired, None otherwise
        """
        # Check in memory first
        if username in self.sessions:
            session = self.sessions[username]
            if self._is_session_valid(session):
                # Update last accessed
                session["last_accessed"] = datetime.now().isoformat()
                self._save_session(username, session)
                return session
            else:
                # Session expired - auto logout
                self.logout(username)
                return None

        # Try to load from disk
        session = self._load_session(username)
        if session and self._is_session_valid(session):
            self.sessions[username] = session
            session["last_accessed"] = datetime.now().isoformat()
            self._save_session(username, session)
            return session

        return None

    def update_session(self, username: str, data_updates: Dict[str, Any]) -> bool:
        """Update session data.

        Args:
            username: Username
            data_updates: Dictionary of updates to merge into session data

        Returns:
            True if successful, False otherwise
        """
        session = self.get_session(username)
        if not session:
            logger.warning(f"Session not found for user {username}")
            return False

        session["data"].update(data_updates)
        session["last_accessed"] = datetime.now().isoformat()
        self._save_session(username, session)
        logger.info(f"Updated session for user {username}")
        return True

    def destroy_session(self, username: str) -> bool:
        """Destroy a user session.

        Args:
            username: Username

        Returns:
            True if successful, False otherwise
        """
        # Remove from memory
        if username in self.sessions:
            del self.sessions[username]

        # Remove from disk
        session_file = StorageConfig.get_user_session_file(username)
        if session_file.exists():
            try:
                session_file.unlink()
                logger.info(f"Destroyed session for user {username}")
                return True
            except Exception as e:
                logger.error(f"Failed to destroy session for user {username}: {e}")
                return False

        return True

    def is_logged_in(self, username: str) -> bool:
        """Check if a user is currently logged in.

        Args:
            username: Username

        Returns:
            True if logged in and session is valid, False otherwise
        """
        return self.logged_in_user == username and self.get_session(username) is not None

    def get_all_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get the currently logged-in session (only one user at a time).

        Returns:
            Dictionary with single logged-in user session, or empty dict
        """
        if self.logged_in_user:
            session = self.get_session(self.logged_in_user)
            if session:
                return {self.logged_in_user: session}
            else:
                self.logged_in_user = None
        
        return {}

    def get_logged_in_users(self) -> set:
        """Get set of currently logged-in usernames (only one possible).

        Returns:
            Set with single username, or empty set
        """
        if self.logged_in_user:
            return {self.logged_in_user}
        return set()

    def clear_all_sessions(self) -> int:
        """Clear all sessions and logout all users.

        Returns:
            Number of sessions cleared
        """
        count = len(self.sessions)
        usernames = list(self.sessions.keys())

        for username in usernames:
            self.logout(username)

        logger.info(f"Cleared {count} sessions")
        return count

    # ========================================================================
    # Private methods
    # ========================================================================

    def _is_session_valid(self, session: Dict[str, Any]) -> bool:
        """Check if session is valid and not expired."""
        try:
            expires_at = datetime.fromisoformat(session["expires_at"])
            return datetime.now() < expires_at
        except Exception as e:
            logger.error(f"Failed to validate session: {e}")
            return False

    def _save_session(self, username: str, session: Dict[str, Any]) -> bool:
        """Save session to disk."""
        try:
            session_file = StorageConfig.get_user_session_file(username)
            session_file.parent.mkdir(parents=True, exist_ok=True)

            with open(session_file, 'w') as f:
                json.dump(session, f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Failed to save session for user {username}: {e}")
            return False

    def _load_session(self, username: str) -> Optional[Dict[str, Any]]:
        """Load session from disk."""
        try:
            session_file = StorageConfig.get_user_session_file(username)
            if not session_file.exists():
                return None

            with open(session_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load session for user {username}: {e}")
            return None

    def _load_all_sessions(self) -> None:
        """Load all sessions from disk on startup."""
        try:
            session_dir = StorageConfig.SESSION_DIR
            if not session_dir.exists():
                return

            for session_file in session_dir.glob("*.json"):
                try:
                    with open(session_file, 'r') as f:
                        session = json.load(f)
                        username = session.get("username")
                        if username and self._is_session_valid(session):
                            self.sessions[username] = session
                            # Only restore if no user currently logged in
                            if not self.logged_in_user:
                                self.logged_in_user = username
                except Exception as e:
                    logger.warning(f"Failed to load session file {session_file}: {e}")

            logger.info(f"Loaded {len(self.sessions)} valid sessions from disk")
            if self.logged_in_user:
                logger.info(f"Restored logged-in user: {self.logged_in_user}")
        except Exception as e:
            logger.error(f"Failed to load all sessions: {e}")

    def _cleanup_expired(self) -> None:
        """Periodically check for expired sessions and logout user."""
        while True:
            time.sleep(StorageConfig.SESSION_CLEAN_INTERVAL)
            try:
                if self.logged_in_user:
                    session = self.sessions.get(self.logged_in_user)
                    if session and not self._is_session_valid(session):
                        expired_user = self.logged_in_user
                        self.logout(self.logged_in_user)
                        logger.info(f"Auto-logged out user {expired_user} due to 31-day inactivity")
            except Exception as e:
                logger.error(f"Error during session cleanup: {e}")


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create the global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
