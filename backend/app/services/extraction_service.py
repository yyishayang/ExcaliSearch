"""
Text extraction service — handles PDF, TXT, DOCX, XLSX and CSV files.

OCR support
-----------
When the environment variable ``EXCALISEARCH_OCR=1`` is set, **images embedded
inside PDF pages** are extracted by PyMuPDF and passed to Tesseract OCR via
*pytesseract* + *Pillow*.  The recognised text is appended to the native text
already extracted from the page, so both kinds of content are indexed together.

Requirements when OCR is enabled
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Tesseract OCR installed and on PATH  (https://github.com/UB-Mannheim/tesseract/wiki)
* Python packages: pytesseract, Pillow  (already in requirements.txt)

Note: pdf2image and Poppler are NOT required — images are extracted directly
from the PDF by PyMuPDF without converting pages to raster images.
"""

import io
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def _ocr_enabled() -> bool:
    return os.environ.get("EXCALISEARCH_OCR", "0").strip() == "1"


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
    """Extract text from PDF using PyMuPDF.

    For every page the native text is extracted first.  When EXCALISEARCH_OCR=1
    is set, images embedded in that page are also extracted and OCR'd; the
    resulting text is appended to the native text so that both are indexed.
    """
    import fitz  # PyMuPDF

    use_ocr = _ocr_enabled()
    doc = fitz.open(str(file_path))
    pages_text: list[str] = []

    for page in doc:
        parts: list[str] = [page.get_text()]

        if use_ocr:
            image_text = _ocr_embedded_images(doc, page)
            if image_text.strip():
                parts.append(image_text)

        pages_text.append("\n".join(parts))

    page_count = len(doc)
    doc.close()
    return "\n".join(pages_text), page_count


def _ocr_embedded_images(doc, page) -> str:
    """Extract images embedded in a PDF page and return their OCR text.
    """
    try:
        import pytesseract
        from PIL import Image

        # Windows: Explicitly set tesseract path if it's in the default install location
        # because pytesseract often fails to find it via PATH.
        if os.name == "nt":
            tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path

        texts: list[str] = []
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes))
            # Tesseract silently ignores any language it doesn't have installed.
            ocr_text = pytesseract.image_to_string(image, lang="spa+eng")
            if ocr_text.strip():
                texts.append(ocr_text)

        return "\n".join(texts)
    except Exception as exc:
        logger.warning("OCR of embedded images failed: %s", exc)
        return ""


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
