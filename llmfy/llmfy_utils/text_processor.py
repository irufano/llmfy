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
    ```python
    text = "This is a long text " * 200
    chunks = chunk_text(text=text, chunk_size=100, chunk_overlap=20)
    for text, chunk_id, meta in chunks:
        print(f"{chunk_id}: {text}")
        print(f"{meta}")

    # OR

    text = "This is a long text " * 200
    data = (text, {"source": "doc1.pdf", "page": 2})
    chunks = chunk_text(text=data, chunk_size=100, chunk_overlap=20)
    for text, chunk_id, meta in chunks:
        print(f"{chunk_id}: {text}")
        print(f"{meta}")
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


def chunk_markdown_by_header(
    markdown_text: Union[str, Tuple[str, Any]],
    header_level: int | None = None,
) -> List[Dict[str, Any]]:
    """
    Split Markdown into chunks based on header levels.
    The content of each chunk includes the header itself.
    Optionally attaches metadata if provided.

    Args:
        markdown_text: str or (str, metadata_dict)
            Example: ("# Title", {"source": "doc1.md", "page": 2})
        header_level: int | None
            - None: include all headers (#-######)
            - int: include headers up to that level

    Returns:
        chunks (List[dict]): Each chunk with keys:
            - 'header': the header text (without #)
            - 'level': header level (1-6)
            - 'content': header + content text
            - 'metadata': optional metadata if provided
    """
    # Unpack metadata if provided
    if isinstance(markdown_text, tuple):
        text, metadata = markdown_text
        if not isinstance(metadata, dict):
            metadata = {"meta": metadata}
    else:
        text = markdown_text
        metadata = None

    # Choose regex based on header level
    if header_level is None:
        pattern = r"^(#{1,6}) (.+)$"  # all headers
    else:
        pattern = rf"^(#{{1,{header_level}}}) (.+)$"  # up to header_level

    matches = list(re.finditer(pattern, text, flags=re.MULTILINE))
    chunks: List[Dict[str, Any]] = []

    for i, match in enumerate(matches):
        hashes = match.group(1)
        header_text = match.group(2).strip()
        level = len(hashes)

        start = match.start()  # include header in content
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()

        chunk = {
            "header": header_text,
            "level": level,
            "content": content,
        }

        if metadata:
            chunk["metadata"] = metadata

        chunks.append(chunk)

    return chunks
