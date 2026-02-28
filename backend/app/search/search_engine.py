"""
Whoosh-powered search engine with highlighted snippet extraction.
"""

from whoosh.qparser import MultifieldParser, OrGroup
from whoosh.highlight import UppercaseFormatter, ContextFragmenter

from app.services.indexing_service import get_index
from app.utils.database import get_document


def search(query: str, limit: int = 20) -> list[dict]:
    """
    Search the Whoosh index for documents matching the query.

    Returns a list of dicts with:
      - doc_id: document ID
      - filename: stored filename
      - original_name: user's original filename
      - snippet: highlighted text fragment
      - score: relevance score
      - file_type: document type
    """
    ix = get_index()
    results_list = []

    with ix.searcher() as searcher:
        parser = MultifieldParser(
            ["content", "filename"], schema=ix.schema, group=OrGroup
        )
        parsed_query = parser.parse(query)
        results = searcher.search(parsed_query, limit=limit)

        # Configure highlighter
        results.formatter = UppercaseFormatter()
        results.fragmenter = ContextFragmenter(maxchars=200, surround=80)

        for hit in results:
            doc_id = hit["doc_id"]
            snippet = hit.highlights("content", top=3)

            # Get metadata to include original_name and file_type
            doc_meta = get_document(doc_id)
            original_name = doc_meta.original_name if doc_meta else hit["filename"]
            file_type = doc_meta.file_type if doc_meta else ""

            if not snippet:
                # Fallback: use first 200 chars of content
                content = hit.get("content", "")
                snippet = content[:200] + "…" if len(content) > 200 else content

            results_list.append(
                {
                    "doc_id": doc_id,
                    "filename": hit["filename"],
                    "original_name": original_name,
                    "snippet": snippet,
                    "score": round(hit.score, 4),
                    "file_type": file_type,
                }
            )

    return results_list
