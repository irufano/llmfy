try:
    import boto3
except ImportError:
    boto3 = None

import json
import os
from typing import Any, Dict, List

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.llms.base_ai_model import BaseAIModel
from llmfy.llmfy_core.llms.bedrock.bedrock_config import (
    BedrockConfig,
)
from llmfy.llmfy_core.messages.tool_call import ToolCall
from llmfy.llmfy_core.responses.ai_response import AIResponse
from llmfy.llmfy_core.service_provider import ServiceProvider


class BedrockModel(BaseAIModel):
    """
    BedrockModel class.

    Example:
    ```python
    # Configuration
    config = BedrockConfig(
            temperature=0.7
    )
    llm = BedrockModel(model="amazon.nova-pro-v1:0", config=config)
    ...
    ```
    """

    def __init__(self, model: str, config: BedrockConfig = BedrockConfig()):
        """
        BedrockModel

        Args:
            model (str): Model ID
            config (BedrockConfig, optional): Configuration. Defaults to BedrockConfig().
        """
        if boto3 is None:
            raise LLMfyException(
                'boto3 package is not installed. Install it using `pip install "llmfy[boto3]"`'
            )
        if not os.getenv("AWS_ACCESS_KEY_ID"):
            raise LLMfyException(
                "Please provide `AWS_ACCESS_KEY_ID` on your environment!"
            )
        if not os.getenv("AWS_SECRET_ACCESS_KEY"):
            raise LLMfyException(
                "Please provide `AWS_SECRET_ACCESS_KEY` on your environment!"
            )
        if not os.getenv("AWS_BEDROCK_REGION"):
            raise LLMfyException(
                "Please provide `AWS_BEDROCK_REGION` on your environment!"
            )

        self.provider = ServiceProvider.BEDROCK
        self.model_name = model
        self.config = config
        self.client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_BEDROCK_REGION"),
        )

    def __call_bedrock(self, params: dict[str, Any]):
        # Import the decorator when the method is first defined/called
        from botocore.exceptions import (
            ClientError,
            ConnectTimeoutError,
            ReadTimeoutError,
        )

        from llmfy.exception.exception_handler import handle_bedrock_error
        from llmfy.llmfy_core.llms.bedrock.bedrock_usage import track_bedrock_usage

        @track_bedrock_usage
        def _call_bedrock_impl(params: dict[str, Any]):
            try:
                response = self.client.converse(**params)
                return response
            except (ClientError, ReadTimeoutError, ConnectTimeoutError) as e:
                raise handle_bedrock_error(e)

        return _call_bedrock_impl(params)

    def __call_stream_bedrock(self, params: dict[str, Any]):
        # Import the decorator when the method is first defined/called
        from botocore.exceptions import (
            ClientError,
            ConnectTimeoutError,
            ReadTimeoutError,
        )

        from llmfy.exception.exception_handler import handle_bedrock_error
        from llmfy.llmfy_core.llms.bedrock.bedrock_usage import (
            track_bedrock_stream_usage,
        )

        @track_bedrock_stream_usage
        def _call_stream_bedrock_impl(params: dict[str, Any]):
            try:
                return self.client.converse_stream(**params)
            except (ClientError, ReadTimeoutError, ConnectTimeoutError) as e:
                raise handle_bedrock_error(e)

        return _call_stream_bedrock_impl(params)

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]] | None = None,
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
            _system = next(
                (msg["content"] for msg in messages if msg["role"] == "system"), None
            )
            _messages = [msg for msg in messages if msg["role"] != "system"]

            inferences = {
                "temperature": self.config.temperature,
                "maxTokens": self.config.max_tokens,
                "stopSequences": self.config.stopSequences,
                "topP": self.config.top_p,
            }
            # Remove None values
            inference_config = {
                key: value for key, value in inferences.items() if value is not None
            }

            additionals: Dict[str, Any] = {
                "top_k": self.config.top_k,
                **kwargs,
            }

            if self.config.enable_thinking:
                if self.config.reasoning_effort is not None:
                    # Amazon Nova 2 Lite format
                    additionals["reasoningConfig"] = {
                        "type": "enabled",
                        "maxReasoningEffort": self.config.reasoning_effort,
                    }
                elif self.config.thinking_type == "adaptive":
                    # Claude adaptive thinking (Sonnet/Opus 4.6, Fable 5, Mythos 5, Opus 4.7)
                    additionals["thinking"] = {"type": "adaptive"}
                    if self.config.thinking_effort is not None:
                        additionals["output_config"] = {
                            "effort": self.config.thinking_effort
                        }
                else:
                    # Claude extended thinking (3.7 Sonnet, Claude 4 Sonnet/Opus/Haiku, 4.5 series)
                    _thinking: Dict[str, Any] = {"type": "enabled"}
                    if self.config.thinking_budget_tokens is not None:
                        _thinking["budget_tokens"] = self.config.thinking_budget_tokens
                    additionals["thinking"] = _thinking

            # Remove None values
            additional_config = {
                key: value for key, value in additionals.items() if value is not None
            }

            params = {
                "modelId": self.model_name,
                "messages": _messages,
                "inferenceConfig": inference_config,
                "additionalModelRequestFields": additional_config,
                **({"system": _system} if _system is not None else {}),
            }

            # Prompt caching: inject cachePoint markers for supported Claude models.
            # cachePoints are evaluated cumulatively: tools → system → messages.
            # A cachePoint after the system caches the system prompt (~90% savings).
            # A cachePoint at the end of the last message caches the full conversation
            # prefix so the next turn can serve it from cache.
            if self.config.enable_prompt_caching:
                _cache_point: Dict[str, Any] = {"type": "default"}
                if self.config.prompt_caching_ttl is not None:
                    _cache_point["ttl"] = self.config.prompt_caching_ttl
                _cache_point_entry = {"cachePoint": _cache_point}

                if _system is not None:
                    # Bedrock cache is a byte-identical prefix match, 
                    # if system prompt changes, which invalidates the cache every time
                    # "You are an expert in Python"     → cache WRITE A (cached for 5 min)
                    # "You are an expert in JavaScript" → cache WRITE B (different prefix, separate cache)
                    # "You are an expert in Go"         → cache WRITE C (different prefix, separate cache)
                    # "You are an expert in Python"     → cache READ D (hit! same as Call 1, still within 5 min)
                    params["system"] = list(_system) + [_cache_point_entry]
                if _messages:
                    # Bedrock writes only the DELTA (new tokens since the last cachePoint),
                    # not the full prefix. Read pool grows each turn; write cost stays constant.
                    #
                    # Turn 1:  [user_q1 + cachePoint]
                    #        → WRITE delta: system + user_q1          (all new, no prior cache)
                    #
                    # Turn 2:  [user_q1, assistant_r1, user_q2 + cachePoint]
                    #        → READ  system + user_q1                 ← from Turn 1's cachePoint
                    #        → WRITE delta: assistant_r1 + user_q2    ← only new tokens since Turn 1
                    #
                    # Turn 3:  [user_q1, assistant_r1, user_q2, assistant_r2, user_q3 + cachePoint]
                    #        → READ  system + user_q1 + assistant_r1 + user_q2  ← from Turn 2's cachePoint
                    #        → WRITE delta: assistant_r2 + user_q3    ← only new tokens since Turn 2
                    #
                    # Write cost is CONSTANT from Turn 2 onwards (delta per turn only).
                    # Read pool GROWS each turn — savings increase with conversation length.
                    _messages = list(_messages)
                    last_msg = _messages[-1]
                    last_content = list(last_msg.get("content", []))
                    last_content.append(_cache_point_entry)
                    _messages[-1] = {**last_msg, "content": last_content}
                    params["messages"] = _messages

            if tools:
                """
                ToolConfig
                {
                    "tools": [
                        {
                            "toolSpec": {
                                "name": "top_song",
                                "description": "Get the most popular song played on a radio station.",
                                "inputSchema": {
                                    "json": {
                                        "type": "object",
                                        "properties": {
                                            "sign": {
                                                "type": "string",
                                                "description": "The call sign for the radio station for which you want the most popular song. Example calls signs are WZPZ and WKRP."
                                            }
                                        },
                                        "required": [
                                            "sign"
                                        ]
                                    }
                                }
                            }
                        }
                    ]
                }
                """
                params["toolConfig"] = {"tools": [{"toolSpec": tool} for tool in tools]}

            response = self.__call_bedrock(params)

            output_message = response["output"]["message"]
            stop_reason = response["stopReason"]
            tool_calls = None
            content = None

            if stop_reason == "tool_use":
                tool_requests = response["output"]["message"]["content"]
                tool_callings = []
                for tool_request in tool_requests:
                    if "toolUse" in tool_request:
                        tool = tool_request["toolUse"]
                        tool_callings.append(
                            ToolCall(
                                request_call_id=response["ResponseMetadata"][
                                    "RequestId"
                                ],
                                tool_call_id=tool["toolUseId"],
                                name=tool["name"],
                                arguments=tool["input"],
                            )
                        )
                tool_calls = tool_callings
            else:
                content = output_message["content"][0]["text"]

            return AIResponse(
                content=content,
                tool_calls=tool_calls,
            )
        except Exception as e:
            if isinstance(e, LLMfyException):
                raise  # Already handled, re-raise as-is
            raise LLMfyException(str(e), raw_error=e)

    def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]] | None = None,
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
            _system = next(
                (msg["content"] for msg in messages if msg["role"] == "system"), None
            )
            _messages = [msg for msg in messages if msg["role"] != "system"]

            inferences = {
                "temperature": self.config.temperature,
                "maxTokens": self.config.max_tokens,
                "stopSequences": self.config.stopSequences,
                "topP": self.config.top_p,
            }
            # Remove None values
            inference_config = {
                key: value for key, value in inferences.items() if value is not None
            }

            additionals: Dict[str, Any] = {
                "top_k": self.config.top_k,
                **kwargs,
            }

            if self.config.enable_thinking:
                if self.config.reasoning_effort is not None:
                    # Amazon Nova 2 Lite format
                    additionals["reasoningConfig"] = {
                        "type": "enabled",
                        "maxReasoningEffort": self.config.reasoning_effort,
                    }
                elif self.config.thinking_type == "adaptive":
                    # Claude adaptive thinking (Sonnet/Opus 4.6, Fable 5, Mythos 5, Opus 4.7)
                    additionals["thinking"] = {"type": "adaptive"}
                    if self.config.thinking_effort is not None:
                        additionals["output_config"] = {
                            "effort": self.config.thinking_effort
                        }
                else:
                    # Claude extended thinking (3.7 Sonnet, Claude 4 Sonnet/Opus/Haiku, 4.5 series)
                    _thinking: Dict[str, Any] = {"type": "enabled"}
                    if self.config.thinking_budget_tokens is not None:
                        _thinking["budget_tokens"] = self.config.thinking_budget_tokens
                    additionals["thinking"] = _thinking

            # Remove None values
            additional_config = {
                key: value for key, value in additionals.items() if value is not None
            }

            params = {
                "modelId": self.model_name,
                "messages": _messages,
                "inferenceConfig": inference_config,
                "additionalModelRequestFields": additional_config,
                **({"system": _system} if _system is not None else {}),
            }

            # Prompt caching: inject cachePoint markers for supported Claude models.
            # cachePoints are evaluated cumulatively: tools → system → messages.
            # A cachePoint after the system caches the system prompt (~90% savings).
            # A cachePoint at the end of the last message caches the full conversation
            # prefix so the next turn can serve it from cache.
            if self.config.enable_prompt_caching:
                _cache_point: Dict[str, Any] = {"type": "default"}
                if self.config.prompt_caching_ttl is not None:
                    _cache_point["ttl"] = self.config.prompt_caching_ttl
                _cache_point_entry = {"cachePoint": _cache_point}

                if _system is not None:
                    # Bedrock cache is a byte-identical prefix match, 
                    # if system prompt changes, which invalidates the cache every time.
                    # "You are an expert in Python"     → cache WRITE A (cached for 5 min)
                    # "You are an expert in JavaScript" → cache WRITE B (different prefix, separate cache)
                    # "You are an expert in Go"         → cache WRITE C (different prefix, separate cache)
                    # "You are an expert in Python"     → cache READ D (hit! same as Call 1, still within 5 min)
                    params["system"] = list(_system) + [_cache_point_entry]
                if _messages:
                    # Bedrock writes only the DELTA (new tokens since the last cachePoint),
                    # not the full prefix. Read pool grows each turn; write cost stays constant.
                    #
                    # Turn 1:  [user_q1 + cachePoint]
                    #        → WRITE delta: system + user_q1          (all new, no prior cache)
                    #
                    # Turn 2:  [user_q1, assistant_r1, user_q2 + cachePoint]
                    #        → READ  system + user_q1                 ← from Turn 1's cachePoint
                    #        → WRITE delta: assistant_r1 + user_q2    ← only new tokens since Turn 1
                    #
                    # Turn 3:  [user_q1, assistant_r1, user_q2, assistant_r2, user_q3 + cachePoint]
                    #        → READ  system + user_q1 + assistant_r1 + user_q2  ← from Turn 2's cachePoint
                    #        → WRITE delta: assistant_r2 + user_q3    ← only new tokens since Turn 2
                    #
                    # Write cost is CONSTANT from Turn 2 onwards (delta per turn only).
                    # Read pool GROWS each turn — savings increase with conversation length.
                    _messages = list(_messages)
                    last_msg = _messages[-1]
                    last_content = list(last_msg.get("content", []))
                    last_content.append(_cache_point_entry)
                    _messages[-1] = {**last_msg, "content": last_content}
                    params["messages"] = _messages

            if tools:
                params["toolConfig"] = {"tools": [{"toolSpec": tool} for tool in tools]}

            response = self.__call_stream_bedrock(params)
            res_metadata = response.get("ResponseMetadata")
            stream = response.get("stream")

            request_id = res_metadata.get("RequestId")
            tool_calls_accumulator = {}
            tools = []
            tool_calls_accumulator["tools"] = tools
            tool_use = {}

            if stream:
                tooluse_id = None
                for chunk in stream:
                    text = None

                    if "messageStart" in chunk:
                        # print(f"\nRole: {chunk['messageStart']['role']}")
                        pass

                    elif "contentBlockStart" in chunk:
                        tool = chunk["contentBlockStart"]["start"]["toolUse"]
                        tooluse_id = tool["toolUseId"]
                        tool_use["toolUseId"] = tooluse_id
                        tool_use["name"] = tool["name"]
                        # print(f"\nSTART: {tooluse_id}")
                        # print(f"START: {tool_use}")

                    if "contentBlockDelta" in chunk:
                        delta = chunk["contentBlockDelta"]["delta"]
                        # print(f"\nDELTA: {delta}")
                        if "text" in delta:
                            text = delta["text"]

                        if "toolUse" in delta:
                            if "input" not in tool_use:
                                tool_use["input"] = ""
                            tool_use["input"] += delta["toolUse"]["input"]

                    elif "contentBlockStop" in chunk:
                        if "input" in tool_use:
                            # print(f"TOOLS: {tools}")
                            # print(f"TOOL_USE: {tool_use}")
                            tool_use["input"] = json.loads(tool_use["input"])
                            tools.append({"toolUse": tool_use})
                            tool_use = {}

                    if "messageStop" in chunk:
                        # print(f"FINAL_TOOLS : {tools}")
                        # print(f"\nStop reason: {chunk['messageStop']['stopReason']}")
                        pass

                    if "metadata" in chunk:
                        metadata = chunk["metadata"]
                        if "usage" in metadata:
                            # print("\nToken usage")
                            # print(f"Input tokens: {metadata['usage']['inputTokens']}")
                            # print(
                            #     f":Output tokens: {metadata['usage']['outputTokens']}"
                            # )
                            # print(f":Total tokens: {metadata['usage']['totalTokens']}")
                            pass
                        if "metrics" in chunk["metadata"]:
                            # print(
                            #     f"Latency: {metadata['metrics']['latencyMs']} milliseconds"
                            # )
                            pass

                    tool_calls = []

                    for tools_content in tool_calls_accumulator["tools"]:
                        if "toolUse" in tools_content:
                            tool = tools_content["toolUse"]
                            tool_calls.append(
                                ToolCall(
                                    request_call_id=request_id,
                                    tool_call_id=tool["toolUseId"],
                                    name=tool["name"],
                                    arguments=tool["input"],
                                )
                            )

                    yield AIResponse(
                        content=text,
                        tool_calls=tool_calls if tool_calls else None,
                    )

        except Exception as e:
            if isinstance(e, LLMfyException):
                raise  # Already handled, re-raise as-is
            raise LLMfyException(str(e), raw_error=e)
