"""
Whoosh indexing service — manages the full-text search index.
"""

import os
from pathlib import Path

from whoosh import index
from whoosh.fields import Schema, TEXT, ID, STORED

from app.utils.file_utils import INDEX_DIR

# Whoosh schema definition
SCHEMA = Schema(
    doc_id=ID(stored=True, unique=True),
    filename=TEXT(stored=True),
    content=TEXT(stored=True),
)


def init_index() -> index.Index:
    """
    Initialize or open the Whoosh index.
    Creates the index directory and schema if they don't exist.
    """
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    if index.exists_in(str(INDEX_DIR)):
        return index.open_dir(str(INDEX_DIR))
    else:
        return index.create_in(str(INDEX_DIR), SCHEMA)


def get_index() -> index.Index:
    """Get or create the Whoosh index."""
    return init_index()


def add_to_index(doc_id: str, content: str, filename: str):
    """Add or update a document in the index."""
    ix = get_index()
    writer = ix.writer()
    # Use update_document so re-indexing the same doc_id replaces it
    writer.update_document(
        doc_id=doc_id,
        filename=filename,
        content=content,
    )
    writer.commit()


def delete_from_index(doc_id: str):
    """Remove a document from the index by its ID."""
    ix = get_index()
    writer = ix.writer()
    writer.delete_by_term("doc_id", doc_id)
    writer.commit()
