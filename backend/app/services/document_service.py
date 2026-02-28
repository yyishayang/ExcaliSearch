"""
Document service — orchestrates the upload pipeline.
"""

from fastapi import UploadFile

from app.utils.models import DocumentMetadata
from app.utils.file_utils import (
    save_upload,
    get_file_path,
    get_file_extension,
    delete_file,
)
from app.utils.hash_utils import compute_sha256
from app.utils.database import (
    add_document,
    get_document,
    delete_document as db_delete,
    find_by_hash,
)
from app.services.extraction_service import extract_text
from app.services.cleaning_service import clean_text
from app.services.indexing_service import add_to_index, delete_from_index
from app.services.semantic_service import (
    upsert_document_chunks,
    delete_document_chunks,
)
from app.services.summary_service import generate_preview


# In-memory text cache: doc_id -> full text
_text_cache: dict[str, str] = {}


async def process_upload(file: UploadFile) -> DocumentMetadata:
    # 1. Save file
    stored_name, file_bytes = await save_upload(file)
    file_type = get_file_extension(file.filename)

    # 2. Hash check
    file_hash = compute_sha256(file_bytes)
    existing = find_by_hash(file_hash)
    if existing:
        # Remove the just-saved duplicate file
        delete_file(stored_name)
        return existing

    # 3. Extract text
    file_path = get_file_path(stored_name)
    raw_text, page_count = extract_text(file_path, file_type)

    # 4. Clean text
    cleaned = clean_text(raw_text)

    # 5. Build metadata
    word_count = len(cleaned.split()) if cleaned else 0
    preview = generate_preview(cleaned)

    doc = DocumentMetadata(
        filename=stored_name,
        original_name=file.filename,
        file_type=file_type,
        file_size=len(file_bytes),
        hash=file_hash,
        text_preview=preview,
        page_count=page_count,
        word_count=word_count,
    )

    # 6. Index in Whoosh + semantic vector index
    add_to_index(doc.id, cleaned, file.filename)
    try:
        upsert_document_chunks(
            doc_id=doc.id,
            filename=stored_name,
            original_name=file.filename,
            file_type=file_type,
            text=cleaned,
        )
    except Exception as exc:
        # Semantic indexing should not block upload.
        print(f"[semantic] failed to index document {doc.id}: {exc}")

    # 7. Persist metadata
    add_document(doc)

    # 8. Cache text
    _text_cache[doc.id] = cleaned

    return doc


def get_document_text(doc_id: str) -> str | None:
    """
    Retrieve full text for a document.
    First checks in-memory cache, then re-extracts from file.
    """
    # Check cache
    if doc_id in _text_cache:
        return _text_cache[doc_id]

    # Re-extract from file
    doc = get_document(doc_id)
    if doc is None:
        return None

    file_path = get_file_path(doc.filename)
    if not file_path.exists():
        return None

    raw_text, _ = extract_text(file_path, doc.file_type)
    cleaned = clean_text(raw_text)
    _text_cache[doc_id] = cleaned
    return cleaned


def remove_document(doc_id: str) -> bool:
    """
    Remove a document completely:
    - Delete from index
    - Delete file from storage
    - Delete from database
    - Remove from text cache
    """
    doc = get_document(doc_id)
    if doc is None:
        return False

    delete_from_index(doc_id)
    try:
        delete_document_chunks(doc_id)
    except Exception as exc:
        print(f"[semantic] failed to delete document {doc_id}: {exc}")
    delete_file(doc.filename)
    db_delete(doc_id)
    _text_cache.pop(doc_id, None)

    return True


def cleanup_orphaned_documents() -> list[str]:
    """
    Detecta y elimina documentos cuyo fichero ya no existe en disco.
    Se llama automáticamente al arrancar el servidor.
    Devuelve la lista de doc_ids eliminados.
    """
    from app.utils.database import list_documents
    removed_ids: list[str] = []

    for doc in list_documents():
        if not get_file_path(doc.filename).exists():
            try:
                delete_from_index(doc.id)
                delete_document_chunks(doc.id)
                db_delete(doc.id)
                _text_cache.pop(doc.id, None)
                removed_ids.append(doc.id)
                print(f"[startup] removed orphan: {doc.original_name} ({doc.id})")
            except Exception as exc:
                print(f"[startup] could not remove orphan {doc.id}: {exc}")

    return removed_ids
