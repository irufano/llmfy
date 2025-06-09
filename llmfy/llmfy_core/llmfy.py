import string
from typing import Any, Callable, Dict, List, Optional
import uuid

from llmfy.llmfy_core.messages.content import Content
from llmfy.llmfy_core.messages.message import Message
from llmfy.llmfy_core.messages.message_temp import MessageTemp
from llmfy.llmfy_core.messages.role import Role
from llmfy.llmfy_core.models.base_ai_model import BaseAIModel
from llmfy.llmfy_core.responses.ai_response import AIResponse
from llmfy.llmfy_core.responses.generation_response import GenerationResponse
from llmfy.llmfy_core.tools.tool import Tool
from llmfy.exception.llmfy_exception import LLMfyException


class LLMfy:
    def __init__(
        self,
        llm: BaseAIModel,
        system_message: Optional[str] = None,
        input_variables: Optional[List[str]] = None,
    ):
        self.model: BaseAIModel = llm
        self.messages_temp: MessageTemp = MessageTemp()
        self.system_message = system_message
        self.input_variables = input_variables or []
        self._tools: Dict[str, Callable] = {}
        self._tool_definitions: Dict[str, Dict[str, Any]] = {}

        def _has_variable_placeholder(s):
            return bool(
                list(string.Formatter().parse(s))
                and any(
                    field for _, field, _, _ in string.Formatter().parse(s) if field
                )
            )

        def _extract_variable_names(s):
            return list(
                set([field for _, field, _, _ in string.Formatter().parse(s) if field])
            )

        # Validate that if system message has variable then input variable should not be empty
        if (
            _has_variable_placeholder(self.system_message)
            if self.system_message
            else False
        ) and not self.input_variables:
            variable_names = _extract_variable_names(self.system_message)
            raise LLMfyException(
                f"System messages have placeholder variables, so the `input variable` should not be empty. "
                f"Missing input variables: {variable_names}. "
            )

        # Validate input variables
        if self.system_message and self.input_variables:
            # Validate that all required input variables are in kwargs
            variable_names = _extract_variable_names(self.system_message)
            missing_vars = [
                var for var in variable_names if var not in self.input_variables
            ]
            if missing_vars:
                raise LLMfyException(
                    f"Missing required input variables: {missing_vars}. "
                    f"Expected variables: {variable_names}."
                )

    def register_tool(self, funcs: List[Callable]) -> None:
        """Register a tool with this framework instance."""
        for func in funcs:
            if not hasattr(func, "_is_tool"):
                raise LLMfyException("Function must be decorated with @Tool")

            tool_def = Tool._get_tool_definition(func, self.model.provider)
            self._tools[func.__name__] = func
            self._tool_definitions[func.__name__] = tool_def

    def __get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all tool definitions registered with this framework."""
        return list(self._tool_definitions.values())

    def __execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a registered tool."""
        if name not in self._tools:
            raise LLMfyException(f"Tool not found: {name}")
        return self._tools[name](**arguments)

    def __validate_system_message(self, **kwargs) -> str | None:
        # If we have a system message and input variables
        try:
            final_system_message = self.system_message if self.system_message else ""
            if self.system_message and self.input_variables:
                # Validate that all required input variables are in kwargs
                missing_vars = [
                    var for var in self.input_variables if var not in kwargs
                ]
                if missing_vars:
                    raise LLMfyException(
                        f"Missing required input variables: {missing_vars}. "
                        f"Expected variables: {self.input_variables}, "
                        f"Received variables: {list(kwargs.keys())}"
                    )

                # Create a dictionary of variables from kwargs that match input_variables
                format_variables = {
                    var: kwargs.get(var)
                    for var in self.input_variables
                    if var in kwargs
                }

                # Update the system message with the variables
                final_system_message = self.system_message.format(**format_variables)

            return final_system_message
        except KeyError as e:
            raise LLMfyException(f"Required variable {e} not found in kwargs")
        except Exception as e:
            raise LLMfyException(f"Error formatting system message: {str(e)}")

    def invoke(self, contents: str | List[Content], **kwargs) -> GenerationResponse:
        """
        Generate a response based on contents.

        Args:
            contents (str | List[Content]): Text or List of content objects to process
            **kwargs: Additional generation parameters

        Returns:
            GenerationResponse containing the generated response
        """
        try:
            self.messages_temp.clear()

            # Generate using user role only if invoke
            messages = [Message(role=Role.USER, content=contents)]

            if self.system_message:
                # Validate system message
                final_system_message = self.__validate_system_message(**kwargs)

                # Add system message to history
                self.messages_temp.add_system_message(
                    final_system_message if final_system_message else ""
                )

            # Add new messages to history
            for message in messages:
                # always ROLE == USER because invoke
                if message.role == Role.USER:
                    self.messages_temp.add_user_message(
                        message.id,
                        message.content if message.content else "",
                    )

            response = self.model.generate(
                self.messages_temp.get_messages(provider=self.model.provider),
                tools=self.__get_tool_definitions(),
            )

            self.messages_temp.add_assistant_message(
                id=str(uuid.uuid4()),
                content=response.content,
                tool_calls=response.tool_calls,
            )

            return GenerationResponse(
                result=response,
                messages=self.messages_temp.get_instance_messages(),
            )
        except Exception as e:
            raise LLMfyException(e)

    def invoke_with_tools(
        self,
        contents: str | List[Content],
        **kwargs,
    ) -> GenerationResponse:
        """
        Generate a response based on contents with tools results.

        Args:
            contents (str | List[Content]): Text or List of content objects to process
            **kwargs: Additional generation parameters

        Returns:
            GenerationResponse containing the generated response
        """
        try:
            self.messages_temp.clear()

            # Generate using user role only if invoke
            messages = [Message(role=Role.USER, content=contents)]

            if self.system_message:
                # Validate system message
                final_system_message = self.__validate_system_message(**kwargs)

                # Add system message to history
                self.messages_temp.add_system_message(
                    final_system_message if final_system_message else ""
                )

            # Add new messages to history
            for message in messages:
                # always ROLE == USER because invoke
                if message.role == Role.USER:
                    self.messages_temp.add_user_message(
                        message.id,
                        message.content if message.content else "",
                    )

            while True:
                response = self.model.generate(
                    self.messages_temp.get_messages(provider=self.model.provider),
                    tools=self.__get_tool_definitions(),
                )

                if response.tool_calls:
                    self.messages_temp.add_assistant_message(
                        id=str(uuid.uuid4()),
                        tool_calls=response.tool_calls,
                    )

                    for tool_call in response.tool_calls:
                        result = self.__execute_tool(
                            tool_call.name, tool_call.arguments
                        )
                        self.messages_temp.add_tool_message(
                            id=str(uuid.uuid4()),
                            request_call_id=tool_call.request_call_id,
                            tool_call_id=tool_call.tool_call_id,
                            name=tool_call.name,
                            result=str(result),
                            provider=self.model.provider,
                        )
                    continue

                self.messages_temp.add_assistant_message(
                    id=str(uuid.uuid4()),
                    content=response.content,
                    tool_calls=response.tool_calls,
                )

                return GenerationResponse(
                    result=response,
                    messages=self.messages_temp.get_instance_messages(),
                )
        except Exception as e:
            raise LLMfyException(e)

    def chat(self, messages: List[Message], **kwargs) -> GenerationResponse:
        """
        Generate a response based on a list of messages.

        Args:
            messages (List[Message]): List of Message objects to process
            **kwargs: Additional generation parameters

        Returns:
            GenerationResponse containing the generated response
        """
        try:
            self.messages_temp.clear()

            if self.system_message:
                # Validate system message
                final_system_message = self.__validate_system_message(**kwargs)

                # Add system message to history
                self.messages_temp.add_system_message(
                    final_system_message if final_system_message else ""
                )

            # Add new messages to history
            for message in messages:
                if message.role == Role.USER:
                    self.messages_temp.add_user_message(
                        message.id,
                        message.content if message.content else "",
                    )
                elif message.role == Role.ASSISTANT:
                    self.messages_temp.add_assistant_message(
                        id=message.id,
                        content=message.content,
                        tool_calls=message.tool_calls,
                    )
                elif message.role == Role.TOOL:
                    self.messages_temp.add_tool_message(
                        id=message.id,
                        request_call_id=message.request_call_id,
                        tool_call_id=(
                            message.tool_call_id if message.tool_call_id else ""
                        ),
                        name=message.name if message.name else "",
                        result=message.tool_results[0] if message.tool_results else "",
                        provider=self.model.provider,
                    )

            response = self.model.generate(
                self.messages_temp.get_messages(provider=self.model.provider),
                tools=self.__get_tool_definitions(),
            )

            self.messages_temp.add_assistant_message(
                id=str(uuid.uuid4()),
                content=response.content,
                tool_calls=response.tool_calls,
            )

            return GenerationResponse(
                result=response,
                messages=self.messages_temp.get_instance_messages(),
            )
        except Exception as e:
            raise LLMfyException(e)

    def chat_with_tools(self, messages: List[Message], **kwargs) -> GenerationResponse:
        """
        Generate a response based on a list of messages with tools results.

        Args:
            messages (List[Message]): List of Message objects to process
            **kwargs: Additional generation parameters

        Returns:
            GenerationResponse containing the generated response
        """
        try:
            self.messages_temp.clear()

            if self.system_message:
                # Validate system message
                final_system_message = self.__validate_system_message(**kwargs)

                # Add system message to history
                self.messages_temp.add_system_message(
                    final_system_message if final_system_message else ""
                )

            # Add new messages to history
            for message in messages:
                if message.role == Role.USER:
                    self.messages_temp.add_user_message(
                        message.id,
                        message.content if message.content else "",
                    )
                elif message.role == Role.ASSISTANT:
                    self.messages_temp.add_assistant_message(
                        id=message.id,
                        content=message.content,
                        tool_calls=message.tool_calls,
                    )
                elif message.role == Role.TOOL:
                    self.messages_temp.add_tool_message(
                        id=message.id,
                        request_call_id=message.request_call_id,
                        tool_call_id=(
                            message.tool_call_id if message.tool_call_id else ""
                        ),
                        name=message.name if message.name else "",
                        result=message.tool_results[0] if message.tool_results else "",
                        provider=self.model.provider,
                    )

            while True:
                response = self.model.generate(
                    self.messages_temp.get_messages(provider=self.model.provider),
                    tools=self.__get_tool_definitions(),
                )

                if response.tool_calls:
                    self.messages_temp.add_assistant_message(
                        id=str(uuid.uuid4()),
                        tool_calls=response.tool_calls,
                    )

                    for tool_call in response.tool_calls:
                        result = self.__execute_tool(
                            tool_call.name, tool_call.arguments
                        )
                        self.messages_temp.add_tool_message(
                            id=str(uuid.uuid4()),
                            request_call_id=tool_call.request_call_id,
                            tool_call_id=tool_call.tool_call_id,
                            name=tool_call.name,
                            result=str(result),
                            provider=self.model.provider,
                        )
                    continue

                self.messages_temp.add_assistant_message(
                    id=str(uuid.uuid4()),
                    content=response.content,
                    tool_calls=response.tool_calls,
                )

                return GenerationResponse(
                    result=response,
                    messages=self.messages_temp.get_instance_messages(),
                )
        except Exception as e:
            raise LLMfyException(e)

    def chat_stream(self, messages: List[Message], **kwargs) -> Any:
        """
        Generate a streaming response based on a list of messages.

        Args:
            messages (List[Message]): List of Message objects to process
            **kwargs: Additional generation parameters

        Returns:
            Streaming response from the model
        """
        try:
            self.messages_temp.clear()

            if self.system_message:
                # Validate system message
                final_system_message = self.__validate_system_message(**kwargs)

                # Add system message to history
                self.messages_temp.add_system_message(
                    final_system_message if final_system_message else ""
                )

            # Add new messages to history
            for message in messages:
                if message.role == Role.USER:
                    self.messages_temp.add_user_message(
                        message.id,
                        message.content if message.content else "",
                    )
                elif message.role == Role.ASSISTANT:
                    self.messages_temp.add_assistant_message(
                        id=message.id,
                        content=message.content,
                        tool_calls=message.tool_calls,
                    )
                elif message.role == Role.TOOL:
                    self.messages_temp.add_tool_message(
                        id=message.id,
                        request_call_id=message.request_call_id,
                        tool_call_id=(
                            message.tool_call_id if message.tool_call_id else ""
                        ),
                        name=message.name if message.name else "",
                        result=message.tool_results[0] if message.tool_results else "",
                        provider=self.model.provider,
                    )

            stream = self.model.generate_stream(
                self.messages_temp.get_messages(provider=self.model.provider),
                tools=self.__get_tool_definitions(),
            )

            full_content = ""
            tool_calls = None

            for chunk in stream:
                if isinstance(chunk, AIResponse):
                    content = ""
                    tool_calls = []
                    # Yield each chunk
                    if chunk.content:
                        content = chunk.content
                        full_content += content

                    if chunk.tool_calls:
                        tool_calls = chunk.tool_calls

                    # update content and toolcalls only
                    yield GenerationResponse(
                        result=AIResponse(content=content, tool_calls=tool_calls),
                        messages=[],
                    )

            self.messages_temp.add_assistant_message(
                id=str(uuid.uuid4()),
                content=full_content,
                tool_calls=tool_calls,
            )

            # update messages only
            yield GenerationResponse(
                result=AIResponse(),
                messages=self.messages_temp.get_instance_messages(),
            )
        except Exception as e:
            raise LLMfyException(e)

    def clear_messages_temp(self) -> None:
        self.messages_temp.clear()
