"""
Search engine facade supporting normal (Whoosh) and semantic modes.
"""

from whoosh.highlight import ContextFragmenter, UppercaseFormatter
from whoosh.qparser import MultifieldParser, OrGroup

from app.services.indexing_service import get_index
from app.services.semantic_service import semantic_search
from app.utils.database import get_document


def keyword_search(query: str, limit: int = 20) -> list[dict]:
    """Keyword search using Whoosh."""
    ix = get_index()
    results_list: list[dict] = []

    with ix.searcher() as searcher:
        parser = MultifieldParser(
            ["content", "filename"], schema=ix.schema, group=OrGroup
        )
        parsed_query = parser.parse(query)
        results = searcher.search(parsed_query, limit=limit)

        results.formatter = UppercaseFormatter()
        results.fragmenter = ContextFragmenter(maxchars=200, surround=80)

        for hit in results:
            doc_id = hit["doc_id"]
            snippet = hit.highlights("content", top=3)

            doc_meta = get_document(doc_id)
            original_name = doc_meta.original_name if doc_meta else hit["filename"]
            file_type = doc_meta.file_type if doc_meta else ""
            summary = doc_meta.summary if doc_meta else ""

            if not snippet:
                content = hit.get("content", "")
                snippet = content[:200] + "..." if len(content) > 200 else content

            results_list.append(
                {
                    "doc_id": doc_id,
                    "filename": hit["filename"],
                    "original_name": original_name,
                    "snippet": snippet,
                    "summary": summary,
                    "score": round(float(hit.score), 4),
                    "file_type": file_type,
                }
            )

    return results_list


def search(query: str, limit: int = 20) -> list[dict]:
    """Backward-compatible default search (semantic mode)."""
    return search_by_mode(query, mode="semantic", limit=limit)


def search_by_mode(query: str, mode: str = "semantic", limit: int = 20) -> list[dict]:
    """Dispatch search strategy based on explicit mode."""
    mode = (mode or "semantic").strip().lower()

    if mode == "normal":
        return keyword_search(query, limit=limit)
    if mode == "semantic":
        try:
            return semantic_search(query, limit=limit)
        except Exception:
            # Do not fail request if embedding model/cache is unavailable.
            return keyword_search(query, limit=limit)
    if mode == "hybrid":
        return hybrid_search(query, limit=limit)

    raise ValueError(f"Unsupported search mode: {mode}")


def hybrid_search(query: str, limit: int = 20, use_reranking: bool = False) -> list[dict]:
    """
    Búsqueda híbrida que combina resultados semánticos + keywords.
    Fusiona ambos con pesos para mejorar recall y precisión.
    
    Args:
        query: Consulta de búsqueda
        limit: Número máximo de resultados
        use_reranking: Si activar reranking en la parte semántica (más lento pero más preciso)
    """
    # Obtener resultados de ambos métodos
    try:
        semantic_results = semantic_search(query, limit=limit * 2, use_reranking=use_reranking)
    except Exception:
        semantic_results = []
    
    keyword_results = keyword_search(query, limit=limit * 2)
    
    # Fusionar resultados con ponderación
    # Semantic: 70%, Keywords: 30%
    combined = {}
    
    for result in semantic_results:
        doc_id = result["doc_id"]
        combined[doc_id] = {
            **result,
            "score": result["score"] * 0.7,
            "search_method": "hybrid"
        }
    
    for result in keyword_results:
        doc_id = result["doc_id"]
        # Normalizar score de keyword [0, ~10] a [0, 1]
        normalized_score = min(result["score"] / 10, 1.0)
        
        if doc_id in combined:
            # Ya existe: sumar el score ponderado de keywords
            combined[doc_id]["score"] += normalized_score * 0.3
            combined[doc_id]["score"] = round(combined[doc_id]["score"], 4)
        else:
            # Nuevo: agregar con peso de keywords
            combined[doc_id] = {
                **result,
                "score": round(normalized_score * 0.3, 4),
                "search_method": "hybrid"
            }
    
    # Ordenar por score combinado y devolver top N
    final = sorted(combined.values(), key=lambda x: x["score"], reverse=True)
    return final[:limit]
