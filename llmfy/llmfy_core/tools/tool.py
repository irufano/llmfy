from typing import Any, Callable, Dict

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.models.bedrock.bedrock_formatter import BedrockFormatter
from llmfy.llmfy_core.models.model_formatter import ModelFormatter
from llmfy.llmfy_core.models.openai.openai_formatter import OpenAIFormatter
from llmfy.llmfy_core.service_provider import ServiceProvider
from llmfy.llmfy_core.tools.function_parser import FunctionParser
from llmfy.llmfy_core.tools.function_type_mapping import FUNCTION_TYPE_MAPPING


class Tool:
    """
    Decorator class for creating tool definitions.
    """

    # Register formatter
    _formatters: Dict[ServiceProvider, ModelFormatter] = {
        ServiceProvider.OPENAI: OpenAIFormatter(),
        ServiceProvider.BEDROCK: BedrockFormatter(),
    }

    def __init__(self, strict: bool = True):
        self.strict = strict

    def __call__(self, func: Callable) -> Callable:
        func._is_tool = True  # type: ignore # Mark the function as a tool
        func._tool_strict = self.strict  # type: ignore # Store strict setting. to check: getattr(func, '_tool_strict', True)
        return func

    @staticmethod
    def _get_tool_definition(func: Callable, provider: ServiceProvider) -> Dict[str, Any]:
        formatter = Tool._formatters.get(provider)
        if not formatter:
            raise LLMfyException(f"Unsupported model provider: {provider}")

        metadata = FunctionParser.get_function_metadata(func)
        return formatter.format_tool_function(metadata, FUNCTION_TYPE_MAPPING)
