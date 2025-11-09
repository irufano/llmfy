import re
import unicodedata


def clean_text_for_embedding(text: str) -> str:
    """
    Light cleaning for embeddings/vector search

    Args:
        text (str): text to clean.

    Returns:
        str: cleaned text
    """
    # Normalize Unicode (e.g., full-width chars → normal width)
    text = unicodedata.normalize("NFKC", text)

    # Collapse multiple spaces/newlines into one space
    text = re.sub(r"\s+", " ", text)

    # Trim leading/trailing whitespace
    return text.strip()