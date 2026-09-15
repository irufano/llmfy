"""Unit tests for llmfy/llmfy_core/tools/function_type_mapping.py."""

from llmfy.llmfy_core.tools.function_type_mapping import FUNCTION_TYPE_MAPPING


def test_expected_python_types_mapped():
    assert FUNCTION_TYPE_MAPPING[int] == "integer"
    assert FUNCTION_TYPE_MAPPING[float] == "number"
    assert FUNCTION_TYPE_MAPPING[str] == "string"
    assert FUNCTION_TYPE_MAPPING[bool] == "boolean"
    assert FUNCTION_TYPE_MAPPING[list] == "array"
    assert FUNCTION_TYPE_MAPPING[dict] == "object"
    assert FUNCTION_TYPE_MAPPING[type(None)] == "null"


def test_unmapped_type_raises_key_error_not_silently_defaulted():
    # Formatters call this via `.get(python_type, "string")`, so an unmapped
    # type falls back to "string" at the call site — but the mapping itself
    # has no entry, and callers must not assume one exists.
    assert set not in FUNCTION_TYPE_MAPPING
