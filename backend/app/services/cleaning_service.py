import re
import unicodedata


def clean_text(raw: str) -> str:
    """
    Clean and normalize extracted text:
    """
    # Normalize unicode to NFC form
    text = unicodedata.normalize("NFC", raw)

    # Remove control characters except newline, tab, carriage return
    text = re.sub(r"[^\S \n\t]+", " ", text)

    # Replace \r\n with \n
    text = text.replace("\r\n", "\n")

    # Collapse multiple blank lines into a single one
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse multiple spaces (but not newlines) into one
    text = re.sub(r"[^\S\n]+", " ", text)

    # Strip each line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Final strip
    text = text.strip()

    return text
