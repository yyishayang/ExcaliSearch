# SPDX-FileCopyrightText: 2026 @albabsuarez
# SPDX-FileCopyrightText: 2026 @aslangallery
# SPDX-FileCopyrightText: 2026 @david598Uni
# SPDX-FileCopyrightText: 2026 @yyishayang
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from fastapi import APIRouter, HTTPException, status

from app.utils.database import get_document
from app.utils.schemas import DocumentDetail
from app.services.document_service import get_document_text

router = APIRouter(prefix="/api/documents", tags=["Metadata"])

@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document_detail(doc_id: str):
    doc = get_document(doc_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    content = get_document_text(doc_id) or ""

    return DocumentDetail(
        id=doc.id,
        filename=doc.filename,
        original_name=doc.original_name,
        file_type=doc.file_type,
        file_size=doc.file_size,
        upload_date=doc.upload_date,
        text_preview=doc.text_preview,
        summary=doc.summary,
        content=content,
        page_count=doc.page_count,
        word_count=doc.word_count,
    )
