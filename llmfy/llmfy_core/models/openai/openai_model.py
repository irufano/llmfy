try:
    import openai
except ImportError:
    openai = None

import json
import os
from typing import Any, Dict, List, Optional

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.messages.tool_call import ToolCall
from llmfy.llmfy_core.models.base_ai_model import BaseAIModel
from llmfy.llmfy_core.models.openai.openai_config import OpenAIConfig
from llmfy.llmfy_core.models.openai.openai_stream_usage_tracker import (
    track_openai_stream_usage,
)
from llmfy.llmfy_core.models.openai.openai_usage import OpenAIUsage

# from app.llmfy.models.openai.openai_usage_tracker import track_openai_usage
from llmfy.llmfy_core.responses.ai_response import AIResponse
from llmfy.llmfy_core.service_provider import ServiceProvider


class OpenAIModel(BaseAIModel):
    """
    OpenAIModel class.

    Example:
    ```python
    # Configuration
    config = OpenAIConfig(
            temperature=0.7
    )
    llm = OpenAIModel(model="gpt-4o-mini", config=config)
    ...
    ```
    """

    def __init__(self, model: str, config: OpenAIConfig):
        if openai is None:
            raise LLMfyException(
                'openai package is not installed. Install it using `pip install "llmy[openai]"`'
            )
        if not os.getenv("OPENAI_API_KEY"):
            raise LLMfyException("Please provide `OPENAI_API_KEY` on your environment!")

        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.provider = ServiceProvider.OPENAI
        self.model_name = model
        self.config = config
        self.usage_callback = OpenAIUsage()

    # @track_openai_usage
    # def __call_openai(self, params: dict[str, Any]):
    #     try:
    #         response = self.client.chat.completions.create(**params)
    #         return response
    #     except Exception as e:
    #         raise e

    def __call_openai(self, params: dict[str, Any]):
        # Import the decorator when the method is first defined/called
        from llmfy.llmfy_core.usage.usage_tracker import track_openai_usage

        @track_openai_usage
        def _call_openai_impl(params: dict[str, Any]):
            try:
                response = self.client.chat.completions.create(**params)
                return response
            except Exception as e:
                raise e

        return _call_openai_impl(params)

    @track_openai_stream_usage
    def __call_stream_openai(self, params: dict[str, Any]):
        try:
            params["stream"] = True
            params["stream_options"] = {"include_usage": True}
            return self.client.chat.completions.create(**params)
        except Exception as e:
            raise e

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> AIResponse:
        """
        Generate messages.

        Args:
                messages (List[Dict[str, Any]]): _description_
                tools (Optional[List[Dict[str, Any]]], optional): _description_. Defaults to None.

        Raises:
                AIGooChatException: _description_

        Returns:
                AIResponse: _description_
        """
        try:
            params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "top_p": self.config.top_p,
                "frequency_penalty": self.config.frequency_penalty,
                "presence_penalty": self.config.presence_penalty,
                "stream": False,
                **kwargs,
            }

            if tools:
                params["tools"] = [
                    {"type": "function", "function": tool} for tool in tools
                ]
                params["tool_choice"] = "auto"

            response = self.__call_openai(params)

            message = response.choices[0].message
            tool_calls = None
            content = None
            # print(f"usage openai: {response.usage.model_dump()}")
            # token_usage = self.usage_callback.update(self.model_name, response.usage)

            if hasattr(message, "tool_calls") and message.tool_calls:
                tool_calls = [
                    ToolCall(
                        request_call_id=response.id,
                        tool_call_id=tool_call.id,
                        name=tool_call.function.name,
                        arguments=json.loads(tool_call.function.arguments),
                    )
                    for tool_call in message.tool_calls
                ]
            else:
                content = message.content

            return AIResponse(
                content=content,
                tool_calls=tool_calls,
            )

        except Exception as e:
            raise LLMfyException(e)

    def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Any:
        """
        Generate messages with streaming.

        Note:
                When using stream=True, the response does not include total usage information (usage field with prompt_tokens, completion_tokens, and total_tokens).

                Why?

                \t- In streaming mode, tokens are sent incrementally, so the API doesnt return a single final response that includes token usage.
                \t- If you need token usage, you must track tokens manually or make a separate non-streaming request.

        Args:
                messages (List[Dict[str, Any]]): _description_
                tools (Optional[List[Dict[str, Any]]], optional): _description_. Defaults to None.

        Raises:
                AIGooChatException: _description_

        Returns:
                Any: _description_
        """
        try:
            params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                **kwargs,
            }

            if tools:
                params["tools"] = [
                    {"type": "function", "function": tool} for tool in tools
                ]
                params["tool_choice"] = "auto"

            stream = self.__call_stream_openai(params)

            tool_calls_accumulator = {}
            tool_calls = None

            for chunk in stream:
                if chunk.usage:
                    # ChatCompletionChunk(id='chatcmpl-B5SIoSdLpEFk9gFH0Vl4B6hM6st8H', choices=[], created=1740640134, model='gpt-4o-mini-2024-07-18', object='chat.completion.chunk', service_tier='default', system_fingerprint='fp_06737a9306', usage=CompletionUsage(completion_tokens=11, prompt_tokens=56, total_tokens=67, completion_tokens_details=CompletionTokensDetails(accepted_prediction_tokens=0, audio_tokens=0, reasoning_tokens=0, rejected_prediction_tokens=0), prompt_tokens_details=PromptTokensDetails(audio_tokens=0, cached_tokens=0)))
                    # usage = chunk.usage
                    # print(f"completion_tokens = {usage.completion_tokens or ''}")
                    # print(f"prompt_tokens = {usage.prompt_tokens or ''}")
                    # print(f"total_tokens = {usage.total_tokens or ''}")
                    pass

                if chunk.choices:
                    content = None

                    delta = chunk.choices[0].delta

                    if delta.content is not None:
                        content = delta.content

                    if delta.tool_calls is not None:
                        tool_calls = []
                        for tool_call in delta.tool_calls:
                            tool_call_id = (
                                tool_call.id
                            )  # Exists only in the first chunk

                            if tool_call_id:  # First chunk of a new tool call
                                tool_calls_accumulator[tool_call_id] = {
                                    "request_call_id": chunk.id,
                                    "tool_call_id": tool_call_id,
                                    "name": tool_call.function.name,
                                    "arguments": "",
                                }

                            # Find the active tool call in the accumulator
                            active_tool_call = next(
                                iter(tool_calls_accumulator.values()), None
                            )
                            if active_tool_call:
                                # Accumulate arguments across multiple chunks
                                active_tool_call["arguments"] += (
                                    tool_call.function.arguments or ""
                                )

                                # Try to parse accumulated JSON when complete
                                try:
                                    parsed_arguments = json.loads(
                                        active_tool_call["arguments"]
                                    )

                                    # Construct the ToolCall object
                                    tool_calls.append(
                                        ToolCall(
                                            request_call_id=active_tool_call[
                                                "request_call_id"
                                            ],
                                            tool_call_id=active_tool_call[
                                                "tool_call_id"
                                            ],
                                            name=active_tool_call["name"],
                                            arguments=parsed_arguments,
                                        )
                                    )

                                    # Remove the tool call once fully processed
                                    del tool_calls_accumulator[
                                        active_tool_call["tool_call_id"]
                                    ]

                                except json.JSONDecodeError:
                                    # JSON is incomplete, continue accumulating
                                    pass

                    yield AIResponse(
                        content=content,
                        tool_calls=tool_calls if tool_calls else None,
                    )

        except Exception as e:
            raise LLMfyException(e)
