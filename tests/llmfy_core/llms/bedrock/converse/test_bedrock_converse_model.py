"""Smoke tests for llmfy/llmfy_core/llms/bedrock/converse/bedrock_converse_model.py.

Deep formatting logic is covered by test_bedrock_converse_formatter.py; this
covers construction, one successful generate() path, and error mapping.
`boto3.client(...)` constructs successfully offline with fake credentials —
no network call happens until `.converse(...)` is invoked, which is what we mock.
"""

from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

import llmfy.llmfy_core.llms.bedrock.converse.bedrock_converse_model as bedrock_model_module
from llmfy.exception.llmfy_exception import LLMfyException, RateLimitException
from llmfy.llmfy_core.llms.bedrock.converse.bedrock_converse_model import (
    BedrockConverseModel,
)
from llmfy.llmfy_core.model_backend import ModelBackend
from llmfy.llmfy_core.service_provider import ServiceProvider


@pytest.fixture
def model(provider_api_keys) -> BedrockConverseModel:
    return BedrockConverseModel(model="amazon.nova-pro-v1:0")


def test_construction_sets_backend_and_provider(model: BedrockConverseModel):
    assert model.backend == ModelBackend.BEDROCK_CONVERSE
    assert model.provider == ServiceProvider.BEDROCK


def test_raises_without_credentials(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    with pytest.raises(LLMfyException, match="AWS_ACCESS_KEY_ID"):
        BedrockConverseModel(model="amazon.nova-pro-v1:0")


def test_raises_without_region(monkeypatch, provider_api_keys):
    monkeypatch.delenv("AWS_BEDROCK_REGION", raising=False)
    with pytest.raises(LLMfyException, match="AWS_BEDROCK_REGION"):
        BedrockConverseModel(model="amazon.nova-pro-v1:0")


def test_raises_when_boto3_missing(provider_api_keys, monkeypatch):
    monkeypatch.setattr(bedrock_model_module, "boto3", None)
    with pytest.raises(LLMfyException, match="boto3 package is not installed"):
        BedrockConverseModel(model="amazon.nova-pro-v1:0")


def test_generate_parses_text_response(model: BedrockConverseModel):
    response = {
        "output": {"message": {"content": [{"text": "Hello there"}]}},
        "stopReason": "end_turn",
        "ResponseMetadata": {"RequestId": "req_1"},
    }
    model.client.converse = MagicMock(return_value=response)  # type: ignore
    result = model.generate(messages=[{"role": "user", "content": [{"text": "hi"}]}])
    assert result.content == "Hello there"
    assert result.tool_calls is None


def test_generate_parses_tool_use_response(model: BedrockConverseModel):
    response = {
        "output": {
            "message": {
                "content": [
                    {
                        "toolUse": {
                            "toolUseId": "tu_1",
                            "name": "get_weather",
                            "input": {"city": "Paris"},
                        }
                    }
                ]
            }
        },
        "stopReason": "tool_use",
        "ResponseMetadata": {"RequestId": "req_1"},
    }
    model.client.converse = MagicMock(return_value=response)  # type: ignore
    result = model.generate(
        messages=[{"role": "user", "content": [{"text": "weather?"}]}]
    )
    assert result.tool_calls[0].name == "get_weather"  # type: ignore
    assert result.tool_calls[0].arguments == {"city": "Paris"}  # type: ignore


def test_provider_client_error_is_mapped(model: BedrockConverseModel):
    error = ClientError(
        {
            "Error": {"Code": "ThrottlingException", "Message": "Too many requests"},
            "ResponseMetadata": {"HTTPStatusCode": 429},
        },
        "Converse",
    )
    model.client.converse = MagicMock(side_effect=error)  # type: ignore
    with pytest.raises(RateLimitException):
        model.generate(messages=[{"role": "user", "content": [{"text": "hi"}]}])
