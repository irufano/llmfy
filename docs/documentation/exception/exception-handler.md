# Exception Handler

LLMfy maps provider-specific errors into a unified exception hierarchy so you can handle errors consistently regardless of which provider you use.

## Base Exception

All LLMfy exceptions inherit from `LLMfyException`:

```python
from llmfy import LLMfyException
```

`LLMfyException` exposes four attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | `str` | Human-readable error message |
| `status_code` | `int \| None` | HTTP status code from the provider |
| `provider` | `str \| None` | Provider name (e.g. `"openai"`, `"bedrock"`, `"google"`) |
| `raw_error` | `Any \| None` | The original exception from the provider SDK |

## Exception Types

| Exception | Description |
|-----------|-------------|
| `LLMfyException` | Base class for all LLMfy errors |
| `RateLimitException` | Rate limit exceeded (HTTP 429) |
| `QuotaExceededException` | Usage/quota limit exceeded |
| `TimeoutException` | Request timed out (HTTP 408) |
| `InvalidRequestException` | Invalid request parameters (HTTP 400/422) |
| `AuthenticationException` | Authentication failed (HTTP 401/403) |
| `PermissionDeniedException` | Permission denied (HTTP 403) |
| `ModelNotFoundException` | Model not found or unavailable (HTTP 404) |
| `ServiceUnavailableException` | Service temporarily unavailable (HTTP 500/503) |
| `ContentFilterException` | Content blocked by safety filters |
| `ModelErrorException` | Model processing error (HTTP 424) |

## Basic Usage

Catch `LLMfyException` to handle any LLMfy error:

```python linenums="1"
from llmfy import LLMfy, LLMfyException

try:
    response = agent.invoke("Hello")
    print(response.result.content)
except LLMfyException as e:
    print(f"Error: {e.message}")
    print(f"Status Code: {e.status_code}")
    print(f"Provider: {e.provider}")
```

## Handling Specific Exceptions

Import specific exception types to handle them differently:

```python linenums="1"
from llmfy import (
    LLMfyException,
    RateLimitException,
    TimeoutException,
    AuthenticationException,
    ServiceUnavailableException,
)

try:
    response = agent.invoke("Hello")
    print(response.result.content)
except RateLimitException as e:
    print(f"Rate limited (HTTP {e.status_code}) — implement backoff and retry.")
except TimeoutException as e:
    print(f"Request timed out — retry with a shorter prompt or increase timeout.")
except AuthenticationException as e:
    print(f"Authentication failed — check your API key or credentials.")
except ServiceUnavailableException as e:
    print(f"Service unavailable (HTTP {e.status_code}) — retry later.")
except LLMfyException as e:
    print(f"Unexpected error: {e.message}")
```

## Provider Error Mapping

LLMfy automatically maps provider-specific errors to the corresponding exception type.

### OpenAI

| Provider Error | LLMfy Exception | Status Code |
|----------------|----------------|-------------|
| `RateLimitError` | `RateLimitException` | 429 |
| `APITimeoutError` | `TimeoutException` | 408 |
| `APIConnectionError` | `ServiceUnavailableException` | — |
| `AuthenticationError` | `AuthenticationException` | 401 |
| `PermissionDeniedError` | `PermissionDeniedException` | 403 |
| `BadRequestError` | `InvalidRequestException` | 400 |
| `NotFoundError` | `ModelNotFoundException` | 404 |
| `UnprocessableEntityError` | `InvalidRequestException` | 422 |
| `InternalServerError` | `ServiceUnavailableException` | 500 |

### AWS Bedrock

| Provider Error | LLMfy Exception | Status Code |
|----------------|----------------|-------------|
| `ThrottlingException` | `RateLimitException` | 429 |
| `ModelTimeoutException` | `TimeoutException` | 408 |
| `ModelNotReadyException` | `ServiceUnavailableException` | 429 |
| `ValidationException` | `InvalidRequestException` | 400 |
| `AccessDeniedException` | `AuthenticationException` | 403 |
| `ResourceNotFoundException` | `ModelNotFoundException` | 404 |
| `ServiceUnavailableException` | `ServiceUnavailableException` | 503 |
| `InternalServerException` | `ServiceUnavailableException` | 500 |
| `ModelErrorException` | `ModelErrorException` | 424 |

### Google AI

| HTTP Status | LLMfy Exception |
|-------------|----------------|
| 400 | `InvalidRequestException` |
| 401 | `AuthenticationException` |
| 403 | `PermissionDeniedException` |
| 404 | `ModelNotFoundException` |
| 408 | `TimeoutException` |
| 429 | `RateLimitException` |
| 500 | `ServiceUnavailableException` |
| 503 | `ServiceUnavailableException` |
