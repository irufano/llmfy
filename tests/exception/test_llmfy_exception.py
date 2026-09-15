"""Unit tests for the LLMfyException hierarchy (llmfy/exception/llmfy_exception.py)."""

import pytest

from llmfy.exception.llmfy_exception import (
    AuthenticationException,
    ContentFilterException,
    InvalidRequestException,
    LLMfyException,
    ModelErrorException,
    ModelNotFoundException,
    PermissionDeniedException,
    QuotaExceededException,
    RateLimitException,
    ServiceUnavailableException,
    TimeoutException,
    TimeoutType,
)

# Every leaf subclass except TimeoutException has no added behavior — its own
# __init__/__repr__ is inherited unmodified from LLMfyException.
PLAIN_SUBCLASSES = [
    RateLimitException,
    QuotaExceededException,
    InvalidRequestException,
    AuthenticationException,
    PermissionDeniedException,
    ModelNotFoundException,
    ServiceUnavailableException,
    ContentFilterException,
    ModelErrorException,
]


class TestLLMfyExceptionBase:
    def test_message_only_construction_does_not_raise(self):
        exc = LLMfyException("boom")
        assert exc.message == "boom"
        assert exc.status_code is None
        assert exc.raw_error is None
        assert exc.provider is None

    def test_str_returns_message(self):
        # super().__init__(message) means str(exc) mirrors plain Exception behavior
        exc = LLMfyException("something went wrong")
        assert str(exc) == "something went wrong"

    def test_all_fields_stored(self):
        raw = {"foo": "bar"}
        exc = LLMfyException(
            "boom", status_code=500, raw_error=raw, provider="openai"
        )
        assert exc.message == "boom"
        assert exc.status_code == 500
        assert exc.raw_error is raw
        assert exc.provider == "openai"

    def test_repr_format(self):
        exc = LLMfyException("boom", status_code=429, provider="openai")
        assert repr(exc) == "LLMfyException(message='boom', status_code=429, provider='openai')"

    def test_repr_omits_raw_error(self):
        exc = LLMfyException("boom", raw_error={"secret": "value"})
        assert "secret" not in repr(exc)

    def test_is_a_plain_exception(self):
        assert isinstance(LLMfyException("x"), Exception)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(LLMfyException) as exc_info:
            raise LLMfyException("failure", status_code=400)
        assert exc_info.value.status_code == 400


class TestPlainSubclasses:
    @pytest.mark.parametrize("exc_class", PLAIN_SUBCLASSES)
    def test_subclass_of_llmfy_exception(self, exc_class):
        exc = exc_class("boom")
        assert isinstance(exc, LLMfyException)
        assert isinstance(exc, Exception)

    @pytest.mark.parametrize("exc_class", PLAIN_SUBCLASSES)
    def test_repr_uses_concrete_class_name(self, exc_class):
        exc = exc_class("boom", status_code=1, provider="openai")
        assert repr(exc).startswith(f"{exc_class.__name__}(")

    @pytest.mark.parametrize("exc_class", PLAIN_SUBCLASSES)
    def test_full_field_construction(self, exc_class):
        exc = exc_class("boom", status_code=503, raw_error={"a": 1}, provider="bedrock")
        assert exc.message == "boom"
        assert exc.status_code == 503
        assert exc.raw_error == {"a": 1}
        assert exc.provider == "bedrock"


class TestTimeoutException:
    def test_default_timeout_type_is_none(self):
        exc = TimeoutException("timed out")
        assert exc.timeout_type is None

    @pytest.mark.parametrize(
        "timeout_type",
        [TimeoutType.CONNECT, TimeoutType.READ, TimeoutType.WRITE, TimeoutType.POOL, TimeoutType.MODEL],
    )
    def test_stores_timeout_type(self, timeout_type):
        exc = TimeoutException("timed out", timeout_type=timeout_type)
        assert exc.timeout_type is timeout_type

    def test_inherits_base_fields(self):
        exc = TimeoutException(
            "timed out", status_code=408, provider="openai", timeout_type=TimeoutType.READ
        )
        assert exc.message == "timed out"
        assert exc.status_code == 408
        assert exc.provider == "openai"

    def test_repr_does_not_include_timeout_type(self):
        # TimeoutException does not override __repr__, so it stays the base
        # LLMfyException format — timeout_type is silently absent from repr().
        exc = TimeoutException("timed out", timeout_type=TimeoutType.CONNECT)
        assert "timeout_type" not in repr(exc)
        assert "connect" not in repr(exc)

    def test_is_llmfy_exception(self):
        assert isinstance(TimeoutException("x"), LLMfyException)


class TestTimeoutTypeEnum:
    def test_values(self):
        assert TimeoutType.CONNECT.value == "connect"
        assert TimeoutType.READ.value == "read"
        assert TimeoutType.WRITE.value == "write"
        assert TimeoutType.POOL.value == "pool"
        assert TimeoutType.MODEL.value == "model"
