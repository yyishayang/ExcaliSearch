# SPDX-FileCopyrightText: 2026 @albabsuarez
# SPDX-FileCopyrightText: 2026 @aslangallery
# SPDX-FileCopyrightText: 2026 @david598Uni
# SPDX-FileCopyrightText: 2026 @yyishayang
#
# SPDX-License-Identifier: AGPL-3.0-or-later

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
    text_preview: str = ""  # first N characters of extracted text
    summary: str = ""  # automatic extractive summary (5-10 sentences)
    page_count: Optional[int] = None  # for PDFs
    word_count: int = 0
