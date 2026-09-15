"""Unit tests for llmfy/llmfy_utils/text_preprocessing/text_preprocessing.py."""

import pytest

from llmfy.llmfy_utils.text_preprocessing.text_preprocessing import (
    clean_text_for_embedding,
)


def test_collapses_multiple_spaces():
    assert clean_text_for_embedding("hello    world") == "hello world"


def test_collapses_newlines_and_tabs_into_single_space():
    # Documented behavior: line breaks/paragraph structure are destroyed —
    # multi-paragraph text becomes one line.
    assert clean_text_for_embedding("line one\n\nline two\tindented") == "line one line two indented"


def test_strips_leading_and_trailing_whitespace():
    assert clean_text_for_embedding("   padded text   ") == "padded text"


def test_empty_string_returns_empty_string():
    assert clean_text_for_embedding("") == ""


def test_nfkc_normalizes_fullwidth_characters():
    # Full-width "Ａ" (U+FF21) normalizes to ASCII "A" under NFKC.
    assert clean_text_for_embedding("ＡＢＣ") == "ABC"


def test_nfkc_normalizes_non_breaking_space_to_regular_space_and_collapses():
    text = "hello world"
    assert clean_text_for_embedding(text) == "hello world"


def test_none_input_raises_type_error():
    with pytest.raises(TypeError):
        clean_text_for_embedding(None)  # type: ignore[arg-type]


def test_non_str_input_raises_type_error():
    with pytest.raises(TypeError):
        clean_text_for_embedding(12345)  # type: ignore[arg-type]


def test_large_input_does_not_hang():
    text = "word " * 200_000
    result = clean_text_for_embedding(text)
    assert result.startswith("word word")
