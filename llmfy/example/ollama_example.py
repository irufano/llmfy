import os

from llmfy import (
    GenerationResponse,
    LLMfy,
    LLMfyException,
    Message,
    OpenAIChatConfig,
    OpenAIChatModel,
    Role,
    Tool,
)

# ─── Ollama (local) ──────────────────────────────────────────────────────────
# Ollama exposes an OpenAI-compatible Chat Completions API at
# http://localhost:11434/v1, so no llmfy code changes are needed — just point
# OpenAIChatModel's `base_url` at it. Ollama doesn't check the API key, but
# the `openai` SDK requires a non-empty string, so any placeholder works.
#
# Setup:
#   1. Install & run Ollama: https://ollama.com
#   2. Pull the model:  ollama pull gemma4:e4b
#   3. Check the exact tag you have locally:  ollama list
#      (adjust OLLAMA_MODEL below if your local tag differs — e.g. plain
#      "gemma3n" or a different size like "gemma3n:e2b")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
# OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:9b")


def ollama_chat_example():
    """Single-turn invoke against a local Ollama model."""

    llm = OpenAIChatModel(
        model=OLLAMA_MODEL,
        config=OpenAIChatConfig(temperature=0.7),
        api_key="ollama",  # unused by Ollama, but required by the openai SDK client
        base_url=OLLAMA_BASE_URL,
    )

    agent = LLMfy(llm, system_message="You are a helpful assistant.")

    try:
        response = agent.invoke("Jelaskan quantum computing dalam 1 kalimat pendek.")
        print("\n[Ollama Chat Completions]")
        print(f">> {response.result.content}")
    except LLMfyException as e:
        print(f"Error: {e}")
        print(
            "Hint: make sure `ollama serve` is running and the model has been "
            f"pulled (`ollama pull {OLLAMA_MODEL}`)."
        )
    print("---")


def ollama_chat_history_example():
    """Multi-turn conversation using explicit Message history."""

    llm = OpenAIChatModel(
        model=OLLAMA_MODEL,
        config=OpenAIChatConfig(temperature=0.7),
        api_key="ollama",
        base_url=OLLAMA_BASE_URL,
    )

    agent = LLMfy(llm, system_message="You are a helpful assistant.")

    try:
        messages = [Message(role=Role.USER, content="Siapa presiden pertama Indonesia?")]
        response = agent.chat(messages)
        print("\n[Ollama Chat with history]")
        if response.result.thinking:
            print(f"[thinking] {response.result.thinking}")
        print("\n\nResponse:\n")
        print(f">> {response.result.content}")
    except LLMfyException as e:
        print(f"Error: {e}")
    print("---")


def ollama_chat_stream_example():
    """Streaming response from a local Ollama model."""

    llm = OpenAIChatModel(
        model=OLLAMA_MODEL,
        config=OpenAIChatConfig(temperature=0.7),
        api_key="ollama",
        base_url=OLLAMA_BASE_URL,
    )

    agent = LLMfy(llm, system_message="You are a helpful assistant.")

    try:
        print("\n[Ollama Chat Completions - streaming]")
        stream = agent.invoke_stream("Ceritakan singkat tentang kota Bandung.")
        full_content = ""
        full_thinking = ""
        is_thinking = False
        for chunk in stream:
            if isinstance(chunk, GenerationResponse):
                if chunk.result.thinking:
                    if not is_thinking:
                        print("[thinking] ", end="", flush=True)
                        is_thinking = True
                    thinking = chunk.result.thinking
                    full_thinking += thinking
                    print(thinking, end="", flush=True)
                if chunk.result.content:
                    if is_thinking:
                        print("\n[/thinking]\n", end="", flush=True)
                        print("\nResponse:\n")
                        is_thinking = False
                    content = chunk.result.content
                    full_content += content
                    print(content, end="", flush=True)
        print("\n--- full ---")
        if full_thinking:
            print(f"[thinking]\n{full_thinking}\n[/thinking]\n")
        print(full_content)
    except LLMfyException as e:
        print(f"Error: {e}")
    print("---")


def ollama_tool_calling_example():
    """Tool calling against a local Ollama model.

    Not every Ollama model supports tool calling — check the model's page on
    ollama.com for a "Tools" capability badge before relying on this (e.g.
    qwen3.5, gpt-oss, llama3.1/3.3, mistral support it; gemma3n generally
    does not).
    """

    llm = OpenAIChatModel(
        model=OLLAMA_MODEL,
        config=OpenAIChatConfig(temperature=0.7),
        api_key="ollama",
        base_url=OLLAMA_BASE_URL,
    )

    agent = LLMfy(llm, system_message="You are a helpful assistant.")

    @Tool()
    def get_current_weather(location: str, unit: str = "celsius") -> str:
        """Get the current weather for a location.

        Args:
            location (str): City name.
            unit (str, optional): Temperature unit, "celsius" or "fahrenheit".

        Returns:
            str: Weather description.
        """
        print(f"[tool] call get_current_weather, location={location}, unit={unit}" )
        return f"The weather in {location} is 22 degrees {unit}"

    @Tool()
    def get_current_time(location: str) -> str:
        """Get the current local time for a location.

        Args:
            location (str): City name.

        Returns:
            str: Current time.
        """
        print(f"[tool] call get_current_time, location={location}")
        return f"The time in {location} is 09:00 AM"

    agent.register_tool([get_current_weather, get_current_time])

    try:
        messages = [
            Message(role=Role.USER, content="What time and weather in London?")
        ]
        response = agent.chat_with_tools(messages)
        print("\n[Ollama Tool Calling]")
        print(f">> {response.result.content}")
    except LLMfyException as e:
        print(f"Error: {e}")
        print(
            "Hint: make sure the model supports tool calling — check its "
            "'Tools' capability badge on ollama.com."
        )
    print("---")


if __name__ == "__main__":
    # ollama_chat_example()
    # ollama_chat_history_example()
    # ollama_chat_stream_example()
    ollama_tool_calling_example()
