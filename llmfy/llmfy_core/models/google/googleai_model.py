try:
    from google import genai
except ImportError:
    genai = None

import uuid
from typing import Any, Dict, List, Optional

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.messages.tool_call import ToolCall
from llmfy.llmfy_core.models.base_ai_model import BaseAIModel
from llmfy.llmfy_core.models.google.googleai_config import GoogleAIConfig
from llmfy.llmfy_core.responses.ai_response import AIResponse
from llmfy.llmfy_core.service_provider import ServiceProvider


class GoogleAIModel(BaseAIModel):
    """
    GoogleAIModel class.

    Uses the `google-genai` package to interact with Google AI (Gemini) models.

    Example:
    ```python
    # Configuration
    config = GoogleAIConfig(
            temperature=0.7
    )
    llm = GoogleAIModel(model="gemini-2.0-flash", config=config)
    ...
    ```
    """

    def __init__(self, model: str, config: GoogleAIConfig = GoogleAIConfig()):
        """
        GoogleAIModel

        Args:
            model (str): Model ID (e.g. "gemini-2.0-flash")
            config (GoogleAIConfig, optional): Configuration. Defaults to GoogleAIConfig().
        """
        if genai is None:
            raise LLMfyException(
                'google-genai package is not installed. Install it using `pip install "llmfy[google-genai]"`'
            )

        import os

        if not os.getenv("GOOGLE_API_KEY"):
            raise LLMfyException("Please provide `GOOGLE_API_KEY` on your environment!")

        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.provider = ServiceProvider.GOOGLE
        self.model_name = model
        self.config = config

    def __build_config(self, tools=None, system_instruction=None):
        """Build GenerateContentConfig from self.config."""
        from google.genai import types

        config_kwargs: Dict[str, Any] = {
            "temperature": self.config.temperature,
        }
        if self.config.max_tokens is not None:
            config_kwargs["max_output_tokens"] = self.config.max_tokens
        if self.config.top_p is not None:
            config_kwargs["top_p"] = self.config.top_p
        if self.config.top_k is not None:
            config_kwargs["top_k"] = self.config.top_k
        if self.config.stop_sequences is not None:
            config_kwargs["stop_sequences"] = self.config.stop_sequences
        if self.config.candidate_count is not None:
            config_kwargs["candidate_count"] = self.config.candidate_count
        if self.config.seed is not None:
            config_kwargs["seed"] = self.config.seed
        if self.config.presence_penalty is not None:
            config_kwargs["presence_penalty"] = self.config.presence_penalty
        if self.config.frequency_penalty is not None:
            config_kwargs["frequency_penalty"] = self.config.frequency_penalty
        if self.config.response_mime_type is not None:
            config_kwargs["response_mime_type"] = self.config.response_mime_type
        if self.config.response_schema is not None:
            config_kwargs["response_schema"] = self.config.response_schema
        if self.config.safety_settings is not None:
            config_kwargs["safety_settings"] = self.config.safety_settings
        if self.config.thinking_config is not None:
            config_kwargs["thinking_config"] = self.config.thinking_config
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
        if tools:
            config_kwargs["tools"] = [types.Tool(function_declarations=tools)]

        return types.GenerateContentConfig(**config_kwargs)

    def __call_googleai(self, params: dict[str, Any]):
        from google.genai import errors

        from llmfy.exception.exception_handler import handle_google_error
        from llmfy.llmfy_core.models.google.googleai_usage import track_googleai_usage

        @track_googleai_usage
        def _call_googleai_impl(params: dict[str, Any]):
            try:
                response = self.client.models.generate_content(
                    model=params["model"],
                    contents=params["contents"],
                    config=params["config"],
                )
                return response
            except errors.APIError as e:
                raise handle_google_error(e)
            # Any non-APIError exceptions will naturally propagate up the call stack.

        return _call_googleai_impl(params)

    def __call_stream_googleai(self, params: dict[str, Any]):
        from google.genai import errors

        from llmfy.exception.exception_handler import handle_google_error
        from llmfy.llmfy_core.models.google.googleai_usage import (
            track_googleai_stream_usage,
        )

        @track_googleai_stream_usage
        def _call_stream_googleai_impl(params: dict[str, Any]):
            try:
                return self.client.models.generate_content_stream(
                    model=params["model"],
                    contents=params["contents"],
                    config=params["config"],
                )
            except errors.APIError as e:
                raise handle_google_error(e)
            # Any non-APIError exceptions will naturally propagate up the call stack.

        return _call_stream_googleai_impl(params)

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> AIResponse:
        """
        Generate messages.

        Args:
            messages (List[Dict[str, Any]]): Formatted messages from MessageTemp.get_messages().
            tools (Optional[List[Dict[str, Any]]], optional): Tool function definitions. Defaults to None.

        Returns:
            AIResponse: Response with content or tool_calls.
        """
        try:
            system_instruction = next(
                (
                    msg["parts"][0]["text"]
                    for msg in messages
                    if msg.get("role") == "system"
                ),
                None,
            )
            contents = [msg for msg in messages if msg.get("role") != "system"]

            params = {
                "model": self.model_name,
                "contents": contents,
                "config": self.__build_config(
                    tools=tools, system_instruction=system_instruction
                ),
            }

            response = self.__call_googleai(params)

            request_call_id = str(uuid.uuid4())
            tool_calls = None
            content = None

            if response.candidates:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    function_call_parts = [
                        p
                        for p in candidate.content.parts
                        if p.function_call is not None
                    ]
                    if function_call_parts:
                        tool_calls = [
                            ToolCall(
                                request_call_id=request_call_id,
                                tool_call_id=fc.id if fc.id else str(uuid.uuid4()),
                                name=fc.name or "",
                                arguments=dict(fc.args) if fc.args else {},
                            )
                            for part in function_call_parts
                            for fc in [part.function_call]
                            if fc is not None
                        ]
                    else:
                        content = response.text

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
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Any:
        """
        Generate messages with streaming.

        Note:
            Google AI delivers complete function_call objects in a single chunk
            (no incremental argument accumulation needed, unlike OpenAI).

        Args:
            messages (List[Dict[str, Any]]): Formatted messages from MessageTemp.get_messages().
            tools (Optional[List[Dict[str, Any]]], optional): Tool function definitions. Defaults to None.

        Returns:
            Generator[AIResponse]: Yields AIResponse chunks.
        """
        try:
            system_instruction = next(
                (
                    msg["parts"][0]["text"]
                    for msg in messages
                    if msg.get("role") == "system"
                ),
                None,
            )
            contents = [msg for msg in messages if msg.get("role") != "system"]

            params = {
                "model": self.model_name,
                "contents": contents,
                "config": self.__build_config(
                    tools=tools, system_instruction=system_instruction
                ),
            }

            stream = self.__call_stream_googleai(params)
            request_call_id = str(uuid.uuid4())

            for chunk in stream:
                content = None
                tool_calls = None

                if chunk.candidates:
                    for candidate in chunk.candidates:
                        if candidate.content and candidate.content.parts:
                            for part in candidate.content.parts:
                                if part.text is not None:
                                    content = part.text

                                if part.function_call is not None:
                                    fc = part.function_call
                                    fc_id = fc.id if fc.id else str(uuid.uuid4())
                                    # Google delivers complete function calls in one chunk
                                    tool_calls = [
                                        ToolCall(
                                            request_call_id=request_call_id,
                                            tool_call_id=fc_id,
                                            name=fc.name or "",
                                            arguments=dict(fc.args) if fc.args else {},
                                        )
                                    ]

                yield AIResponse(
                    content=content,
                    tool_calls=tool_calls if tool_calls else None,
                )

        except Exception as e:
            if isinstance(e, LLMfyException):
                raise  # Already handled, re-raise as-is
            raise LLMfyException(str(e), raw_error=e)
