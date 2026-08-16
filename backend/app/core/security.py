"""Cryptographic Security, Password Hashing & Prompt-Injection Defense."""

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt
from app.core.config import settings
from app.core.exceptions import PromptInjectionException, UnauthorizedException

# Argon2id Password Hasher instance with recommended parameters
ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,  # 64 MB
    parallelism=1,
    hash_len=32
)

# Known adversarial prompt injection patterns in untrusted documents
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a\s+different\s+ai", re.IGNORECASE),
    re.compile(r"system\s*:\s*override", re.IGNORECASE),
    re.compile(r"<\s*script\s*>", re.IGNORECASE),
    re.compile(r"drop\s+table\s+", re.IGNORECASE),
    re.compile(r"bypass\s+all\s+safety\s+filters?", re.IGNORECASE),
    re.compile(r"forget\s+all\s+rules?", re.IGNORECASE),
]


def hash_password(password: str) -> str:
    """Hash plaintext password with Argon2id."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against stored Argon2id hash."""
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


import hashlib
import secrets

def hash_token(token: str) -> str:
    """Compute SHA-256 hex digest of a token for secure database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_secure_random_token() -> str:
    """Generate cryptographically secure 256-bit URL-safe token."""
    return secrets.token_urlsafe(32)


def create_access_token(
    subject: str,
    org_id: Optional[str] = None,
    role: Optional[str] = None,
    session_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate signed JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    
    payload: Dict[str, Any] = {
        "sub": subject,
        "org_id": org_id,
        "role": role,
        "session_id": session_id,
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.APP_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: str,
    org_id: Optional[str] = None,
    session_id: Optional[str] = None,
    family_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate signed JWT refresh token."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    
    payload: Dict[str, Any] = {
        "sub": subject,
        "org_id": org_id,
        "session_id": session_id,
        "family_id": family_id,
        "jti": secrets.token_hex(16),
        "iat": now,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.APP_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)



def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a signed JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.APP_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("Session token has expired.")
    except jwt.InvalidTokenError:
        raise UnauthorizedException("Invalid token signature or payload.")


def sanitize_document_text(text: str, strict: bool = False) -> str:
    """
    Sanitize untrusted document text before passing to LLM / RAG pipeline.
    Documents are DATA, not INSTRUCTIONS.
    """
    if not text:
        return ""

    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.search(text):
            if strict:
                raise PromptInjectionException(
                    "Adversarial prompt injection pattern detected in document content."
                )
            # Neutralize instruction override attempts in data stream
            text = pattern.sub("[SANITIZED_INSTRUCTION_ATTEMPT]", text)

    return text
