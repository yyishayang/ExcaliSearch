import json
import os
from pathlib import Path
from typing import Optional, List
from threading import Lock

from app.utils.models import DocumentMetadata
from app.utils.file_utils import DATA_DIR

DB_FILE = DATA_DIR / "metadata.json"
_lock = Lock()


def _ensure_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_FILE.exists():
        DB_FILE.write_text(json.dumps({"documents": {}}, indent=2))


def load_db() -> dict:
    _ensure_db()
    with _lock:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)


def save_db(data: dict):
    _ensure_db()
    with _lock:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def add_document(doc: DocumentMetadata):
    db = load_db()
    db["documents"][doc.id] = doc.model_dump()
    save_db(db)


def get_document(doc_id: str) -> Optional[DocumentMetadata]:
    db = load_db()
    raw = db["documents"].get(doc_id)
    if raw is None:
        return None
    return DocumentMetadata(**raw)


def list_documents() -> List[DocumentMetadata]:
    db = load_db()
    docs = [DocumentMetadata(**v) for v in db["documents"].values()]
    docs.sort(key=lambda d: d.upload_date, reverse=True)
    return docs


def delete_document(doc_id: str) -> bool:
    db = load_db()
    if doc_id in db["documents"]:
        del db["documents"][doc_id]
        save_db(db)
        return True
    return False


def find_by_hash(file_hash: str) -> Optional[DocumentMetadata]:
    db = load_db()
    for v in db["documents"].values():
        if v.get("hash") == file_hash:
            return DocumentMetadata(**v)
    return None
