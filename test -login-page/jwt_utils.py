"""
JWT Token Creation and Validation
Uses Flask-JWT-Extended for better security and features
"""

from flask_jwt_extended import create_access_token as jwt_create_access_token
from flask_jwt_extended import decode_token as jwt_decode_token
from datetime import timedelta
from config import JWT_ACCESS_TOKEN_EXPIRES


def create_access_token(user_id, username, email):
    """
    Create a JWT access token
    
    Args:
        user_id (str): User ID
        username (str): Username
        email (str): User email
    
    Returns:
        str: JWT token
    """
    additional_claims = {
        "username": username,
        "email": email,
        "token_type": "access"
    }
    
    token = jwt_create_access_token(
        identity=user_id,
        additional_claims=additional_claims,
        expires_delta=JWT_ACCESS_TOKEN_EXPIRES
    )
    return token


def verify_token(token):
    """
    Verify and decode JWT token
    
    Args:
        token (str): JWT token to verify
    
    Returns:
        dict: Decoded payload if valid, None if invalid
    """
    try:
        payload = jwt_decode_token(token)
        return payload
    except Exception:
        return None  # Token is invalid or expired


def decode_token(token):
    """
    Decode token without verification (for debugging)
    
    Args:
        token (str): JWT token
    
    Returns:
        dict: Decoded payload
    """
    try:
        return jwt_decode_token(token)
    except Exception:
        return None
