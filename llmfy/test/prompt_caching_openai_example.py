from dotenv import load_dotenv

from llmfy import (
    LLMfy,
    LLMfyException,
    OpenAIConfig,
    OpenAIModel,
    llmfy_usage_tracker,
)

load_dotenv()

# ─── Shared large context ────────────────────────────────────────────────────
# OpenAI caches the longest common prompt PREFIX automatically.
# Static content (system prompt, documents) must stay at the beginning.
# No markers or config changes affect the request — caching is fully automatic.
# Minimum 1,024 tokens required for caching to activate.
LARGE_CONTEXT = """
LLMfy is a Python framework for building and integrating LLM-powered applications.
It provides a unified interface across AWS Bedrock, OpenAI, and Google AI so that
switching providers requires only a config change.

Key features:
  - Unified generation API (invoke, chat, stream) across all providers
  - Thinking / reasoning mode for Claude, Nova 2, OpenAI o-series, and Gemini
  - Prompt caching to reduce costs on repeated large-context calls
  - Tool calling with automatic argument parsing
  - Multimodal input: text, images, documents, and video
  - Usage tracking with per-request token counts and cost estimates
  - Flow Engine for building stateful multi-step AI agents
  - Embeddings and FAISS vector store for retrieval-augmented generation
  - PII detection and masking as a guardrail

Providers supported:
  OpenAI   — GPT-4o, GPT-4.1, GPT-5, o-series reasoning models
  Bedrock  — Claude 3.x / 4.x / 4.5 / 4.6 / 4.8 / Fable 5, Amazon Nova, Llama
  Google AI — Gemini 2.5 and 3.x families

Installation:
  pip install llmfy[openai]       # OpenAI
  pip install llmfy[boto3]        # AWS Bedrock
  pip install llmfy[google-genai] # Google AI

Environment variables required for OpenAI:
  OPENAI_API_KEY

Prompt caching on OpenAI:
  Caching is applied automatically by OpenAI on all API requests — no markers
  or code changes are needed. The longest common prompt prefix is cached
  server-side. Requests that reuse the same prefix within the TTL window
  (5–10 minutes inactivity, max 1 hour) pay no additional fees and benefit
  from reduced latency. Setting enable_prompt_caching=True on OpenAIConfig
  is an intent flag that ensures cached token counts appear in usage details.

  Cache TTL:
    Standard models (gpt-4o, gpt-4.1, o-series): 5–10 min inactivity, max 1h
    Extended (gpt-5, gpt-5.5, gpt-4.1):          up to 24 hours

  Supported models (all gpt-4o and newer):
    gpt-4o, gpt-4o-mini           (standard TTL)
    gpt-4.1, gpt-4.1-mini, gpt-4.1-nano  (extended 24h TTL)
    o1, o1-mini, o3, o3-mini, o3-pro, o4-mini
    gpt-5, gpt-5.1, gpt-5.2, gpt-5.4, gpt-5.5, gpt-5.5-pro

  Best practice:
    Place large stable content (system prompt, reference documents) at the
    beginning of the prompt. Dynamic content (user questions, context that
    changes per request) should come after — it does not affect the cached
    prefix and does not break cache hits.
""" * 3  # repeat to push past the 1,024-token minimum threshold


def prompt_caching_openai_example():
    """Demonstrate prompt caching with gpt-4o on OpenAI.

    OpenAI caching is fully automatic — no markers needed.
    enable_prompt_caching=True is an intent flag that ensures cache_read_tokens
    appear in usage details when the prefix is served from cache.

    First call:  prefix written to OpenAI's server-side cache.
    Second call: prefix served from cache (cache_read_tokens > 0).
    """

    config = OpenAIConfig(
        temperature=0.7,
        enable_prompt_caching=True,  # intent flag — caching is always automatic
    )

    llm = OpenAIModel(
        model="gpt-4o",
        config=config,
    )

    agent = LLMfy(
        llm,
        system_message=LARGE_CONTEXT,
    )

    questions = [
        "What providers does LLMfy support?",
        "How do I install LLMfy for OpenAI?",
        "What environment variables are required for OpenAI?",
        "What is the default cache TTL for gpt-4o?",
    ]

    try:
        with llmfy_usage_tracker() as usage:
            for i, question in enumerate(questions, 1):
                print(f"\n── Question {i}: {question}")
                response = agent.invoke(question)
                print(f"   Answer: {response.result.content}")

        print("\n" + "=" * 60)
        print(usage)
        print("=" * 60)

        # Access cache stats programmatically
        data = usage.to_dict()
        cache = data.get("cache", {})
        print("\nCache summary:")
        print(f"  cache_read_tokens : {cache.get('cache_read_tokens', 0)}")
        print(f"  cache_write_tokens: {cache.get('cache_write_tokens', 0)}")
        print()
        print("Note: cache_read_tokens > 0 from the second call onwards")
        print("      when the same system prompt prefix is served from cache.")

    except LLMfyException as e:
        print(f"Error: {e}")


prompt_caching_openai_example()
