"""Unit tests for llmfy/llmfy_utils/chunk/chunk.py."""

import re

import pytest

from llmfy.llmfy_utils.chunk.chunk import chunk_markdown_by_header, chunk_text


class TestChunkTextBasic:
    def test_short_text_below_100_chars_is_silently_dropped(self):
        # Documented behavior: chunks with len(content) <= 100 are filtered
        # out entirely, even for otherwise-valid input.
        assert chunk_text("short text") == []

    def test_empty_string_returns_empty_list(self):
        assert chunk_text("") == []

    def test_long_enough_text_produces_one_chunk(self):
        text = "word " * 30  # > 100 chars once joined
        chunks = chunk_text(text, chunk_size=100, chunk_overlap=20)
        assert len(chunks) == 1
        assert chunks[0].id == "chunk_0"

    def test_multiple_chunks_with_overlap(self):
        words = [f"word{i}" for i in range(200)]
        text = " ".join(words)
        chunks = chunk_text(text, chunk_size=50, chunk_overlap=10)
        assert len(chunks) > 1
        assert [c.id for c in chunks] == [f"chunk_{i}" for i in range(len(chunks))]

    def test_none_input_raises_attribute_error(self):
        with pytest.raises(AttributeError):
            chunk_text(None)  # type: ignore[arg-type]

    def test_chunk_ids_reflect_kept_chunks_only_not_global_position(self):
        # A chunk filtered out by the <=100-char rule does not consume an id
        # — ids only increment for chunks actually appended. Three short
        # single-word windows get dropped before a long one is kept as
        # "chunk_0", not "chunk_3".
        text = "a a a " + ("b" * 200)
        chunks = chunk_text(text, chunk_size=1, chunk_overlap=0)
        assert len(chunks) == 1
        assert chunks[0].id == "chunk_0"


class TestChunkTextMetadata:
    def test_tuple_input_with_dict_metadata(self):
        text = "word " * 30
        chunks = chunk_text((text, {"source": "doc1.pdf"}), chunk_size=100, chunk_overlap=20)
        assert chunks[0].metadata == {"source": "doc1.pdf"}

    def test_tuple_input_with_non_dict_metadata_wrapped(self):
        text = "word " * 30
        chunks = chunk_text((text, 42), chunk_size=100, chunk_overlap=20)
        assert chunks[0].metadata == {"meta": 42}

    def test_plain_string_input_has_empty_metadata(self):
        text = "word " * 30
        chunks = chunk_text(text, chunk_size=100, chunk_overlap=20)
        assert chunks[0].metadata == {}


class TestChunkTextOverlapEdgeCases:
    def test_overlap_equal_to_size_raises_value_error(self):
        # step = chunk_size - chunk_overlap == 0 -> range() step-zero ValueError.
        with pytest.raises(ValueError):
            chunk_text("word " * 30, chunk_size=50, chunk_overlap=50)

    def test_overlap_greater_than_size_produces_empty_result_silently(self):
        # Negative step with a positive stop produces an empty range, not an
        # error — a notably different failure mode from the equal case above.
        result = chunk_text("word " * 30, chunk_size=10, chunk_overlap=20)
        assert result == []


class TestChunkMarkdownByHeader:
    def test_no_headers_returns_empty_list(self):
        assert chunk_markdown_by_header("just plain text, no headers") == []

    def test_single_header_chunk_includes_header_line(self):
        md = "# Title\nSome body text."
        chunks = chunk_markdown_by_header(md)
        assert len(chunks) == 1
        assert chunks[0].header == "Title"
        assert chunks[0].level == 1
        assert chunks[0].content.startswith("# Title")

    def test_multiple_headers_split_into_separate_chunks(self):
        md = "# H1\nbody1\n## H2\nbody2\n### H3\nbody3"
        chunks = chunk_markdown_by_header(md)
        assert [c.header for c in chunks] == ["H1", "H2", "H3"]
        assert [c.level for c in chunks] == [1, 2, 3]

    def test_header_level_filter_ignores_deeper_headers(self):
        md = "# H1\nbody\n## H2 nested\nmore body"
        chunks = chunk_markdown_by_header(md, header_level=1)
        assert len(chunks) == 1
        assert chunks[0].header == "H1"
        # The level-2 header line becomes ordinary content, not its own chunk.
        assert "## H2 nested" in chunks[0].content

    def test_header_without_space_after_hashes_is_not_matched(self):
        md = "#NoSpace\nbody"
        assert chunk_markdown_by_header(md) == []

    def test_content_before_first_header_is_dropped(self):
        md = "preamble text\n# Title\nbody"
        chunks = chunk_markdown_by_header(md)
        assert len(chunks) == 1
        assert "preamble" not in chunks[0].content

    def test_invalid_header_level_zero_raises_re_error(self):
        with pytest.raises(re.error):
            chunk_markdown_by_header("# Title\nbody", header_level=0)

    def test_negative_header_level_never_matches_but_does_not_raise(self):
        # Unlike header_level=0 (an invalid `{1,0}` quantifier range), a
        # negative bound like `{1,-1}` isn't valid regex-quantifier syntax
        # either, but Python's re engine falls back to treating `{1,-1}` as
        # literal text rather than raising — so this just never matches.
        assert chunk_markdown_by_header("# Title\nbody", header_level=-1) == []

    def test_none_input_raises_type_error(self):
        with pytest.raises(TypeError):
            chunk_markdown_by_header(None)  # type: ignore[arg-type]

    def test_tuple_metadata_attached_to_every_chunk(self):
        md = "# H1\nbody1\n## H2\nbody2"
        chunks = chunk_markdown_by_header((md, {"source": "doc1.md"}))
        assert all(c.metadata == {"source": "doc1.md"} for c in chunks)


class TestChunkResultSecurityAndRobustness:
    """Malformed/hostile input handling for a text-processing utility: no
    crashes or unbounded resource use on adversarial-shaped input."""

    def test_very_large_input_does_not_hang(self):
        text = "word " * 200_000  # ~1MB
        chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)
        assert len(chunks) > 0

    def test_whitespace_only_text_returns_empty(self):
        assert chunk_text("   \n\t   ") == []

    def test_unicode_text_handled_without_error(self):
        text = ("héllo wörld 你好世界 " * 30)
        chunks = chunk_text(text, chunk_size=100, chunk_overlap=10)
        assert isinstance(chunks, list)
