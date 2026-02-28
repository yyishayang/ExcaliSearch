"""
Semantic search service powered by ChromaDB + sentence-transformers.
"""

from __future__ import annotations

import os
from math import exp
from pathlib import Path
from threading import Lock
from typing import Any

from app.utils.database import list_documents
from app.utils.file_utils import get_file_path, DATA_DIR
from app.services.cleaning_service import clean_text
from app.services.extraction_service import extract_text

# El modelo sugerido era all-MiniLM-L6-v2, pero para permitir el cruce ES-EN "contrato" -> "agreement" 
# de forma 100% nativa sin diccionarios trampa, usamos un modelo multilingüe de la misma familia.
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "documents"
CHROMA_DIR = DATA_DIR / "chroma_db"
HF_CACHE_DIR = DATA_DIR / "hf_cache"

MAX_CHUNK_WORDS = 150
CHUNK_OVERLAP_WORDS = 30

_state_lock = Lock()
_client = None
_collection = None
_embedding_function = None


def _configure_hf_cache():
    """
    Force Hugging Face/SentenceTransformers cache inside project data dir.
    Avoids Windows issues when ~/.cache is not a normal directory.
    """
    HF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(HF_CACHE_DIR))
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(HF_CACHE_DIR / "hub"))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(HF_CACHE_DIR / "transformers"))
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    os.environ.setdefault(
        "SENTENCE_TRANSFORMERS_HOME",
        str(HF_CACHE_DIR / "sentence_transformers"),
    )


def _get_embedding_function():
    """Obtiene la función de embeddings de SentenceTransformers para inyectar en ChromaDB."""
    global _embedding_function
    if _embedding_function is None:
        _configure_hf_cache()
        from chromadb.utils import embedding_functions
        
        _embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME
        )
    return _embedding_function


def init_semantic_index():
    """Inicializa ChromaDB y crea la colección si no existe iterando la distancia coseno."""
    global _client, _collection

    _configure_hf_cache()
    try:
        import chromadb
    except ImportError as exc:
        raise RuntimeError(
            "Missing semantic search dependencies. "
            "Install with: pip install chromadb sentence-transformers"
        ) from exc

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    with _state_lock:
        if _client is None:
            _client = chromadb.PersistentClient(path=str(CHROMA_DIR))

        if _collection is None:
            ef = _get_embedding_function()
            _collection = _client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=ef,
                metadata={"hnsw:space": "cosine"}, # Distancia coseno como se pide
            )

    return _collection


def _chunk_text(text: str) -> list[str]:
    """Parte el texto en ventanas de palabras superpuestas."""
    words = text.split()
    if not words:
        return []

    if len(words) <= MAX_CHUNK_WORDS:
        return [text.strip()]

    step = max(1, MAX_CHUNK_WORDS - CHUNK_OVERLAP_WORDS)
    chunks: list[str] = []

    for start in range(0, len(words), step):
        window = words[start : start + MAX_CHUNK_WORDS]
        if not window:
            continue
        chunk = " ".join(window).strip()
        if chunk:
            chunks.append(chunk)

    if len(chunks) >= 2 and len(chunks[-1].split()) < 30:
        chunks[-2] = f"{chunks[-2]} {chunks[-1]}"
        chunks.pop()

    return chunks


def vector_distance_to_score(distance: float) -> float:
    """Convierte la distancia coseno (0=idéntico, 2=opuesto) a un % de similitud [0, 1]."""
    return max(0.0, min(1.0, (2.0 - float(distance)) / 2.0))


def _reindex_existing_documents():
    """Reconstruye el índice vector leyendo todos los documentos de la BD sqlite."""
    docs = list_documents()
    for doc in docs:
        file_path = get_file_path(doc.filename)
        if not file_path.exists():
            continue
        try:
            raw_text, _ = extract_text(file_path, doc.file_type)
            cleaned = clean_text(raw_text)
            upsert_document_chunks(
                doc_id=doc.id,
                filename=doc.filename,
                original_name=doc.original_name,
                file_type=doc.file_type,
                text=cleaned,
            )
        except Exception as exc:
            print(f"[semantic] reindex skipped for {doc.id}: {exc}")


def ensure_semantic_index_up_to_date():
    """
    Asegura que la colección esté inicializada en el arranque.
    Como la validación de config se quitó para mantenerlo limpio,
    si se desea borrar todo hay que purgar el directorio `chroma_db`.
    """
    init_semantic_index()


def upsert_document_chunks(
    doc_id: str,
    filename: str,
    original_name: str,
    file_type: str,
    text: str,
):
    """
    Corta el documento en trozos (chunks) y los guarda en ChromaDB.
    Chroma calcula los embeddings automáticamente usando la embedding_function inyectada.
    """
    if not text.strip():
        return

    collection = init_semantic_index()

    chunks = _chunk_text(text)
    if not chunks:
        return

    # Limpiamos trozos viejos para no duplicar si estuviéramos re-indexando el mismo doc
    collection.delete(where={"doc_id": doc_id})

    ids = [f"{doc_id}:{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "doc_id": doc_id,
            "filename": filename,
            "original_name": original_name,
            "file_type": file_type,
            "chunk_index": i,
        }
        for i in range(len(chunks))
    ]

    collection.upsert(
        ids=ids,
        documents=chunks,
        metadatas=metadatas,
    )


def delete_document_chunks(doc_id: str):
    """Borra todos los embeddings de un documento usando su identificador."""
    collection = init_semantic_index()
    collection.delete(where={"doc_id": doc_id})


def semantic_search(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """
    Busca los chunks más similares semánticamente a la consulta.
    Devuelve los mejores resultados (1 por cada documento como máximo).
    """
    if not query.strip():
        return []

    collection = init_semantic_index()

    # Hacemos la query directamente a ChromaDB; la embedding function codifica el input "query" por sí misma.
    # Pedimos más resultados de los solicitados por si múltiples chunks son del mismo documento.
    raw = collection.query(
        query_texts=[query],
        n_results=limit * 10,
        include=["documents", "metadatas", "distances"],
    )

    documents = raw.get("documents", [[]])[0]
    metadatas = raw.get("metadatas", [[]])[0]
    distances = raw.get("distances", [[]])[0]

    best_by_doc: dict[str, dict[str, Any]] = {}

    for chunk_text, meta, distance in zip(documents, metadatas, distances):
        if not meta:
            continue

        doc_id = meta.get("doc_id")
        if not doc_id:
            continue

        score = vector_distance_to_score(distance)

        # Si ya teníamos un chunk de este doc, nos quedamos con el que tenga mayor similitud (score max)
        prev = best_by_doc.get(doc_id)
        if prev and score <= float(prev["score"]):
            continue

        snippet = (chunk_text or "").strip()
        if len(snippet) > 260:
            snippet = snippet[:257] + "..."

        best_by_doc[doc_id] = {
            "doc_id": doc_id,
            "filename": meta.get("filename", ""),
            "original_name": meta.get("original_name", meta.get("filename", "")),
            "snippet": snippet,
            "score": round(score, 4),    # Guardamos el score con el tip de % [0, 1] 
            "file_type": meta.get("file_type", ""),
        }

    # Ordenamos de mayor a menor score total y cortamos al límite real
    final_results = sorted(best_by_doc.values(), key=lambda c: c["score"], reverse=True)
    return final_results[:limit]
