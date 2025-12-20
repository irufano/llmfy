
# ============================================================================
# AWS Bedrock Error Mapping
# Docs: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html#API_runtime_Converse_Errors
# ============================================================================

from llmfy.exception.llmfy_exception import AuthenticationException, InvalidRequestException, ModelErrorException, ModelNotFoundException, PermissionDeniedException, RateLimitException, ServiceUnavailableException, TimeoutException


BEDROCK_ERROR_MAP = {
    # ThrottlingException - HTTP 429
    'ThrottlingException': (RateLimitException, 429),
    
    # ModelTimeoutException - HTTP 408
    'ModelTimeoutException': (TimeoutException, 408),
    
    # ModelNotReadyException - HTTP 429
    'ModelNotReadyException': (ServiceUnavailableException, 429),
    
    # ValidationException - HTTP 400
    'ValidationException': (InvalidRequestException, 400),
    
    # AccessDeniedException - HTTP 403
    'AccessDeniedException': (AuthenticationException, 403),
    
    # ResourceNotFoundException - HTTP 404
    'ResourceNotFoundException': (ModelNotFoundException, 404),
    
    # ServiceUnavailableException - HTTP 503
    'ServiceUnavailableException': (ServiceUnavailableException, 503),
    
    # InternalServerException - HTTP 500
    'InternalServerException': (ServiceUnavailableException, 500),
    
    # ModelErrorException - HTTP 424
    'ModelErrorException': (ModelErrorException, 424),
}


# ============================================================================
# OpenAI Error Mapping
# Docs: https://github.com/openai/openai-python#handling-errors
# ============================================================================

OPENAI_ERROR_MAP = {
    'RateLimitError': (RateLimitException, 429),
    'APITimeoutError': (TimeoutException, 408),
    'APIConnectionError': (ServiceUnavailableException, None),
    'AuthenticationError': (AuthenticationException, 401),
    'PermissionDeniedError': (PermissionDeniedException, 403),
    'BadRequestError': (InvalidRequestException, 400),
    'NotFoundError': (ModelNotFoundException, 404),
    'UnprocessableEntityError': (InvalidRequestException, 422),
    'InternalServerError': (ServiceUnavailableException, 500),
}


# ============================================================================
# Google Gen AI Error Mapping
# Docs: https://github.com/googleapis/python-genai#error-handling
# ============================================================================

GOOGLE_ERROR_MAP = {
    429: RateLimitException,
    408: TimeoutException,
    400: InvalidRequestException,
    401: AuthenticationException,
    403: PermissionDeniedException,
    404: ModelNotFoundException,
    500: ServiceUnavailableException,
    503: ServiceUnavailableException,
}


