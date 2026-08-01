from abc import ABC, abstractmethod
from typing import Any

from llmfy.llmfy_core.responses.ai_response import AIResponse
from llmfy.llmfy_core.service_provider import ServiceProvider


class BaseAIModel(ABC):
    """BaseAIModel Abstract"""

    def __init__(self):
        """Model provider."""
        self.provider: ServiceProvider

    @abstractmethod
    def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> AIResponse:
        pass

    @abstractmethod
    def generate_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> Any:
        pass
