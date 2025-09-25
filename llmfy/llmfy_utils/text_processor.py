import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple, Union


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


def chunk_text(
    text: Union[str, Tuple[str, Any]],
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> List[Tuple[str, str, Optional[Dict[str, Any]]]]:
    """
    Split text into overlapping chunks.

    example:
    ```
    text = "This is a long text " * 200
    chunks = chunk_text(text=text, chunk_size=100, chunk_overlap=20)
    for text, chunk_id, meta in chunks:
        print(f"{chunk_id}: {text} \n{meta}\n")

    # OR

    text = "This is a long text " * 200
    data = (text, {"source": "doc1.pdf", "page": 2})
    chunks = chunk_text(text=data, chunk_size=100, chunk_overlap=20)
    for text, chunk_id, meta in chunks:
        print(f"{chunk_id}: {text} \n{meta}\n")
    ```

    Args:
        text (str | tuple): Text to chunk or (text, metadata)
        chunk_size (int, optional): Defaults to 800.
        chunk_overlap (int, optional): Defaults to 100.

    Returns:
        List[Tuple[str, str, dict | None]]: (chunk_text, chunk_id, metadata)
    """

    chunks: List[Tuple[str, str, Optional[Dict[str, Any]]]] = []

    # Extract text and metadata
    if isinstance(text, tuple):
        raw_text, metadata = text
        if not isinstance(metadata, dict):
            metadata = {"meta": metadata}
    else:
        raw_text, metadata = text, None

    words = raw_text.split()
    index = 0

    for i in range(0, len(words), chunk_size - chunk_overlap):
        chunk_words = words[i : i + chunk_size]
        chunk_text = " ".join(chunk_words)

        if len(chunk_text.strip()) > 100:  # Only substantial chunks
            chunk_id = f"chunk_{index}"
            chunks.append((chunk_text, chunk_id, metadata))
            index += 1

    return chunks
