"""
File hashing utilities for duplicate detection.
"""

import hashlib


def compute_sha256(file_bytes: bytes) -> str:
    """Compute SHA-256 hash of file content."""
    return hashlib.sha256(file_bytes).hexdigest()
