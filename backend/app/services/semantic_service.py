from __future__ import annotations

import os
from math import exp
from pathlib import Path
from threading import Lock
from typing import Any

try:
    import numpy as np
except ImportError:
    np = None  # Reranking no estará disponible sin numpy

from app.utils.database import list_documents
from app.utils.file_utils import get_file_path, DATA_DIR
from app.services.cleaning_service import clean_text
from app.services.extraction_service import extract_text

# El modelo sugerido era all-MiniLM-L6-v2, pero para permitir el cruce ES-EN "contrato" -> "agreement" 
# de forma 100% nativa sin diccionarios trampa, usamos un modelo multilingüe de la misma familia.
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
RERANKER_MODEL_NAME = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"  # Reranking para mejorar precisión
COLLECTION_NAME = "documents"
CHROMA_DIR = DATA_DIR / "chroma_db"
HF_CACHE_DIR = DATA_DIR / "hf_cache"

MAX_CHUNK_WORDS = 150
CHUNK_OVERLAP_WORDS = 30

_state_lock = Lock()
_client = None
_collection = None
_embedding_function = None
_reranker_model = None


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


def _get_reranker_model():
    """Carga el modelo Cross-Encoder para reranking de resultados."""
    global _reranker_model
    if _reranker_model is None:
        _configure_hf_cache()
        try:
            from sentence_transformers import CrossEncoder
            _reranker_model = CrossEncoder(RERANKER_MODEL_NAME)
        except ImportError:
            print("[semantic] CrossEncoder no disponible. Instala: pip install sentence-transformers")
            _reranker_model = False  # Marker to avoid retrying
        except Exception as exc:
            print(f"[semantic] Error cargando reranker: {exc}")
            _reranker_model = False
    return _reranker_model if _reranker_model is not False else None


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


def _chunk_text(text: str, title: str = "") -> list[str]:
    """
    Parte el texto en ventanas de palabras superpuestas.
    Añade el título al principio de cada chunk para mejorar drásticamente
    la representación semántica, especialmente en textos cortos.
    """
    words = text.split()
    if not words:
        return []

    prefix = f"Título del documento: {title}\nContenido:\n" if title else ""

    if len(words) <= MAX_CHUNK_WORDS:
        return [prefix + text.strip()]

    step = max(1, MAX_CHUNK_WORDS - CHUNK_OVERLAP_WORDS)
    chunks: list[str] = []

    for start in range(0, len(words), step):
        window = words[start : start + MAX_CHUNK_WORDS]
        if not window:
            continue
        chunk_body = " ".join(window).strip()
        if chunk_body:
            chunks.append(prefix + chunk_body)

    if len(chunks) >= 2 and len(chunks[-1].split()) < 30:
        # Unir el último trozo pequeño al anterior
        last_body = chunks[-1].replace(prefix, "", 1).strip()
        chunks[-2] = f"{chunks[-2]} {last_body}"
        chunks.pop()

    return chunks


def vector_distance_to_score(distance: float) -> float:
    """Convierte la distancia coseno (0=idéntico, 2=opuesto) a un % de similitud [0, 1]."""
    return max(0.0, min(1.0, (2.0 - float(distance)) / 2.0))


