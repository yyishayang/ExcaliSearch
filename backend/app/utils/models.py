"""
Pydantic models for document metadata persistence.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid


class DocumentMetadata(BaseModel):
    """Represents a stored document's metadata."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    filename: str  # stored filename (may be renamed to avoid collisions)
    original_name: str  # user-provided original filename
    file_type: str  # pdf, txt, docx
    file_size: int  # bytes
    hash: str  # SHA-256 of file content
    upload_date: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
    text_preview: str = ""  # first N characters of extracted text
    page_count: Optional[int] = None  # for PDFs
    word_count: int = 0
