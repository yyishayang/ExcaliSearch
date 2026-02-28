"""
API response and request schemas.
"""

from pydantic import BaseModel
from typing import List, Optional


class UploadResponse(BaseModel):
    """Response after a successful document upload."""

    id: str
    filename: str
    original_name: str
    file_type: str
    file_size: int
    upload_date: str
    message: str = "Document uploaded and indexed successfully"


class SearchResult(BaseModel):
    """A single search result."""

    doc_id: str
    filename: str
    original_name: str
    snippet: str  # highlighted text fragment
    score: float
    file_type: str


class SearchResponse(BaseModel):
    """Response for a search query."""

    query: str
    total_results: int
    results: List[SearchResult]


class DocumentDetail(BaseModel):
    """Full document detail for the viewer."""

    id: str
    filename: str
    original_name: str
    file_type: str
    file_size: int
    upload_date: str
    text_preview: str
    content: str  # full extracted text
    page_count: Optional[int] = None
    word_count: int = 0


class DocumentListItem(BaseModel):
    """Document item for listing."""

    id: str
    original_name: str
    file_type: str
    file_size: int
    upload_date: str
    word_count: int = 0


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
