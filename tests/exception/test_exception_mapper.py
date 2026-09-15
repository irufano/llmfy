"""Unit tests for the provider error-code -> exception-class maps
(llmfy/exception/exception_mapper.py). These are pure data; the tests pin
their exact shape since `exception_handler.py` depends on it precisely, and a
one-character typo in a key (e.g. a provider SDK exception class name) would
silently produce plain `LLMfyException` fallbacks instead of the intended
mapping.
"""

from llmfy.exception.exception_mapper import (
    ANTHROPIC_ERROR_MAP,
    BEDROCK_ERROR_MAP,
    GOOGLE_ERROR_MAP,
    OPENAI_ERROR_MAP,
)
from llmfy.exception.llmfy_exception import (
    AuthenticationException,
    InvalidRequestException,
    ModelErrorException,
    ModelNotFoundException,
    PermissionDeniedException,
    RateLimitException,
    ServiceUnavailableException,
    TimeoutException,
)


class TestBedrockErrorMap:
    def test_expected_keys_present(self):
        assert set(BEDROCK_ERROR_MAP.keys()) == {
            "ThrottlingException",
            "ModelTimeoutException",
            "ModelNotReadyException",
            "ValidationException",
            "AccessDeniedException",
            "ResourceNotFoundException",
            "ServiceUnavailableException",
            "InternalServerException",
            "ModelErrorException",
        }

    def test_each_value_is_a_class_status_tuple(self):
        for exception_class, status_code in BEDROCK_ERROR_MAP.values():
            assert isinstance(exception_class, type)
            assert issubclass(exception_class, Exception)
            assert status_code is None or isinstance(status_code, int)

    def test_throttling_maps_to_rate_limit_429(self):
        assert BEDROCK_ERROR_MAP["ThrottlingException"] == (RateLimitException, 429)

    def test_model_timeout_maps_to_timeout_408(self):
        assert BEDROCK_ERROR_MAP["ModelTimeoutException"] == (TimeoutException, 408)

    def test_validation_maps_to_invalid_request_400(self):
        assert BEDROCK_ERROR_MAP["ValidationException"] == (InvalidRequestException, 400)

    def test_access_denied_maps_to_authentication_403(self):
        assert BEDROCK_ERROR_MAP["AccessDeniedException"] == (AuthenticationException, 403)

    def test_resource_not_found_maps_to_model_not_found_404(self):
        assert BEDROCK_ERROR_MAP["ResourceNotFoundException"] == (ModelNotFoundException, 404)


class TestOpenAIAndAnthropicErrorMaps:
    """OpenAI and Anthropic use the openai-python SDK exception-class names
    for both, since the anthropic SDK follows the same naming convention."""

    def test_same_key_shape(self):
        assert set(OPENAI_ERROR_MAP.keys()) == set(ANTHROPIC_ERROR_MAP.keys())

    def test_expected_keys_present(self):
        expected = {
            "RateLimitError",
            "APITimeoutError",
            "APIConnectionError",
            "AuthenticationError",
            "PermissionDeniedError",
            "BadRequestError",
            "NotFoundError",
            "UnprocessableEntityError",
            "InternalServerError",
        }
        assert set(OPENAI_ERROR_MAP.keys()) == expected

    def test_rate_limit_maps_to_429(self):
        assert OPENAI_ERROR_MAP["RateLimitError"] == (RateLimitException, 429)
        assert ANTHROPIC_ERROR_MAP["RateLimitError"] == (RateLimitException, 429)

    def test_connection_error_has_no_default_status(self):
        # APIConnectionError deliberately has no default status code (unlike
        # every other entry) — a real network failure has no HTTP response at all.
        assert OPENAI_ERROR_MAP["APIConnectionError"] == (ServiceUnavailableException, None)
        assert ANTHROPIC_ERROR_MAP["APIConnectionError"] == (ServiceUnavailableException, None)

    def test_timeout_maps_to_timeout_exception(self):
        assert OPENAI_ERROR_MAP["APITimeoutError"][0] is TimeoutException
        assert ANTHROPIC_ERROR_MAP["APITimeoutError"][0] is TimeoutException


class TestGoogleErrorMap:
    def test_keyed_by_http_status_int_not_class_name(self):
        assert all(isinstance(k, int) for k in GOOGLE_ERROR_MAP)

    def test_expected_status_codes_present(self):
        assert set(GOOGLE_ERROR_MAP.keys()) == {400, 401, 403, 404, 408, 429, 500, 503}

    def test_values_are_plain_classes_not_tuples(self):
        # Unlike the other three maps, Google's map has no per-entry default
        # status code tuple — the key IS the status code already.
        for exception_class in GOOGLE_ERROR_MAP.values():
            assert isinstance(exception_class, type)
            assert issubclass(exception_class, Exception)

    def test_429_maps_to_rate_limit(self):
        assert GOOGLE_ERROR_MAP[429] is RateLimitException

    def test_503_and_500_both_map_to_service_unavailable(self):
        assert GOOGLE_ERROR_MAP[500] is ServiceUnavailableException
        assert GOOGLE_ERROR_MAP[503] is ServiceUnavailableException

    def test_403_maps_to_permission_denied(self):
        assert GOOGLE_ERROR_MAP[403] is PermissionDeniedException

    def test_model_error_not_used_by_google(self):
        # ModelErrorException is Bedrock-specific (its `ModelErrorException`
        # error code) — Google's map has no equivalent entry.
        assert ModelErrorException not in GOOGLE_ERROR_MAP.values()
