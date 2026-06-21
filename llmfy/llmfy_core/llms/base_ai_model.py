from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

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
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> AIResponse:
        pass

    @abstractmethod
    def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Any:
        pass
