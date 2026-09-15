"""Unit tests for llmfy/llmfy_utils/chunk/result/*.py."""

import pytest
from pydantic import ValidationError

from llmfy.llmfy_utils.chunk.result.base_chunk_result import BaseChunkResult
from llmfy.llmfy_utils.chunk.result.md_chunk_result import MarkdownChunkResult


class TestBaseChunkResult:
    def test_id_defaults_to_unique_uuid(self):
        a = BaseChunkResult(content="x")
        b = BaseChunkResult(content="x")
        assert a.id != b.id

    def test_metadata_defaults_to_empty_dict_not_shared(self):
        a = BaseChunkResult(content="x")
        b = BaseChunkResult(content="x")
        a.metadata["k"] = "v"
        assert b.metadata == {}

    def test_content_is_required(self):
        with pytest.raises(ValidationError):
            BaseChunkResult()  # type: ignore[call-arg]

    def test_explicit_id_and_metadata_respected(self):
        result = BaseChunkResult(id="custom", content="x", metadata={"a": 1})
        assert result.id == "custom"
        assert result.metadata == {"a": 1}


class TestMarkdownChunkResult:
    def test_requires_header_and_level(self):
        with pytest.raises(ValidationError):
            MarkdownChunkResult(content="x")  # type: ignore[call-arg]

    def test_valid_construction(self):
        result = MarkdownChunkResult(content="# H\nbody", header="H", level=1)
        assert result.header == "H"
        assert result.level == 1

    def test_inherits_base_chunk_result_fields(self):
        result = MarkdownChunkResult(content="x", header="H", level=2)
        assert isinstance(result, BaseChunkResult)
        assert result.metadata == {}
