try:
    import anthropic
except ImportError:
    anthropic = None

import json
import os
from typing import Any

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.llms.anthropic.messages.anthropic_messages_config import (
    AnthropicMessagesConfig,
)
from llmfy.llmfy_core.llms.base_ai_model import BaseAIModel
from llmfy.llmfy_core.messages.tool_call import ToolCall
from llmfy.llmfy_core.model_backend import ModelBackend
from llmfy.llmfy_core.responses.ai_response import AIResponse
from llmfy.llmfy_core.service_provider import ServiceProvider


class AnthropicMessagesModel(BaseAIModel):
    """
    AnthropicMessagesModel class - native Anthropic Messages API
    (api.anthropic.com).

    Example:
    ```python
    config = AnthropicMessagesConfig(max_tokens=8192)
    llm = AnthropicMessagesModel(model="claude-sonnet-5", config=config)
    ```
    """

    def __init__(
        self,
        model: str,
        config: AnthropicMessagesConfig | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        default_headers: dict[str, str] | None = None,
    ):
        """
        AnthropicMessagesModel

        Args:
            model (str): Model ID
            config (AnthropicMessagesConfig, optional): Configuration. Defaults to AnthropicMessagesConfig().
            api_key (str, optional): Anthropic API key. Defaults to the
                `ANTHROPIC_API_KEY` environment variable if not provided.
            base_url (str, optional): Override the API base URL (e.g. for a proxy or
                a compatible endpoint such as AWS Bedrock's `bedrock-mantle`).
            default_headers (dict[str, str], optional): Extra HTTP headers sent on every
                request, passed straight through to the `anthropic` SDK client. Needed for
                endpoints that require headers beyond `x-api-key`/`anthropic-version` — e.g.
                Bedrock Mantle's `anthropic-workspace-id` header for Workspace scoping.
        """
        config = config if config is not None else AnthropicMessagesConfig()
        if anthropic is None:
            raise LLMfyException(
                'anthropic package is not installed. Install it using `pip install "llmfy[anthropic]"`'
            )

        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMfyException(
                "Please provide `ANTHROPIC_API_KEY` on your environment or pass `api_key`!"
            )

        self.backend = ModelBackend.ANTHROPIC_MESSAGES
        self.provider = ServiceProvider.ANTHROPIC
        self.model_name = model
        self.config = config
        self.client = anthropic.Anthropic(
            api_key=api_key, base_url=base_url, default_headers=default_headers
        )

    def __call_anthropic(self, params: dict[str, Any]):
        # Import the decorator when the method is first defined/called
        from anthropic import APIError

        from llmfy.exception.exception_handler import handle_anthropic_error
        from llmfy.llmfy_core.llms.anthropic.messages.anthropic_messages_usage import (
            track_anthropic_messages_usage,
        )

        @track_anthropic_messages_usage
        def _call_anthropic_impl(params: dict[str, Any]):
            try:
                return self.client.messages.create(**params)
            except APIError as e:
                raise handle_anthropic_error(e) from e

        return _call_anthropic_impl(params)

    def __call_stream_anthropic(self, params: dict[str, Any]):
        # Import the decorator when the method is first defined/called
        from anthropic import APIError

        from llmfy.exception.exception_handler import handle_anthropic_error
        from llmfy.llmfy_core.llms.anthropic.messages.anthropic_messages_usage import (
            track_anthropic_messages_stream_usage,
        )

        @track_anthropic_messages_stream_usage
        def _call_stream_anthropic_impl(params: dict[str, Any]):
            try:
                return self.client.messages.create(**params, stream=True)
            except APIError as e:
                raise handle_anthropic_error(e) from e

        return _call_stream_anthropic_impl(params)

    def __build_params(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None
    ) -> dict[str, Any]:
        # System is hoisted out of `messages`, same extraction pattern as
        # BedrockModel — the formatter still emits a {"role": "system", ...}
        # entry; we strip it here and pass it as the top-level `system` param.
        _system = next(
            (msg["content"] for msg in messages if msg["role"] == "system"), None
        )
        _messages = [msg for msg in messages if msg["role"] != "system"]

        params: dict[str, Any] = {
            "model": self.model_name,
            "max_tokens": self.config.max_tokens,  # REQUIRED — always sent
            "messages": _messages,
        }
        if self.config.temperature is not None:
            params["temperature"] = self.config.temperature
        if self.config.top_p is not None:
            params["top_p"] = self.config.top_p
        if self.config.top_k is not None:
            params["top_k"] = self.config.top_k
        if self.config.stop_sequences is not None:
            params["stop_sequences"] = self.config.stop_sequences

        if self.config.thinking.enabled:
            if self.config.thinking.type == "adaptive":
                params["thinking"] = {"type": "adaptive"}
                if self.config.thinking.effort is not None:
                    params["output_config"] = {"effort": self.config.thinking.effort}
            else:
                _thinking: dict[str, Any] = {"type": "enabled"}
                if self.config.thinking.budget_tokens is not None:
                    _thinking["budget_tokens"] = self.config.thinking.budget_tokens
                params["thinking"] = _thinking

        # Prompt caching — inline cache_control on the last block of the
        # prefix to cache (system, and separately the last message). See
        # AnthropicMessagesPromptCachingConfig docstring for the placement
        # rationale.
        if self.config.prompt_caching.enabled:
            cache_control: dict[str, Any] = {"type": "ephemeral"}
            if self.config.prompt_caching.ttl is not None:
                cache_control["ttl"] = self.config.prompt_caching.ttl

            if _system:
                _system = list(_system)
                _system[-1] = {**_system[-1], "cache_control": cache_control}

            if _messages:
                _messages = list(_messages)
                last_msg = _messages[-1]
                last_content = list(last_msg.get("content", []))
                if last_content:
                    last_content[-1] = {
                        **last_content[-1],
                        "cache_control": cache_control,
                    }
                    _messages[-1] = {**last_msg, "content": last_content}
                params["messages"] = _messages

        if _system is not None:
            params["system"] = _system

        if tools:
            params["tools"] = tools
            # No explicit tool_choice — Anthropic defaults to {"type": "auto"}.

        return params

    def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> AIResponse:
        """
        Generate messages.

        Args:
                messages (List[Dict[str, Any]]): _description_
                tools (Optional[List[Dict[str, Any]]], optional): _description_. Defaults to None.

        Returns:
                AIResponse: _description_
        """
        try:
            params = {**self.__build_params(messages, tools), **kwargs}
            response = self.__call_anthropic(params)

            tool_calls = None
            content = None

            if response.stop_reason == "tool_use":
                tool_calls = [
                    ToolCall(
                        request_call_id=response.id,
                        tool_call_id=block.id,
                        name=block.name,
                        arguments=block.input,
                    )
                    for block in response.content
                    if block.type == "tool_use"
                ]
            else:
                text_block = next(
                    (b for b in response.content if b.type == "text"), None
                )
                content = text_block.text if text_block else None

            return AIResponse(content=content, tool_calls=tool_calls)
        except Exception as e:
            if isinstance(e, LLMfyException):
                raise  # Already handled, re-raise as-is
            raise LLMfyException(str(e), raw_error=e) from e

    def generate_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs,
    ) -> Any:
        """
        Generate messages with streaming.

        Args:
                messages (List[Dict[str, Any]]): _description_
                tools (Optional[List[Dict[str, Any]]], optional): _description_. Defaults to None.

        Returns:
                Any: _description_
        """
        try:
            params = {**self.__build_params(messages, tools), **kwargs}
            stream = self.__call_stream_anthropic(params)

            # Index-keyed accumulator (event.index) — every content block
            # carries an explicit index, so multiple parallel tool_use
            # blocks stream correctly (unlike a single-in-flight-call dict).
            blocks: dict[int, dict[str, Any]] = {}
            message_id = ""

            for event in stream:
                text_out = None
                new_tool_call = None

                if event.type == "message_start":
                    message_id = event.message.id

                elif event.type == "content_block_start":
                    cb = event.content_block
                    if cb.type == "tool_use":
                        blocks[event.index] = {
                            "type": "tool_use",
                            "id": cb.id,
                            "name": cb.name,
                            "input_json": "",
                        }
                    elif cb.type == "text":
                        blocks[event.index] = {"type": "text", "text": ""}
                    else:
                        # "thinking" or other future block types — not
                        # surfaced in v1
                        blocks[event.index] = {"type": cb.type}

                elif event.type == "content_block_delta":
                    block = blocks.get(event.index)
                    if block is None:
                        continue
                    if event.delta.type == "text_delta":
                        block["text"] += event.delta.text
                        text_out = event.delta.text
                    elif event.delta.type == "input_json_delta":
                        block["input_json"] += event.delta.partial_json
                    # "thinking_delta" ignored in v1

                elif event.type == "content_block_stop":
                    block = blocks.get(event.index)
                    if block and block["type"] == "tool_use":
                        arguments = (
                            json.loads(block["input_json"])
                            if block["input_json"]
                            else {}
                        )
                        new_tool_call = ToolCall(
                            request_call_id=message_id,
                            tool_call_id=block["id"],
                            name=block["name"],
                            arguments=arguments,
                        )

                if text_out is not None or new_tool_call is not None:
                    yield AIResponse(
                        content=text_out,
                        tool_calls=[new_tool_call] if new_tool_call else None,
                    )

        except Exception as e:
            if isinstance(e, LLMfyException):
                raise  # Already handled, re-raise as-is
            raise LLMfyException(str(e), raw_error=e) from e
