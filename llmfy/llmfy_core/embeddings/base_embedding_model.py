from abc import ABC, abstractmethod
from typing import Any

from llmfy.llmfy_core.service_provider import ServiceProvider


class BaseEmbeddingModel(ABC):
    """BaseEmbeddingModel Abstract"""

    def __init__(self):
        """Model provider."""
        self.provider: ServiceProvider
        self.model: str

    @abstractmethod
    def encode(
        self,
        text: str,
    ) -> list[float]:
        pass

    @abstractmethod
    def encode_batch(
        self,
        texts: list[str] | str,
        batch_size: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        show_progress_bar: bool = False,
    ) -> Any:
        pass
