"""
Summary service — generates text previews.
"""


def generate_preview(text: str, max_len: int = 300) -> str:
    """
    Generate a short preview from the extracted text.
    Returns the first max_len characters, trimmed to the last complete word.
    """
    if len(text) <= max_len:
        return text

    truncated = text[:max_len]
    # Try to break at the last space
    last_space = truncated.rfind(" ")
    if last_space > max_len * 0.5:
        truncated = truncated[:last_space]

    return truncated.rstrip() + "…"
