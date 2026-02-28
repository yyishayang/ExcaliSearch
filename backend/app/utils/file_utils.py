"""
File storage utilities and path constants.
"""

import os
import uuid
from pathlib import Path
from fastapi import UploadFile

# Base directory is project root (backend/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
STORAGE_DIR = BASE_DIR / "storage"
DATA_DIR = BASE_DIR / "data"
INDEX_DIR = BASE_DIR / "whoosh_index"

ALLOWED_EXTENSIONS = {"pdf", "txt", "docx"}


def ensure_dirs():
    """Create required directories if they don't exist."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """Extract lowercase file extension without dot."""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def is_allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    return get_file_extension(filename) in ALLOWED_EXTENSIONS


async def save_upload(file: UploadFile) -> tuple[str, bytes]:
    """
    Save an uploaded file to the storage directory.
    Returns (stored_filename, file_bytes).
    Uses a UUID prefix to avoid name collisions.
    """
    ensure_dirs()

    # Generate unique stored filename
    ext = get_file_extension(file.filename)
    unique_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"

    file_path = STORAGE_DIR / unique_name
    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    return unique_name, content


def get_file_path(stored_filename: str) -> Path:
    """Get the full path to a stored file."""
    return STORAGE_DIR / stored_filename


def delete_file(stored_filename: str) -> bool:
    """Delete a stored file. Returns True if the file existed."""
    path = STORAGE_DIR / stored_filename
    if path.exists():
        path.unlink()
        return True
    return False


def get_file_size_str(size_bytes: int) -> str:
    """Human-readable file size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
