"""
LLMfy Exception Handling

Documentation References:

- AWS Bedrock Converse API: [https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html)
- OpenAI Python SDK: [https://github.com/openai/openai-python#handling-errors](https://github.com/openai/openai-python#handling-errors)
- Google Gen AI SDK: [https://github.com/googleapis/python-genai#error-handling](https://github.com/googleapis/python-genai#error-handling)

Example of catching and inspecting an error:
```python
try:
    # _call_llmfy
    pass
except LLMfyException as e:
    print(f"Error: {e.message}")
    print(f"Status Code: {e.status_code}")
    print(f"Provider: {e.provider}")
    print(f"Raw Error: {e.raw_error}")

    # Check specific exception type
    if isinstance(e, RateLimitException):
        print("Rate limited! Implement backoff...")
    elif isinstance(e, TimeoutException):
        print("Request timed out! Retry...")
```
"""

from enum import Enum
from typing import Any, Optional


class TimeoutType(Enum):
    CONNECT = "connect"  # could not establish a connection to the endpoint
    READ = "read"        # connected but timed out waiting for response bytes
    WRITE = "write"      # timed out sending the request
    POOL = "pool"        # timed out waiting for a connection slot from the pool
    MODEL = "model"      # model-side processing timeout (Bedrock ModelTimeoutException)


class LLMfyException(Exception):
    """
    Base LLMfy Exception

    Example of catching and inspecting an error:
    ```python
    try:
        # _call_llmfy
        pass
    except LLMfyException as e:
        print(f"Error: {e.message}")
        print(f"Status Code: {e.status_code}")
        print(f"Provider: {e.provider}")
        print(f"Raw Error: {e.raw_error}")

        # Check specific exception type
        if isinstance(e, RateLimitException):
            print("Rate limited! Implement backoff...")
        elif isinstance(e, TimeoutException):
            print("Request timed out! Retry...")
    ```
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        raw_error: Optional[Any] = None,
        provider: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.raw_error = raw_error
        self.provider = provider

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code}, "
            f"provider={self.provider!r})"
        )


class RateLimitException(LLMfyException):
    """Rate limit exceeded"""

    pass


class QuotaExceededException(LLMfyException):
    """Quota/usage limit exceeded"""

    pass


class TimeoutException(LLMfyException):
    """Request timed out"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        raw_error: Optional[Any] = None,
        provider: Optional[str] = None,
        timeout_type: Optional[TimeoutType] = None,
    ):
        super().__init__(message, status_code, raw_error, provider)
        self.timeout_type = timeout_type


class InvalidRequestException(LLMfyException):
    """Invalid request parameters"""

    pass


class AuthenticationException(LLMfyException):
    """Authentication failed"""

    pass


class PermissionDeniedException(LLMfyException):
    """Permission denied"""

    pass


class ModelNotFoundException(LLMfyException):
    """Model not found or unavailable"""

    pass


class ServiceUnavailableException(LLMfyException):
    """Service temporarily unavailable"""

    pass


class ContentFilterException(LLMfyException):
    """Content blocked by safety filters"""

    pass


class ModelErrorException(LLMfyException):
    """Model processing error"""

    pass
