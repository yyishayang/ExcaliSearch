from fastapi import APIRouter, HTTPException, Query

from app.utils.schemas import SearchResponse, SearchResult
from app.search.search_engine import search

router = APIRouter(prefix="/api", tags=["Search"])

@router.get("/search", response_model=SearchResponse)
async def search_documents(q: str = Query(..., min_length=1, description="Search query")):
    """
    Search for documents matching the query.
    Returns results with highlighted snippets and relevance scores.
    """
    try:
        results = search(q)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search error: {str(e)}",
        )

    return SearchResponse(
        query=q,
        total_results=len(results),
        results=[
            SearchResult(
                doc_id=r["doc_id"],
                filename=r["filename"],
                original_name=r["original_name"],
                snippet=r["snippet"],
                score=r["score"],
                file_type=r["file_type"],
            )
            for r in results
        ],
    )
