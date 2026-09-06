"""Security & Encryption Utilities for Third-Party Connector Credentials and Telemetry Ingestion."""

import base64
import hashlib
import html
import json
import re
from typing import Any, Dict, Optional
from cryptography.fernet import Fernet
from app.core.config import settings
from app.domains.telemetry.schemas import ConnectionCredentials


class CredentialVault:
    """Enterprise-grade symmetric encryption vault for external OAuth credentials and API secrets.
    
    Guarantees:
    1. Credentials are NEVER stored plaintext in the database.
    2. Credentials are encrypted using Fernet (AES-128 in CBC mode with HMAC-SHA256).
    3. Keys are deterministically derived from APP_SECRET_KEY using SHA-256.
    4. Secrets are NEVER serialized into user-facing API representations.
    """

    @classmethod
    def _get_fernet_key(cls) -> bytes:
        """Derive a 32-byte URL-safe base64-encoded key from the application secret key."""
        raw_key = settings.APP_SECRET_KEY.encode("utf-8")
        # SHA-256 digest gives exactly 32 bytes
        digest = hashlib.sha256(raw_key).digest()
        return base64.urlsafe_b64encode(digest)

    @classmethod
    def encrypt_credentials(cls, credentials: Any) -> str:
        """Encrypt credentials dictionary or schema into an authenticated ciphertext string."""
        fernet = Fernet(cls._get_fernet_key())
        if hasattr(credentials, "model_dump_json"):
            raw_json = credentials.model_dump_json()
        elif isinstance(credentials, dict):
            raw_json = json.dumps(credentials)
        else:
            raw_json = json.dumps(dict(credentials))
        encrypted_bytes = fernet.encrypt(raw_json.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")

    @classmethod
    def decrypt_credentials(cls, encrypted_payload: str) -> Dict[str, Any]:
        """Decrypt ciphertext payload into raw credentials dictionary."""
        if not encrypted_payload:
            return {}
        fernet = Fernet(cls._get_fernet_key())
        decrypted_bytes = fernet.decrypt(encrypted_payload.encode("utf-8"))
        return json.loads(decrypted_bytes.decode("utf-8"))

    @classmethod
    def decrypt_as_credentials(cls, encrypted_payload: str) -> ConnectionCredentials:
        """Decrypt ciphertext payload into strongly-typed ConnectionCredentials object."""
        data = cls.decrypt_credentials(encrypted_payload)
        return ConnectionCredentials(**data)

    @classmethod
    def mask_secret(cls, secret: Optional[str], visible_suffix_chars: int = 4) -> str:
        """Mask sensitive tokens or keys for safe operational display."""
        return mask_secret(secret, visible_suffix_chars)


def mask_secret(secret: Optional[str], visible_suffix_chars: int = 4) -> str:
    """Mask sensitive tokens or keys for safe operational display (e.g. '00D5****test')."""
    if not secret:
        return "******"
    if len(secret) <= visible_suffix_chars or len(secret) <= 8:
        return "******"
    return f"{secret[:4]}{'*' * (len(secret) - 8)}{secret[-4:]}"


def sanitize_untrusted_text(text: Optional[str], max_length: int = 2000) -> str:
    """Sanitize external CRM/ERP freeform text fields to neutralize injection attacks.
    
    External CRM/ERP records (notes, descriptions, stage comments) are treated as untrusted data.
    They must never execute code, render raw HTML, or inject prompt instructions into LLM agents.
    """
    if not text:
        return ""
    
    # 1. Truncate to maximum permissible length
    s = str(text).strip()[:max_length]

    # 2. Escape HTML / Script tags
    s = html.escape(s)

    # 3. Strip common prompt injection control sequences (e.g. 'Ignore previous instructions')
    injection_patterns = [
        r"(?i)\bignore\s+(all\s+)?previous\s+instructions\b",
        r"(?i)\bsystem\s+override\b",
        r"(?i)\bdeveloper\s+mode\b",
        r"(?i)\bact\s+as\s+a\b",
    ]
    for pattern in injection_patterns:
        s = re.sub(pattern, "[FILTERED_INSTRUCTION]", s)

    return s