def _enhance_query(query: str) -> str:
    """Mejora la consulta para búsqueda semántica."""
    query = query.strip()
    
    if "e5" in EMBEDDING_MODEL_NAME.lower():
        if not query.lower().startswith(("query:", "search:", "find:")):
            query = f"query: {query}"
    
    return query


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
    Inicializa ChromaDB y asegura que todos los documentos de metadata.json
    estén indexados. Si ChromaDB fue borrado o está vacío, re-indexa automáticamente
    los documentos que falten en el índice vectorial.
    """
    collection = init_semantic_index()

    # Obtener qué doc_ids están ya en ChromaDB
    try:
        existing = collection.get(include=["metadatas"])
        indexed_ids: set[str] = {
            m.get("doc_id")
            for m in (existing.get("metadatas") or [])
            if m and m.get("doc_id")
        }
    except Exception:
        indexed_ids = set()

    # Comprobar cuáles de los documentos en metadata.json no están en ChromaDB
    docs_to_index = [
        doc for doc in list_documents()
        if doc.id not in indexed_ids
    ]

    if not docs_to_index:
        return  # Todo está sincronizado

    for doc in docs_to_index:
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
            print(f"[semantic] error indexando {doc.id}: {exc}")


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

    chunks = _chunk_text(text, title=original_name)
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


MIN_SCORE_THRESHOLD = 0.35
CANDIDATES_FOR_RERANKING = 15


def semantic_search(
    query: str, 
    limit: int = 20, 
    use_reranking: bool = True,
    file_type_filter: str | None = None
) -> list[dict[str, Any]]:
    """
    Busca los chunks más similares semánticamente a la consulta.
    Devuelve los mejores resultados (1 por cada documento como máximo).
    
    Args:
        query: Consulta de búsqueda
        limit: Número máximo de resultados
        use_reranking: Aplicar reranking con Cross-Encoder (mejora precisión)
        file_type_filter: Filtrar por tipo de archivo (pdf, txt, csv, etc.)
    """
    if not query.strip():
        return []

    enhanced_query = _enhance_query(query)
    collection = init_semantic_index()

    total_chunks = collection.count()
    if total_chunks == 0:
        return []

    n_candidates = CANDIDATES_FOR_RERANKING if use_reranking else limit * 10
    n_results = min(n_candidates, total_chunks)

    # Hacemos la query directamente a ChromaDB; la embedding function codifica el input "query" por sí misma.
    raw = collection.query(
        query_texts=[enhanced_query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    documents = raw.get("documents", [[]])[0]
    metadatas = raw.get("metadatas", [[]])[0]
    distances = raw.get("distances", [[]])[0]

    best_by_doc: dict[str, dict[str, Any]] = {}
    filtered_count = 0

    # Recolectar candidatos (antes del reranking)
    candidates: list[dict[str, Any]] = []
    
    for chunk_text, meta, distance in zip(documents, metadatas, distances):
        if not meta:
            continue

        doc_id = meta.get("doc_id")
        if not doc_id:
            continue

        from app.utils.database import get_document
        doc_meta = get_document(doc_id)
        if doc_meta is None:
            continue
        
        # Filtro por tipo de archivo
        if file_type_filter and meta.get("file_type") != file_type_filter:
            continue

        score = vector_distance_to_score(distance)

        # Descartar resultados por debajo del umbral mínimo de relevancia semántica
        if score < MIN_SCORE_THRESHOLD:
            filtered_count += 1
            continue

        snippet = (chunk_text or "").strip()
        if len(snippet) > 260:
            snippet = snippet[:257] + "..."

        candidates.append({
            "doc_id": doc_id,
            "filename": meta.get("filename", ""),
            "original_name": meta.get("original_name", meta.get("filename", "")),
            "snippet": snippet,
            "summary": doc_meta.summary if doc_meta else "",
            "chunk_text": chunk_text,  # Guardamos el texto completo para reranking
            "score": round(score, 4),
            "file_type": meta.get("file_type", ""),
        })
    
    # Aplicar reranking si está habilitado
    if use_reranking and candidates:
        reranker = _get_reranker_model()
        if reranker:
            # Preparar pares (query, chunk) para el reranker
            pairs = [[query, c["chunk_text"]] for c in candidates]
            
            # Obtener scores del cross-encoder (más precisos que embeddings)
            try:
                rerank_scores = reranker.predict(pairs)
                
                # Actualizar scores con los del reranker
                for i, candidate in enumerate(candidates):
                    # Convertir score de cross-encoder [-10, 10] a [0, 1]
                    normalized_score = 1 / (1 + float(np.exp(-rerank_scores[i])))
                    candidate["rerank_score"] = round(normalized_score, 4)
                    # Combinar score original (40%) + reranking (60%)
                    candidate["score"] = round(
                        0.4 * candidate["score"] + 0.6 * normalized_score, 4
                    )
                
            except Exception as exc:
                print(f"[semantic_search] Error en reranking: {exc}")
    
    # Agrupar por documento y quedarnos con el mejor chunk
    for candidate in candidates:
        doc_id = candidate["doc_id"]
        prev = best_by_doc.get(doc_id)
        if prev and candidate["score"] <= float(prev["score"]):
            continue
        
        # Eliminar chunk_text antes de guardar (ya no lo necesitamos)
        candidate.pop("chunk_text", None)
        best_by_doc[doc_id] = candidate

    # Ordenamos de mayor a menor score total y cortamos al límite real
    final_results = sorted(best_by_doc.values(), key=lambda c: c["score"], reverse=True)
    
    return final_results[:limit]
