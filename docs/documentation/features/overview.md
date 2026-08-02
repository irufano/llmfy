# Overview

LLMfy provides a unified interface for building LLM-powered applications across multiple providers — [Anthropic](providers.md#anthropic-messages-api), [OpenAI](providers.md#openai-chat-completions) (Chat Completions and Responses API), [AWS Bedrock](providers.md#aws-bedrock), and [Google AI](providers.md#google-ai) — plus a workflow orchestration engine, vector store, and guardrails.

This guide covers the core building blocks:

- **[Framework](framework.md)** — the `LLMfy` class: initializing an agent, system messages, and template variables.
- **[Providers](providers.md)** — installation, environment variables, and configuration for each supported provider.
- **LLM**
    - **[Generation](generate.md)** — the six generation methods (`invoke`, `chat`, streaming, tool-calling variants).
    - **[Content Types](content.md)** — text, image, document, and video input.
    - **[Tool Calling](tool-calling.md)** — registering and calling functions from the model.
    - **[Thinking Config](thinking-config.md)** — extended thinking / reasoning mode per provider.
    - **[Prompt Caching](prompt-caching.md)** — reducing cost for repeated context per provider.
- **Embeddings**
    - **[Embeddings](embedding.md)**, **[Chunking](chunk-text.md)**, and **[Vector Store](../vector-store/faiss-vector-store.md)** for retrieval-augmented generation.
- **[Usage Tracking](usage.md)** — token counts and cost tracking across providers.
- **[Exception Handling](../exception/exception-handler.md)** — a unified exception hierarchy across providers.

## Quick example

```python linenums="1"
from llmfy import LLMfy, OpenAIChatModel, OpenAIChatConfig, Message, Role

llm = OpenAIChatModel(model="gpt-4o-mini", config=OpenAIChatConfig(temperature=0.7))
agent = LLMfy(llm, system_message="You are a helpful assistant.")

response = agent.invoke("Hello")
print(f"\n>> {response.result.content}\n")
```

`LLMfy` is provider-agnostic — swap `OpenAIChatModel`/`OpenAIChatConfig` for [`AnthropicMessagesModel`](providers.md#anthropic-messages-api), `BedrockModel`, `OpenAIResponsesModel`, or `GoogleAIModel` (and their matching config classes) without changing anything else. See [Framework](framework.md) and [Providers](providers.md) for a deeper walkthrough.
