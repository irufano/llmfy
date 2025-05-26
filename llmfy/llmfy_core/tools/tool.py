from typing import Any, Callable, Dict

from llmfy.llmfy_core.models.model_formatter import ModelFormatter
from llmfy.llmfy_core.models.bedrock.bedrock_formatter import BedrockFormatter
from llmfy.llmfy_core.models.model_provider import ModelProvider
from llmfy.llmfy_core.models.openai.openai_formatter import OpenAIFormatter
from llmfy.llmfy_core.tools.function_parser import FunctionParser
from llmfy.llmfy_core.tools.function_type_mapping import FUNCTION_TYPE_MAPPING
from llmfy.exception.llmfy_exception import LLMfyException


class Tool:
    """
    Decorator class for creating tool definitions.
    """

    # Register formatter
    _formatters: Dict[ModelProvider, ModelFormatter] = {
        ModelProvider.OPENAI: OpenAIFormatter(),
        ModelProvider.BEDROCK: BedrockFormatter(),
    }

    def __init__(self, strict: bool = True):
        self.strict = strict

    def __call__(self, func: Callable) -> Callable:
        func._is_tool = True  # type: ignore # Mark the function as a tool
        func._tool_strict = self.strict  # type: ignore # Store strict setting. to check: getattr(func, '_tool_strict', True)
        return func

    @staticmethod
    def _get_tool_definition(func: Callable, provider: ModelProvider) -> Dict[str, Any]:
        formatter = Tool._formatters.get(provider)
        if not formatter:
            raise LLMfyException(f"Unsupported model provider: {provider}")

        metadata = FunctionParser.get_function_metadata(func)
        return formatter.format_tool_function(metadata, FUNCTION_TYPE_MAPPING)
