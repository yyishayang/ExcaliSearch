# SPDX-FileCopyrightText: 2026 @albabsuarez
# SPDX-FileCopyrightText: 2026 @aslangallery
# SPDX-FileCopyrightText: 2026 @david598Uni
# SPDX-FileCopyrightText: 2026 @yyishayang
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.utils.database import get_document, update_document, list_documents
from app.services.document_service import get_document_text
from app.services.summary_service import generate_summary, generate_smart_summary

router = APIRouter(prefix="/api/summary", tags=["Summary"])


class SummaryResponse(BaseModel):
    """Response containing a document summary."""
    
    doc_id: str
    original_name: str
    summary: str
    sentence_count: int
    algorithm: str
    language: str
    method: str = "extractive"  # "extractive" or "llm"


class RegenerateSummaryRequest(BaseModel):
    """Request to regenerate a summary with custom parameters."""
    
    sentence_count: int = 5
    algorithm: str = "lsa"  # "lsa", "lexrank", or "textrank" (for extractive)
    language: str = "spanish"  # "spanish" or "english"
    method: str = "auto"  # "auto", "extractive", or "llm"


class BulkRegenerateResponse(BaseModel):
    """Response for bulk summary regeneration."""
    
    total_documents: int
    successful: int
    failed: int
    errors: list[str] = []


@router.get("/{doc_id}", response_model=SummaryResponse)
async def get_document_summary(doc_id: str):
    """
    Get the summary for a specific document.
    Returns the stored summary if it exists, or generates a new one.
    """
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found"
        )
    
    # If summary already exists, return it
    if doc.summary:
        return SummaryResponse(
            doc_id=doc.id,
            original_name=doc.original_name,
            summary=doc.summary,
            sentence_count=len(doc.summary.split(". ")),
            algorithm="lsa",  # Default used during upload
            language="auto",
            method="extractive"  # Default method
        )
    
    # Generate summary if it doesn't exist
    text = get_document_text(doc_id)
    if not text:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve document text"
        )
    
    summary = generate_smart_summary(text)
    doc.summary = summary
    update_document(doc)
    
    return SummaryResponse(
        doc_id=doc.id,
        original_name=doc.original_name,
        summary=summary,
        sentence_count=len(summary.split(". ")),
        algorithm="lsa",
        language="auto",
        method="auto"
    )


@router.post("/{doc_id}/regenerate", response_model=SummaryResponse)
async def regenerate_document_summary(
    doc_id: str,
    request: RegenerateSummaryRequest
):
    """
    Regenerate the summary for a specific document with custom parameters.
    
    Allows customizing:
    - Number of sentences in the summary
    - Summarization method (auto, extractive, llm)
    - Algorithm for extractive method (lsa, lexrank, textrank)
    - Language for stopwords (spanish, english)
    """
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found"
        )
    
    text = get_document_text(doc_id)
    if not text:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve document text"
        )
    
    # Validate parameters
    if request.method not in ["auto", "extractive", "llm"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Method must be one of: auto, extractive, llm"
        )
    
    if request.algorithm not in ["lsa", "lexrank", "textrank"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Algorithm must be one of: lsa, lexrank, textrank"
        )
    
    if request.language not in ["spanish", "english"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Language must be one of: spanish, english"
        )
    
    if request.sentence_count < 1 or request.sentence_count > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sentence count must be between 1 and 20"
        )
    
    # Generate new summary based on method
    if request.method in ["auto", "llm"]:
        # Try smart summary (with LLM if available)
        summary = generate_smart_summary(
            text,
            max_sentences=request.sentence_count,
            method=request.method
        )
        actual_method = "llm" if summary and "LLM-generated" in str(summary) else "extractive"
    else:
        # Force extractive method
        summary = generate_summary(
            text,
            sentence_count=request.sentence_count,
            algorithm=request.algorithm,
            language=request.language
        )
        actual_method = "extractive"
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summary. The document may be too short."
        )
    
    # Update stored summary
    doc.summary = summary
    update_document(doc)
    
    return SummaryResponse(
        doc_id=doc.id,
        original_name=doc.original_name,
        summary=summary,
        sentence_count=request.sentence_count,
        algorithm=request.algorithm,
        language=request.language,
        method=actual_method
    )


@router.post("/regenerate-all", response_model=BulkRegenerateResponse)
async def regenerate_all_summaries(request: Optional[RegenerateSummaryRequest] = None):
    """
    Regenerate summaries for all documents in the database.
    
    This is useful if you want to update summaries with a different algorithm
    or if some documents are missing summaries.
    """
    if request is None:
        request = RegenerateSummaryRequest()
    
    # Validate parameters
    if request.algorithm not in ["lsa", "lexrank", "textrank"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Algorithm must be one of: lsa, lexrank, textrank"
        )
    
    if request.language not in ["spanish", "english"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Language must be one of: spanish, english"
        )
    
    documents = list_documents()
    total = len(documents)
    successful = 0
    failed = 0
    errors = []
    
    for doc in documents:
        try:
            text = get_document_text(doc.id)
            if not text:
                failed += 1
                errors.append(f"{doc.original_name}: Could not retrieve text")
                continue
            
            summary = generate_summary(
                text,
                sentence_count=request.sentence_count,
                algorithm=request.algorithm,
                language=request.language
            )
            
            if summary:
                doc.summary = summary
                update_document(doc)
                successful += 1
            else:
                failed += 1
                errors.append(f"{doc.original_name}: Summary generation failed (document may be too short)")
        
        except Exception as e:
            failed += 1
            errors.append(f"{doc.original_name}: {str(e)}")
    
    return BulkRegenerateResponse(
        total_documents=total,
        successful=successful,
        failed=failed,
        errors=errors
    )
