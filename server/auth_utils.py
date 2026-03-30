"""JWT and password helpers for API authentication."""
import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Dict, Optional

import jwt
from flask import jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", "168"))  # 7 days


def hash_password(plain: str) -> str:
    return generate_password_hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return check_password_hash(hashed, plain)


def encode_token(user_id: int, email: str, is_admin: bool = False) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "is_admin": is_admin,
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


def get_bearer_token() -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return None


def require_auth(f):
    """Decorator: require valid JWT; sets request.user_id from token."""

    @wraps(f)
    def wrapped(*args, **kwargs):
        from models import User, db

        token = get_bearer_token()
        if not token:
            return jsonify({"error": "Authentication required"}), 401
        data = decode_token(token)
        if not data or not data.get("sub"):
            return jsonify({"error": "Invalid or expired token"}), 401
        user = User.query.get(int(data["sub"]))
        if not user or not user.is_active:
            return jsonify({"error": "User not found or inactive"}), 401
        request.user_id = user.id
        request.user = user
        return f(*args, **kwargs)

    return wrapped


def optional_auth():
    """If Bearer token present and valid, set request.user; else leave unset."""
    from models import User

    token = get_bearer_token()
    if not token:
        return
    data = decode_token(token)
    if not data or not data.get("sub"):
        return
    user = User.query.get(int(data["sub"]))
    if user and user.is_active:
        request.user_id = user.id
        request.user = user


def require_admin(f):
    """Decorator: require authenticated admin user."""

    @wraps(f)
    def wrapped(*args, **kwargs):
        from models import User

        token = get_bearer_token()
        if not token:
            return jsonify({"error": "Authentication required"}), 401
        data = decode_token(token)
        if not data or not data.get("sub"):
            return jsonify({"error": "Invalid or expired token"}), 401
        user = User.query.get(int(data["sub"]))
        if not user or not user.is_active:
            return jsonify({"error": "User not found or inactive"}), 401
        if not user.is_admin:
            return jsonify({"error": "Admin access required"}), 403
        request.user_id = user.id
        request.user = user
        return f(*args, **kwargs)

    return wrapped
