# Thinking / Reasoning Example

Demonstrates reading `response.result.thinking` — the model's reasoning trace — across all 5 backends: Anthropic Messages, AWS Bedrock (Claude), OpenAI Chat Completions, OpenAI Responses, and Google AI (Gemini). See [Thinking Config](../documentation/features/thinking-config.md) for the full per-provider config reference this example follows.

!!! warning "OpenAI Chat Completions never returns thinking text for real OpenAI models"
    Unlike the other four backends, OpenAI's own Chat Completions API only lets `reasoning_effort` control how much the model reasons — it never returns the reasoning trace itself, only a `reasoning_tokens` count in usage. `response.result.thinking` only gets populated on this backend when pointed at an OpenAI-*compatible* endpoint that fabricates a non-standard `reasoning`/`reasoning_content` field (e.g. Ollama, DeepSeek — see the [Ollama example](example-ollama.md)).

!!! note "OpenAI Responses needs `reasoning.summary` set"
    The Responses API never returns the raw chain of thought — only a model-generated summary, and only when `OpenAIResponsesReasoningConfig.summary` is explicitly set (`'auto'`, `'concise'`, or `'detailed'`).

```python linenums="1"
from dotenv import load_dotenv

from llmfy import (
    AnthropicMessagesConfig,
    AnthropicMessagesModel,
    AnthropicMessagesThinkingConfig,
    BedrockConverseConfig,
    BedrockConverseModel,
    BedrockConverseThinkingConfig,
    GenerationResponse,
    GoogleAIGenerateConfig,
    GoogleAIGenerateModel,
    GoogleAIGenerateThinkingConfig,
    LLMfy,
    LLMfyException,
    OpenAIChatConfig,
    OpenAIChatModel,
    OpenAIChatThinkingConfig,
    OpenAIResponsesConfig,
    OpenAIResponsesModel,
    OpenAIResponsesReasoningConfig,
)

load_dotenv()

# ─── Thinking / reasoning across all 5 backends (streaming) ─────────────────
# `AIResponse.thinking` carries the model's reasoning trace when the provider
# returns one and the request asked for it via each provider's `thinking`/
# `reasoning` config. See docs/documentation/features/thinking-config.md for
# the full per-provider config reference this example follows.


def _stream_and_print(agent: LLMfy, prompt: str, label: str, note_if_no_thinking: str = ""):
    """Shared streaming loop: prints [thinking] chunks as they arrive, then
    switches to the regular content once thinking ends."""

    print(f"\n{label}")
    try:
        stream = agent.invoke_stream(prompt)
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
                        is_thinking = False
                    content = chunk.result.content
                    full_content += content
                    print(content, end="", flush=True)

        print("\n--- full ---")
        if full_thinking:
            print(f"[thinking]\n{full_thinking}\n[/thinking]\n")
        elif note_if_no_thinking:
            print(note_if_no_thinking)
        print(full_content)
    except LLMfyException as e:
        print(f"Error: {e}")
    print("---")


def anthropic_thinking_example():
    """Anthropic Messages API — Claude extended thinking."""

    config = AnthropicMessagesConfig(
        max_tokens=8192,
        thinking=AnthropicMessagesThinkingConfig(
            enabled=True,
            budget_tokens=4000,
        ),
    )
    llm = AnthropicMessagesModel(model="claude-sonnet-4-5-20250929", config=config)

    agent = LLMfy(llm, system_message="You are a helpful assistant.")
    _stream_and_print(
        agent,
        "Explain the halting problem step by step.",
        "[Anthropic Messages - thinking stream]",
    )


def bedrock_thinking_example():
    """AWS Bedrock (Amazon Nova 2 Lite) — reasoning via the reasoningConfig
    API format (Mode 3). Uses a named effort level instead of a token budget
    — the only Nova model this codebase documents as supporting thinking.
    """

    config = BedrockConverseConfig(
        thinking=BedrockConverseThinkingConfig(
            enabled=True,
            reasoning_effort="medium",
        ),
    )
    llm = BedrockConverseModel(
        model="us.amazon.nova-2-lite-v1:0",
        config=config,
    )

    agent = LLMfy(llm, system_message="You are a helpful assistant.")
    _stream_and_print(
        agent,
        "Explain the halting problem step by step.",
        "[Bedrock Converse - thinking stream]",
    )


def openai_chat_thinking_example():
    """OpenAI Chat Completions — o-series reasoning.

    Note: unlike the other four backends, real OpenAI never returns the
    reasoning trace as text on this API — `reasoning_effort` only controls
    depth, and the model only reports back a `reasoning_tokens` count. So
    `response.result.thinking` stays empty here against real OpenAI; it's
    only populated when this same code points at an OpenAI-compatible
    endpoint that fabricates a `reasoning`/`reasoning_content` field (e.g.
    Ollama, DeepSeek — see example-ollama.md).
    """

    config = OpenAIChatConfig(
        thinking=OpenAIChatThinkingConfig(
            enabled=True,
            effort="high",
        ),
        # o-series reasoning models only accept the default temperature/top_p
        # (1) — a 400 unsupported_value otherwise, so omit both entirely.
        temperature=None,
        top_p=None,
    )
    llm = OpenAIChatModel(model="o4-mini", config=config)

    agent = LLMfy(llm, system_message="You are a helpful assistant.")
    _stream_and_print(
        agent,
        "What is the time complexity of Dijkstra's algorithm?",
        "[OpenAI Chat Completions - thinking stream]",
        note_if_no_thinking="[thinking] not returned by this API — see docstring above",
    )


def openai_responses_thinking_example():
    """OpenAI Responses API — reasoning with a natural-language summary.

    Requires `reasoning.summary` to be set — the raw chain of thought is
    never returned, only this model-generated summary.
    """

    config = OpenAIResponsesConfig(
        reasoning=OpenAIResponsesReasoningConfig(
            enabled=True,
            effort="high",
            summary="detailed",
        ),
        # gpt-5.6-terra rejects temperature/top_p outright (400
        # unsupported_parameter) rather than accepting a default — None omits
        # the field from the request entirely.
        temperature=None,
        top_p=None,
    )
    llm = OpenAIResponsesModel(model="gpt-5.6-terra", config=config)

    agent = LLMfy(llm, system_message="You are a helpful assistant.")
    _stream_and_print(
        agent,
        "What is the time complexity of Dijkstra's algorithm?",
        "[OpenAI Responses - thinking stream]",
    )


def google_thinking_example():
    """Google AI (Gemini) — thinking with thought summaries included.

    gemini-2.5-flash (unlike gemini-2.5-pro) is available on Google AI
    Studio's free tier and still fully supports thinking — see
    https://ai.google.dev/gemini-api/docs/pricing.
    """

    config = GoogleAIGenerateConfig(
        thinking=GoogleAIGenerateThinkingConfig(
            enabled=True,
            budget_tokens=2048,
            include_thoughts=True,
        ),
    )
    llm = GoogleAIGenerateModel(model="gemini-2.5-flash", config=config)

    agent = LLMfy(llm, system_message="You are a helpful assistant.")
    _stream_and_print(
        agent,
        "Explain how transformers work in deep learning.",
        "[Google AI Generate - thinking stream]",
    )


if __name__ == "__main__":
    anthropic_thinking_example()
    bedrock_thinking_example()
    openai_chat_thinking_example()
    openai_responses_thinking_example()
    google_thinking_example()
```
