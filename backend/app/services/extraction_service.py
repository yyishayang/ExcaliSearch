"""
Text extraction service — handles PDF, TXT, and DOCX files.
"""

from pathlib import Path


def extract_text(file_path: Path, file_type: str) -> tuple[str, int | None]:
    """
    Extract text from a document file.
    Returns (text, page_count).
    page_count is only set for PDFs; None otherwise.
    """
    file_type = file_type.lower()

    if file_type == "pdf":
        return _extract_pdf(file_path)
    elif file_type == "txt":
        return _extract_txt(file_path)
    elif file_type == "docx":
        return _extract_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def _extract_pdf(file_path: Path) -> tuple[str, int]:
    """Extract text from PDF using PyMuPDF."""
    import fitz  # PyMuPDF

    doc = fitz.open(str(file_path))
    pages = []
    for page in doc:
        pages.append(page.get_text())
    page_count = len(doc)
    doc.close()
    return "\n".join(pages), page_count


def _extract_txt(file_path: Path) -> tuple[str, None]:
    """Read plain text file."""
    # Try UTF-8 first, fall back to latin-1
    for encoding in ["utf-8", "latin-1", "cp1252"]:
        try:
            text = file_path.read_text(encoding=encoding)
            return text, None
        except (UnicodeDecodeError, ValueError):
            continue
    # Last resort: read as bytes and decode ignoring errors
    raw = file_path.read_bytes()
    return raw.decode("utf-8", errors="ignore"), None


def _extract_docx(file_path: Path) -> tuple[str, None]:
    """Extract text from DOCX using python-docx."""
    from docx import Document

    doc = Document(str(file_path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs), None
