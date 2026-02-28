from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse

from app.utils.file_utils import get_file_path, is_allowed_file
from app.utils.database import list_documents, get_document
from app.utils.schemas import UploadResponse, DocumentListItem, BatchUploadResponse, BatchUploadResult
from app.services.document_service import process_upload, remove_document

router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not allowed. Accepted: pdf, txt, docx, csv, xlsx",
        )

    try:
        doc = await process_upload(file)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}",
        )

    return UploadResponse(
        id=doc.id,
        filename=doc.filename,
        original_name=doc.original_name,
        file_type=doc.file_type,
        file_size=doc.file_size,
        upload_date=doc.upload_date,
        summary=doc.summary,
    )

@router.post("/upload/batch", response_model=BatchUploadResponse)
async def upload_multiple_documents(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided",
        )
    
    results = []
    successful = 0
    failed = 0
    
    for file in files:
        if not file.filename:
            results.append(BatchUploadResult(
                filename="<unknown>",
                status="error",
                error="No filename provided"
            ))
            failed += 1
            continue
        
        if not is_allowed_file(file.filename):
            results.append(BatchUploadResult(
                filename=file.filename,
                status="error",
                error="File type not allowed"
            ))
            failed += 1
            continue
        
        try:
            doc = await process_upload(file)
            results.append(BatchUploadResult(
                filename=file.filename,
                status="success",
                doc_id=doc.id,
                word_count=doc.word_count
            ))
            successful += 1
        except Exception as e:
            results.append(BatchUploadResult(
                filename=file.filename,
                status="error",
                error=str(e)
            ))
            failed += 1
    
    return BatchUploadResponse(
        total_files=len(files),
        successful=successful,
        failed=failed,
        results=results
    )


@router.get("", response_model=list[DocumentListItem])
async def list_all_documents():
    docs = list_documents()
    return [
        DocumentListItem(
            id=d.id,
            original_name=d.original_name,
            file_type=d.file_type,
            file_size=d.file_size,
            upload_date=d.upload_date,
            summary=d.summary,
            word_count=d.word_count,
        )
        for d in docs
    ]


@router.get("/{doc_id}/download")
async def download_document(doc_id: str, inline: bool = False):
    doc = get_document(doc_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    file_path = get_file_path(doc.filename)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk",
        )

    media_types = {
        "pdf": "application/pdf",
        "txt": "text/plain",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "csv": "text/csv",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    media_type = media_types.get(doc.file_type, "application/octet-stream")

    disposition = "inline" if inline else "attachment"
    headers = {
        "Content-Disposition": f'{disposition}; filename="{doc.original_name}"'
    }

    return FileResponse(
        path=str(file_path),
        filename=doc.original_name,
        media_type=media_type,
        headers=headers,
    )


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    success = remove_document(doc_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return {"message": "Document deleted successfully", "id": doc_id}
