from collections.abc import Callable
from typing import Any

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.llms.bedrock.bedrock_formatter import BedrockFormatter
from llmfy.llmfy_core.llms.google.googleai_formatter import GoogleAIFormatter
from llmfy.llmfy_core.llms.model_formatter import ModelFormatter
from llmfy.llmfy_core.llms.openai.chat.openai_chat_formatter import OpenAIChatFormatter
from llmfy.llmfy_core.llms.openai.responses.openai_responses_formatter import (
    OpenAIResponsesFormatter,
)
from llmfy.llmfy_core.model_backend import ModelBackend
from llmfy.llmfy_core.tools.function_parser import FunctionParser
from llmfy.llmfy_core.tools.function_type_mapping import FUNCTION_TYPE_MAPPING


class Tool:
    """
    Decorator class for creating tool definitions.
    """

    # Register formatter
    _formatters: dict[ModelBackend, ModelFormatter] = {
        ModelBackend.OPENAI: OpenAIChatFormatter(),
        ModelBackend.OPENAI_RESPONSES: OpenAIResponsesFormatter(),
        ModelBackend.BEDROCK: BedrockFormatter(),
        ModelBackend.GOOGLE: GoogleAIFormatter(),
    }

    def __init__(self, strict: bool = True):
        self.strict = strict

    def __call__(self, func: Callable) -> Callable:
        func._is_tool = True  # type: ignore # Mark the function as a tool
        func._tool_strict = self.strict  # type: ignore # Store strict setting. to check: getattr(func, '_tool_strict', True)
        return func

    @staticmethod
    def _get_tool_definition(func: Callable, backend: ModelBackend) -> dict[str, Any]:
        formatter = Tool._formatters.get(backend)
        if not formatter:
            raise LLMfyException(f"Unsupported model backend: {backend}")

        metadata = FunctionParser.get_function_metadata(func)
        return formatter.format_tool_function(metadata, FUNCTION_TYPE_MAPPING)
