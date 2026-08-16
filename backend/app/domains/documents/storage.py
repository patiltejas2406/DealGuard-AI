"""Document Storage Engine with Tenant Boundary Isolation & Safe Path Verification."""

import hashlib
import os
import re
import uuid
from typing import Tuple
from app.core.config import settings
from app.core.exceptions import ValidationException

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB limit


class DocumentStorageManager:
    """Manages file persistence, checksum verification, and path traversal security."""

    def __init__(self, base_storage_dir: str = "data/vault") -> None:
        self.base_storage_dir = os.path.abspath(base_storage_dir)
        os.makedirs(self.base_storage_dir, exist_ok=True)

    def calculate_sha256(self, file_bytes: bytes) -> str:
        """Calculate SHA-256 hex digest of document bytes."""
        return hashlib.sha256(file_bytes).hexdigest()

    def sanitize_filename(self, filename: str) -> str:
        """Strip dangerous path characters and normalize filename."""
        clean_name = os.path.basename(filename)
        clean_name = re.sub(r"[^\w\.\-\_]", "_", clean_name)
        return clean_name or "document.bin"

    async def save_document(
        self,
        organization_id: uuid.UUID,
        deal_id: uuid.UUID,
        filename: str,
        file_bytes: bytes,
    ) -> Tuple[str, str, int]:
        """
        Validate and save uploaded file to tenant-isolated disk storage.
        Returns: (storage_path, sha256_hash, size_bytes)
        """
        size_bytes = len(file_bytes)
        if size_bytes == 0:
            raise ValidationException("Uploaded file is empty (0 bytes).")
        if size_bytes > MAX_FILE_SIZE_BYTES:
            raise ValidationException(f"File size exceeds maximum permitted limit of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB.")

        sha256_hash = self.calculate_sha256(file_bytes)
        clean_filename = self.sanitize_filename(filename)

        # Build tenant/deal directory
        target_dir = os.path.join(self.base_storage_dir, str(organization_id), str(deal_id))
        os.makedirs(target_dir, exist_ok=True)

        target_file_path = os.path.join(target_dir, f"{sha256_hash[:16]}_{clean_filename}")

        # Path traversal guard
        if not os.path.abspath(target_file_path).startswith(self.base_storage_dir):
            raise ValidationException("Illegal path traversal detected in storage path.")

        with open(target_file_path, "wb") as f:
            f.write(file_bytes)

        return target_file_path, sha256_hash, size_bytes

    async def read_document(self, storage_path: str) -> bytes:
        """Read document bytes securely from storage."""
        if not os.path.exists(storage_path):
            raise ValidationException(f"Document file not found at path: {storage_path}")

        with open(storage_path, "rb") as f:
            return f.read()
