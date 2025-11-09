from llmfy.llmfy_utils.chunk.result.base_chunk_result import BaseChunkResult


class MarkdownChunkResult(BaseChunkResult):
    """Base interface for chunk result."""

    header: str
    level: int
