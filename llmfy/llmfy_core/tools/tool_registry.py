from typing import Any, Callable, Dict, List

from llmfy.llmfy_core.models.base_ai_model import BaseAIModel
from llmfy.llmfy_core.tools.tool import Tool
from llmfy.exception.llmfy_exception import LLMfyException


class ToolRegistry:
    """
    TollRegistry class.

    Use this ToolRegistry to using tools in `LLMfyPipe`.

    Example:
    ```python
    # register tools
    registry = ToolRegistry(['some_tool','other_tool'])

    # execute
    registry.execute_tool(name='some_tool', arguments:{"arg1": "value"})

    ```

    """

    def __init__(
        self,
        funcs: List[Callable],
        model: BaseAIModel,
    ):
        self._tools: Dict[str, Callable] = {}
        self._tool_definitions: Dict[str, Dict[str, Any]] = {}

        for func in funcs:
            if not hasattr(func, "_is_tool"):
                raise LLMfyException("Function must be decorated with @Tool")

            tool_def = Tool._get_tool_definition(func, model.provider)
            self._tools[func.__name__] = func
            self._tool_definitions[func.__name__] = tool_def
            # print(f"`{func.__name__}` registered ✅")

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all tool definitions registered with this framework."""
        return list(self._tool_definitions.values())

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a registered tool."""
        if name not in self._tools:
            raise LLMfyException(f"Tool not found: {name}")
        return self._tools[name](**arguments)
