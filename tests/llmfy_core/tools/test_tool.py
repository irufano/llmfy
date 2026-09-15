"""Unit tests for llmfy/llmfy_core/tools/tool.py."""

import pytest

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.model_backend import ModelBackend
from llmfy.llmfy_core.tools.tool import Tool


class TestToolDecorator:
    def test_marks_function_as_tool_with_default_strict(self):
        @Tool()
        def my_func(x: int) -> int:
            """Do something."""
            return x

        assert my_func._is_tool is True
        assert my_func._tool_strict is True

    def test_strict_false_is_stored(self):
        @Tool(strict=False)
        def my_func(x: int) -> int:
            """Do something."""
            return x

        assert my_func._tool_strict is False

    def test_decorated_function_still_callable_and_unwrapped(self):
        @Tool()
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        assert add(2, 3) == 5

    def test_docstring_reassigned_after_decoration_is_still_used(self):
        # Tool.__call__ does not inspect/cache the docstring at decoration
        # time — metadata extraction happens on demand in _get_tool_definition.
        @Tool()
        def my_func(x: int) -> int:
            """Original."""
            return x

        my_func.__doc__ = """Replaced docstring.

        Args:
            x (int): a number.
        """
        tool_def = Tool._get_tool_definition(my_func, ModelBackend.OPENAI_CHAT)
        assert tool_def["description"] == "Replaced docstring."


class TestGetToolDefinition:
    def test_delegates_to_registered_formatter(self):
        @Tool()
        def get_weather(location: str) -> str:
            """Get the weather.

            Args:
                location (str): The city.
            """
            return "sunny"

        tool_def = Tool._get_tool_definition(get_weather, ModelBackend.OPENAI_CHAT)
        assert tool_def["name"] == "get_weather"
        assert "location" in tool_def["parameters"]["properties"]

    def test_every_real_backend_is_registered(self):
        @Tool()
        def noop() -> None:
            """Do nothing."""
            return None

        for backend in ModelBackend:
            # Must not raise "Unsupported model backend" for any real member.
            Tool._get_tool_definition(noop, backend)

    def test_unsupported_backend_raises(self, monkeypatch):
        @Tool()
        def noop() -> None:
            """Do nothing."""
            return None

        monkeypatch.setattr(Tool, "_formatters", {})
        with pytest.raises(LLMfyException, match="Unsupported model backend"):
            Tool._get_tool_definition(noop, ModelBackend.OPENAI_CHAT)
