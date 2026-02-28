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
    elif file_type == "xlsx":
        return _extract_xlsx(file_path)
    elif file_type == "csv":
        return _extract_csv(file_path)
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


def _extract_xlsx(file_path: Path) -> tuple[str, None]:
    """Extract text from XLSX using openpyxl. Reads all sheets."""
    import openpyxl

    wb = openpyxl.load_workbook(str(file_path), read_only=True, data_only=True)
    lines = []
    for sheet in wb.worksheets:
        lines.append(f"[Sheet: {sheet.title}]")
        for row in sheet.iter_rows(values_only=True):
            cells = [str(c) if c is not None else "" for c in row]
            if any(c.strip() for c in cells):
                lines.append("\t".join(cells))
    wb.close()
    return "\n".join(lines), None


def _extract_csv(file_path: Path) -> tuple[str, None]:
    import csv

    for encoding in ["utf-8", "latin-1", "cp1252"]:
        try:
            with open(file_path, newline="", encoding=encoding) as f:
                reader = csv.reader(f)
                lines = ["\t".join(row) for row in reader if any(cell.strip() for cell in row)]
            return "\n".join(lines), None
        except (UnicodeDecodeError, ValueError):
            continue

    raw = file_path.read_bytes().decode("utf-8", errors="ignore")
    return raw, None
