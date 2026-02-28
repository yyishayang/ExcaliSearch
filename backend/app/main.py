from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.utils.file_utils import ensure_dirs
from app.services.indexing_service import init_index
from app.services.semantic_service import ensure_semantic_index_up_to_date
from app.services.document_service import cleanup_orphaned_documents
from app.api.routes_documents import router as documents_router
from app.api.routes_search import router as search_router
from app.api.routes_metadata import router as metadata_router
from app.api.routes_semantic import router as semantic_router

app = FastAPI(
    title="ExcaliSearch",
    description="Document search platform — upload, index, and search documents",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)
app.include_router(documents_router)
app.include_router(metadata_router)
app.include_router(semantic_router)

@app.on_event("startup")
async def startup():
    """Initialize storage directories and search index on startup."""
    ensure_dirs()
    init_index()
    try:
        ensure_semantic_index_up_to_date()
    except Exception as exc:
        # Keep backend available even if semantic dependencies are missing.
        print(f"[semantic] startup warning: {exc}")

    try:
        cleanup_orphaned_documents()
    except Exception as exc:
        print(f"[startup] cleanup warning: {exc}")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "ExcaliSearch"}
