from fastapi import APIRouter, BackgroundTasks
from app.services.semantic_service import _reindex_existing_documents, init_semantic_index, delete_document_chunks
from app.services.indexing_service import delete_from_index
from app.utils.database import list_documents, delete_document as db_delete_document
from app.utils.file_utils import get_file_path

router = APIRouter(prefix="/api/semantic", tags=["Semantic"])

_reindex_running = False

def _run_reindex():
    global _reindex_running
    _reindex_running = True
    try:
        # Clear all existing vectors first
        collection = init_semantic_index()
        results = collection.get()
        ids = results.get("ids", [])
        if ids:
            for i in range(0, len(ids), 1000):
                collection.delete(ids=ids[i : i + 1000])
        # Re-index from metadata.json
        _reindex_existing_documents()
    finally:
        _reindex_running = False

@router.post("/reindex")
async def reindex_all(background_tasks: BackgroundTasks):
    """
    Borra el índice semántico actual y lo reconstruye desde la base de datos de metadatos.
    Se ejecuta en background para no bloquear la respuesta.
    """
    global _reindex_running
    if _reindex_running:
        return {"status": "already_running", "message": "Re-indexado ya en curso, espera un momento."}

    background_tasks.add_task(_run_reindex)
    return {"status": "started", "message": "Re-indexado iniciado en background. En unos segundos la búsqueda semántica estará actualizada."}

@router.post("/cleanup")
async def cleanup_orphans():
    """
    Detecta y elimina documentos cuyo fichero ya no existe en disco.
    Limpia metadata.json, ChromaDB y el índice Whoosh.
    """
    docs = list_documents()
    removed = []
    errors = []

    for doc in docs:
        file_path = get_file_path(doc.filename)
        if not file_path.exists():
            try:
                delete_document_chunks(doc.id)
                delete_from_index(doc.id)
                db_delete_document(doc.id)
                removed.append({"id": doc.id, "original_name": doc.original_name})
            except Exception as exc:
                errors.append({"id": doc.id, "original_name": doc.original_name, "error": str(exc)})

    if not removed and not errors:
        return {"status": "ok", "message": "Todo está sincronizado, no hay ficheros huérfanos.", "removed": [], "errors": []}

    return {
        "status": "done",
        "message": f"Limpieza completada: {len(removed)} documento(s) eliminado(s).",
        "removed": removed,
        "errors": errors,
    }

@router.get("/debug")
async def debug_search(q: str = "test"):
    """
    Ejecuta la búsqueda semántica SIN filtro de threshold y devuelve los scores reales
    de todos los documentos. Útil para diagnosticar por qué un documento no aparece.
    """
    from app.services.semantic_service import (
        init_semantic_index,
        vector_distance_to_score,
        MIN_SCORE_THRESHOLD,
    )

    collection = init_semantic_index()

    # Total de chunks indexados
    total = collection.count()
    if total == 0:
        return {"query": q, "total_chunks": 0, "threshold": MIN_SCORE_THRESHOLD, "results": [],
                "warning": "ChromaDB está vacío. Reinicia el backend o sube un documento para indexar."}

    try:
        raw = collection.query(
            query_texts=[q],
            n_results=min(total, 50),
            include=["metadatas", "distances"],
        )
    except Exception as exc:
        import traceback
        return {"query": q, "error": str(exc), "traceback": traceback.format_exc()}

    metadatas = raw.get("metadatas", [[]])[0]
    distances = raw.get("distances", [[]])[0]

    # Agrupar por doc y quedarnos con el mejor chunk por doc
    best: dict = {}
    for meta, dist in zip(metadatas, distances):
        if not meta:
            continue
        doc_id = meta.get("doc_id", "?")
        score = round(vector_distance_to_score(dist), 4)
        if doc_id not in best or score > best[doc_id]["score"]:
            best[doc_id] = {
                "doc_id": doc_id,
                "original_name": meta.get("original_name", meta.get("filename", "?")),
                "file_type": meta.get("file_type", ""),
                "score": score,
                "above_threshold": score >= MIN_SCORE_THRESHOLD,
            }

    results = sorted(best.values(), key=lambda x: x["score"], reverse=True)

    return {
        "query": q,
        "total_chunks_in_chromadb": total,
        "current_threshold": MIN_SCORE_THRESHOLD,
        "results": results,
    }
