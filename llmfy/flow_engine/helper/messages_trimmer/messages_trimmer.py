from typing import Callable, List, Literal, Optional, Tuple, Union

from llmfy.llmfy_core.messages.message import Message


def count_tokens_approximately(messages: List[Message]) -> int:
    """
    Approximate token counter for messages.
    Rough estimate: 1 token ≈ 4 characters for English text.

    Args:
        messages: List of Message objects

    Returns:
        Approximate token count
    """
    total_chars = 0
    for msg in messages:
        # Get content
        content = getattr(msg, "content", None)
        if content:
            if isinstance(content, list):
                # Handle List[Content] case
                for item in content:
                    total_chars += len(str(item))
            else:
                total_chars += len(str(content))

        # Count tool calls
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            total_chars += len(str(tool_calls))

        # Count tool results
        tool_results = getattr(msg, "tool_results", None)
        if tool_results:
            total_chars += len(str(tool_results))

    # Approximate: 1 token ≈ 4 characters
    return total_chars // 4


def get_message_role(msg: Message) -> str:
    """
    Extract role from Message object.

    Args:
        msg: Message object

    Returns:
        Role string (user, assistant, tool, system, etc.)
    """
    role = getattr(msg, "role", "")
    # Handle enum or string role
    if hasattr(role, "value"):
        return role.value.lower()  # type: ignore
    return str(role).lower()


def trim_messages(
    messages: List[Message],
    strategy: Literal["first", "last"] = "last",
    token_counter: Optional[Callable[[List[Message]], int]] = None,
    max_tokens: Optional[int] = None,
    start_on: Optional[Union[str, Tuple[str, ...]]] = None,
    end_on: Optional[Union[str, Tuple[str, ...]]] = None,
    include_system: bool = True,
) -> List[Message]:
    """
    Trim messages based on token count and role constraints, similar to LangGraph's trim_messages.

    Args:
        messages: List of Message objects to trim
        strategy: "first" to keep earliest messages, "last" to keep latest messages
        token_counter: Function to count tokens in messages. If None, uses count_tokens_approximately
        max_tokens: Maximum number of tokens to keep. If None, no token limit is applied
        start_on: Role(s) that the trimmed messages must start with. Can be a string or tuple of strings
        end_on: Role(s) that the trimmed messages must end with. Can be a string or tuple of strings
        include_system: Whether to always include system messages regardless of token limit

    Returns:
        Trimmed list of Message objects

    Examples:
        >>> messages = [Message(...), Message(...)]
        >>> trimmed = trim_messages(
        ...     messages,
        ...     strategy="last",
        ...     max_tokens=128,
        ...     start_on="user",
        ...     end_on=("user", "tool")
        ... )
    """
    if not messages:
        return []

    # Use default token counter if none provided
    if token_counter is None:
        token_counter = count_tokens_approximately

    # Separate system messages if include_system is True
    system_messages = []
    non_system_messages = []

    for msg in messages:
        role = get_message_role(msg)
        if include_system and role == "system":
            system_messages.append(msg)
        else:
            non_system_messages.append(msg)

    # If no max_tokens, just apply role constraints
    if max_tokens is None:
        working_messages = non_system_messages
    else:
        # Apply token limit based on strategy
        if strategy == "last":
            working_messages = _trim_from_end(
                non_system_messages, token_counter, max_tokens
            )
        else:  # strategy == "first"
            working_messages = _trim_from_start(
                non_system_messages, token_counter, max_tokens
            )

    # Apply start_on constraint
    if start_on is not None:
        working_messages = _apply_start_constraint(working_messages, start_on)

    # Apply end_on constraint
    if end_on is not None:
        working_messages = _apply_end_constraint(working_messages, end_on)

    # Combine system messages with working messages
    return system_messages + working_messages


def _trim_from_end(
    messages: List[Message],
    token_counter: Callable,
    max_tokens: int,
) -> List[Message]:
    """
    Keep the most recent messages that fit within max_tokens.
    """
    if not messages:
        return []

    result = []
    for msg in reversed(messages):
        temp = [msg] + result
        if token_counter(temp) <= max_tokens:
            result = temp
        else:
            break

    return result


def _trim_from_start(
    messages: List[Message],
    token_counter: Callable,
    max_tokens: int,
) -> List[Message]:
    """
    Keep the earliest messages that fit within max_tokens.
    """
    if not messages:
        return []

    result = []
    for msg in messages:
        temp = result + [msg]
        if token_counter(temp) <= max_tokens:
            result = temp
        else:
            break

    return result


def _apply_start_constraint(
    messages: List[Message],
    start_on: Union[str, Tuple[str, ...]],
) -> List[Message]:
    """
    Ensure messages start with one of the specified roles.
    """
    if not messages:
        return []

    allowed_roles = (start_on,) if isinstance(start_on, str) else start_on
    # Normalize allowed roles to lowercase
    allowed_roles = tuple(r.lower() for r in allowed_roles)

    # Find first message with allowed role
    for i, msg in enumerate(messages):
        role = get_message_role(msg)
        if role in allowed_roles:
            return messages[i:]

    # If no message found with allowed role, return empty list
    return []


def _apply_end_constraint(
    messages: List[Message], end_on: Union[str, Tuple[str, ...]]
) -> List[Message]:
    """
    Ensure messages end with one of the specified roles.
    """
    if not messages:
        return []

    allowed_roles = (end_on,) if isinstance(end_on, str) else end_on
    # Normalize allowed roles to lowercase
    allowed_roles = tuple(r.lower() for r in allowed_roles)

    # Find last message with allowed role
    for i in range(len(messages) - 1, -1, -1):
        role = get_message_role(messages[i])
        if role in allowed_roles:
            return messages[: i + 1]

    # If no message found with allowed role, return empty list
    return []
