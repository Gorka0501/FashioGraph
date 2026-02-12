"""Unit tests for security module (password hashing and JWT tokens)."""
import pytest
from datetime import timedelta
from app.backend.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    TokenData
)


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test that password hashing creates a valid hash."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password  # Hash should be different from original
    
    def test_verify_correct_password(self):
        """Test that correct password verifies successfully."""
        password = "correct_password"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        """Test that incorrect password fails verification."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_password_with_special_characters(self):
        """Test password hashing with special characters."""
        password = "P@ssw0rd!#$%^&*()"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_with_unicode(self):
        """Test password hashing with unicode characters."""
        password = "пароль_密码_🔐"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_long_password_truncation(self):
        """Test that passwords longer than 72 bytes are handled."""
        # bcrypt has a 72-byte limit
        long_password = "a" * 100
        hashed = hash_password(long_password)
        
        # Should still work for the truncated portion
        assert verify_password(long_password, hashed) is True
        
        # But a completely different long password should fail
        different_long = "b" * 100
        assert verify_password(different_long, hashed) is False


class TestJWTTokens:
    """Test JWT token creation and verification."""
    
    def test_create_access_token(self):
        """Test that access token is created successfully."""
        user_id = 1
        username = "testuser"
        token = create_access_token(user_id=user_id, username=username)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_token_with_expiration(self):
        """Test token creation with custom expiration."""
        user_id = 1
        username = "testuser"
        expires_delta = timedelta(hours=1)
        token = create_access_token(
            user_id=user_id,
            username=username,
            expires_delta=expires_delta
        )
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_verify_valid_token(self):
        """Test that valid token is verified successfully."""
        user_id = 123
        username = "testuser"
        token = create_access_token(user_id=user_id, username=username)
        
        token_data = verify_token(token)
        
        assert token_data is not None
        assert isinstance(token_data, TokenData)
        assert token_data.user_id == user_id
        assert token_data.username == username
    
    def test_verify_invalid_token(self):
        """Test that invalid token returns None."""
        invalid_token = "invalid.token.here"
        
        result = verify_token(invalid_token)
        
        assert result is None
    
    def test_token_contains_user_info(self):
        """Test that token contains correct user information."""
        user_id = 456
        username = "john_doe"
        token = create_access_token(user_id=user_id, username=username)
        
        token_data = verify_token(token)
        
        assert token_data.user_id == user_id
        assert token_data.username == username


class TestTokenData:
    """Test TokenData pydantic model."""
    
    def test_token_data_creation(self):
        """Test TokenData model creation."""
        token_data = TokenData(user_id=1, username="testuser")
        
        assert token_data.user_id == 1
        assert token_data.username == "testuser"
    
    def test_token_data_validation(self):
        """Test TokenData validation."""
        # Valid data
        token_data = TokenData(user_id=1, username="testuser")
        assert token_data is not None
        
        # Invalid data should raise validation error
        with pytest.raises(Exception):
            TokenData(user_id="not_an_int", username="testuser")
