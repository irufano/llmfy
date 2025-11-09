import re
from typing import Any, List, Tuple, Union

from llmfy.llmfy_utils.chunk.result.base_chunk_result import BaseChunkResult
from llmfy.llmfy_utils.chunk.result.md_chunk_result import MarkdownChunkResult


def chunk_text(
    text: Union[str, Tuple[str, Any]],
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> List[BaseChunkResult]:
    """
    Split text into overlapping chunks.

    example:
    ```python
    text = "This is a long text " * 200
    chunks = chunk_text(text=text, chunk_size=100, chunk_overlap=20)
    for chunk in chunks:
        print(f"{chunk.id}: {chunk.content}")
        print(f"{chunk.metadata}")

    # OR

    text = "This is a long text " * 200
    data = (text, {"source": "doc1.pdf", "page": 2})
    chunks = chunk_text(text=data, chunk_size=100, chunk_overlap=20)
    for chunk in chunks:
        print(f"{chunk.id}: {chunk.content}")
        print(f"{chunk.metadata}")
    ```

    Args:
        text (str | tuple): Text to chunk or (text, metadata)
        chunk_size (int, optional): Defaults to 800.
        chunk_overlap (int, optional): Defaults to 100.

    Returns:
        chunks (List[BaseChunkResult]): Each chunk property:
            - 'id': chunk id
            - 'content': chunk content
            - 'metadata': optional metadata if provided
    """

    chunks: List[BaseChunkResult] = []

    # Extract text and metadata
    if isinstance(text, tuple):
        raw_text, metadata = text
        metadata = metadata if isinstance(metadata, dict) else {"meta": metadata}
    else:
        raw_text, metadata = text, {}

    words = raw_text.split()
    index = 0

    for i in range(0, len(words), chunk_size - chunk_overlap):
        chunk_words = words[i : i + chunk_size]
        chunk_content = " ".join(chunk_words).strip()

        if len(chunk_content) > 100:  # Only substantial chunks
            chunk = BaseChunkResult(
                id=f"chunk_{index}",
                content=chunk_content,
                metadata=metadata,
            )
            chunks.append(chunk)
            index += 1

    return chunks


def chunk_markdown_by_header(
    markdown_text: Union[str, Tuple[str, Any]],
    header_level: int | None = None,
) -> List[MarkdownChunkResult]:
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
        chunks (List[MarkdownChunkResult]): Each chunk property:
            - 'id': chunk id
            - 'header': the header text (without #)
            - 'level': header level (1-6)
            - 'content': header + content text
            - 'metadata': optional metadata if provided
    """
    # Unpack metadata if provided

    # Unpack metadata if provided
    if isinstance(markdown_text, tuple):
        text, metadata = markdown_text
        base_metadata = metadata if isinstance(metadata, dict) else {"meta": metadata}
    else:
        text = markdown_text
        base_metadata = {}

    # Regex for headers
    pattern = (
        r"^(#{1,6}) (.+)$"
        if header_level is None
        else rf"^(#{{1,{header_level}}}) (.+)$"
    )
    matches = list(re.finditer(pattern, text, flags=re.MULTILINE))
    chunks: List[MarkdownChunkResult] = []

    for i, match in enumerate(matches):
        hashes = match.group(1)
        header_text = match.group(2).strip()
        level = len(hashes)

        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()

        chunk = MarkdownChunkResult(
            id=f"chunk_{i}",
            header=header_text,
            level=level,
            content=content,
            metadata=base_metadata,
        )
        chunks.append(chunk)

    return chunks
