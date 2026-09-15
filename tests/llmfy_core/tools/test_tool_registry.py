"""Unit tests for llmfy/llmfy_core/tools/tool_registry.py."""

import pytest

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.model_backend import ModelBackend
from llmfy.llmfy_core.tools.tool import Tool
from llmfy.llmfy_core.tools.tool_registry import ToolRegistry


class FakeModel:
    """Minimal duck-typed stand-in for BaseAIModel — ToolRegistry only ever
    reads `.backend` from it."""

    def __init__(self, backend=ModelBackend.OPENAI_CHAT):
        self.backend = backend


@Tool()
def get_weather(location: str) -> str:
    """Get the weather for a location.

    Args:
        location (str): The city name.
    """
    return f"sunny in {location}"


def not_a_tool(x: int) -> int:
    return x


class TestConstruction:
    def test_registers_decorated_function(self):
        registry = ToolRegistry([get_weather], FakeModel())  # type: ignore
        assert "get_weather" in registry._tools
        assert "get_weather" in registry._tool_definitions

    def test_undecorated_function_raises(self):
        with pytest.raises(LLMfyException, match="must be decorated with @Tool"):
            ToolRegistry([not_a_tool], FakeModel())  # type: ignore

    def test_lambda_without_tool_decorator_raises(self):
        with pytest.raises(LLMfyException, match="must be decorated with @Tool"):
            ToolRegistry([lambda x: x], FakeModel())  # type: ignore

    def test_duplicate_names_last_one_wins_silently(self):
        @Tool()
        def dup(x: int) -> int:  # type: ignore
            """First version.

            Args:
                x (int): a number.
            """
            return x

        first_dup = dup

        @Tool()
        def dup(x: int) -> int:  # noqa: F811 - intentional redefinition for the test
            """Second version.

            Args:
                x (int): a number.
            """
            return x * 100

        registry = ToolRegistry([first_dup, dup], FakeModel())  # type: ignore
        assert len(registry._tools) == 1
        assert registry._tools["dup"](5) == 500  # the later function wins


class TestGetToolDefinitions:
    def test_returns_list_in_registration_order(self):
        @Tool()
        def tool_a() -> None:
            """A."""

        @Tool()
        def tool_b() -> None:
            """B."""

        registry = ToolRegistry([tool_a, tool_b], FakeModel())  # type: ignore
        names = [d["name"] for d in registry.get_tool_definitions()]
        assert names == ["tool_a", "tool_b"]


class TestExecuteTool:
    def test_executes_registered_tool_with_kwargs(self):
        registry = ToolRegistry([get_weather], FakeModel())  # type: ignore
        result = registry.execute_tool("get_weather", {"location": "Paris"})
        assert result == "sunny in Paris"

    def test_unregistered_tool_name_raises_llmfy_exception(self):
        registry = ToolRegistry([get_weather], FakeModel())  # type: ignore
        with pytest.raises(LLMfyException, match="Tool not found: does_not_exist"):
            registry.execute_tool("does_not_exist", {})

    def test_arbitrary_attacker_supplied_names_do_not_execute_anything(self):
        # Security: name lookup is a plain dict membership check, never
        # eval/getattr-on-arbitrary-object — an attacker-controlled name like
        # a builtin or dunder must be rejected the same as any other unknown name.
        registry = ToolRegistry([get_weather], FakeModel())  # type: ignore
        for hostile_name in ["__import__", "os.system", "eval", "../../etc/passwd"]:
            with pytest.raises(LLMfyException, match="Tool not found"):
                registry.execute_tool(hostile_name, {})

    def test_missing_required_argument_raises_type_error_unwrapped(self):
        # ToolRegistry does not catch/wrap errors raised by the underlying
        # tool function itself — a wrong-arity call surfaces as a plain
        # TypeError, not an LLMfyException.
        registry = ToolRegistry([get_weather], FakeModel())  # type: ignore
        with pytest.raises(TypeError):
            registry.execute_tool("get_weather", {})
