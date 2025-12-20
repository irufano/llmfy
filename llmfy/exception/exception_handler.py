from llmfy.exception.exception_mapper import (
    BEDROCK_ERROR_MAP,
    # GOOGLE_ERROR_MAP,
    OPENAI_ERROR_MAP,
)
from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.service_provider import ServiceProvider


def handle_bedrock_error(e) -> LLMfyException:
    """
    Handle AWS Bedrock ClientError exceptions.

    Docs: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html
    """
    from botocore.exceptions import ClientError

    if not isinstance(e, ClientError):
        return LLMfyException(
            message=str(e),
            raw_error=e,
            provider="bedrock",
        )

    error_code = e.response["Error"]["Code"]
    message = e.response["Error"].get("Message", str(e))
    http_status = e.response.get("ResponseMetadata", {}).get("HTTPStatusCode")

    if error_code in BEDROCK_ERROR_MAP:
        exception_class, default_status = BEDROCK_ERROR_MAP[error_code]
        status_code = http_status or default_status
    else:
        exception_class = LLMfyException
        status_code = http_status

    return exception_class(
        message=message,
        status_code=status_code,
        raw_error=e.response,
        provider=ServiceProvider.BEDROCK,
    )


def handle_openai_error(e) -> LLMfyException:
    """
    Handle OpenAI API exceptions.

    Docs: https://github.com/openai/openai-python#handling-errors
    """
    # import openai

    error_type = type(e).__name__

    # Extract status code from APIStatusError subclasses
    status_code = getattr(e, "status_code", None)

    # Build raw error dict
    raw_error = {
        "type": error_type,
        "message": str(e),
    }

    # Add response if available
    if hasattr(e, "response"):
        raw_error["response"] = e.response

    # Add request_id if available
    if hasattr(e, "request_id"):
        raw_error["request_id"] = e.request_id

    # Add body if available
    if hasattr(e, "body"):
        raw_error["body"] = e.body

    if error_type in OPENAI_ERROR_MAP:
        exception_class, default_status = OPENAI_ERROR_MAP[error_type]
        status_code = status_code or default_status
    else:
        exception_class = LLMfyException

    return exception_class(
        message=str(e),
        status_code=status_code,
        raw_error=raw_error,
        provider=ServiceProvider.OPENAI,
    )


# def handle_google_error(e) -> LLMfyException:
#     """
#     Handle Google Gen AI API exceptions.

#     Docs: https://github.com/googleapis/python-genai#error-handling
#     """
#     # from google.genai import errors

#     if isinstance(e, errors.APIError):
#         status_code = e.code
#         message = e.message

#         raw_error = {
#             'code': e.code,
#             'message': e.message,
#         }

#         # Add any additional attributes
#         if hasattr(e, 'details'):
#             raw_error['details'] = e.details

#         exception_class = GOOGLE_ERROR_MAP.get(status_code, LLMfyException)

#         return exception_class(
#             message=message,
#             status_code=status_code,
#             raw_error=raw_error,
#             provider='google',
#         )

#     return LLMfyException(
#         message=str(e),
#         raw_error={'error': str(e)},
#         provider='google',
#     )
