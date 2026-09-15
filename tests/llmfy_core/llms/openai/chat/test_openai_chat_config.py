"""Unit tests for llmfy/llmfy_core/llms/openai/chat/openai_chat_config.py."""

from llmfy.llmfy_core.llms.openai.chat.openai_chat_config import (
    OpenAIChatConfig,
    OpenAIChatPromptCachingConfig,
    OpenAIChatThinkingConfig,
)


def test_defaults():
    config = OpenAIChatConfig()
    assert config.temperature == 0.7
    assert config.max_tokens is None
    assert config.top_p == 1.0
    assert config.frequency_penalty == 0.0
    assert config.presence_penalty == 0.0
    assert config.thinking.enabled is False
    assert config.prompt_caching.enabled is False


def test_temperature_and_top_p_can_be_set_to_none_to_omit_from_request():
    config = OpenAIChatConfig(temperature=None, top_p=None)
    assert config.temperature is None
    assert config.top_p is None


def test_nested_thinking_config():
    config = OpenAIChatConfig(thinking=OpenAIChatThinkingConfig(enabled=True, effort="high"))
    assert config.thinking.enabled is True
    assert config.thinking.effort == "high"


def test_nested_prompt_caching_config():
    config = OpenAIChatConfig(prompt_caching=OpenAIChatPromptCachingConfig(enabled=True))
    assert config.prompt_caching.enabled is True
