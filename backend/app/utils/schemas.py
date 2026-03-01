from pydantic import BaseModel
from typing import List, Optional

class UploadResponse(BaseModel):

    id: str
    filename: str
    original_name: str
    file_type: str
    file_size: int
    upload_date: str
    summary: str = ""
    message: str = "Document uploaded and indexed successfully"


class SearchResult(BaseModel):

    doc_id: str
    filename: str
    original_name: str
    snippet: str  # highlighted text fragment
    summary: str = ""  # document summary
    score: float
    file_type: str


class SearchResponse(BaseModel):

    query: str
    total_results: int
    results: List[SearchResult]


class DocumentDetail(BaseModel):

    id: str
    filename: str
    original_name: str
    file_type: str
    file_size: int
    upload_date: str
    text_preview: str
    summary: str = ""
    content: str  # full extracted text
    page_count: Optional[int] = None
    word_count: int = 0


class DocumentListItem(BaseModel):

    id: str
    original_name: str
    file_type: str
    file_size: int
    upload_date: str
    summary: str = ""
    word_count: int = 0


class ErrorResponse(BaseModel):

    detail: str


class BatchUploadResult(BaseModel):
    
    filename: str
    status: str  # "success" or "error"
    doc_id: Optional[str] = None
    error: Optional[str] = None
    word_count: Optional[int] = None


class BatchUploadResponse(BaseModel):
    
    total_files: int
    successful: int
    failed: int
    results: List[BatchUploadResult]
