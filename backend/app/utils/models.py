from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid


class DocumentMetadata(BaseModel):
    """Represents a stored document's metadata."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    filename: str 
    original_name: str 
    file_type: str 
    file_size: int  
    hash: str  
    upload_date: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
    text_preview: str = ""  
    page_count: Optional[int] = None 
    word_count: int = 0
