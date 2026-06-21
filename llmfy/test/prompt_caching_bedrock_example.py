from dotenv import load_dotenv

from llmfy import (
    BedrockConfig,
    BedrockModel,
    LLMfy,
    LLMfyException,
    llmfy_usage_tracker,
)

load_dotenv()

# ─── Shared large context ────────────────────────────────────────────────────
# Simulate a large document that would be expensive to process on every call.
# In production this would be a real document loaded from disk or a database.
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
  AWS Bedrock  — Claude 3.x / 4.x / 4.5 / 4.6 / 4.8 / Fable 5, Amazon Nova, Llama, DeepSeek
  OpenAI       — GPT-4o, GPT-4.1, GPT-5, o-series reasoning models
  Google AI    — Gemini 2.5 and 3.x families

Installation:
  pip install llmfy[boto3]        # AWS Bedrock
  pip install llmfy[openai]       # OpenAI
  pip install llmfy[google-genai] # Google AI

Environment variables required for Bedrock:
  AWS_ACCESS_KEY_ID
  AWS_SECRET_ACCESS_KEY
  AWS_BEDROCK_REGION

Prompt caching on Bedrock:
  Set enable_prompt_caching=True on BedrockConfig to inject cachePoint markers
  automatically. The system prompt and conversation prefix are cached so that
  repeated calls with the same context pay ~10 percent of the normal input price
  for the cached portion.
  Use prompt_caching_ttl="1h" on Claude 4.5, 4.6, 4.8, and Fable 5 for a longer
  cache lifetime suited to batch processing workflows.

  Supported models for caching:
    anthropic.claude-3-5-sonnet-20241022-v2:0  (min 1 024 tokens, 5m TTL)
    anthropic.claude-3-7-sonnet-20250219-v1:0  (min 1 024 tokens, 5m TTL)
    anthropic.claude-opus-4-20250514-v1:0      (min 1 024 tokens, 5m TTL)
    anthropic.claude-sonnet-4-5-20250929-v1:0  (min 4 096 tokens, 5m/1h TTL)
    anthropic.claude-sonnet-4-6                (min 1 024 tokens, 5m/1h TTL)
    anthropic.claude-fable-5                   (min 1 024 tokens, 5m/1h TTL)
""" * 3  # repeat to push past the 1 024-token minimum threshold


def prompt_caching_bedrock_example():
    """Demonstrate prompt caching with Claude Sonnet 4 on AWS Bedrock.

    First call:  writes the system prompt to the cache (cache_write_tokens).
    Second call: reads the system prompt from the cache (cache_read_tokens).

    Both cache_read_tokens and cache_write_tokens appear in the usage tracker
    output under the Cache section and per-request details.
    """

    config = BedrockConfig(
        temperature=0.7,
        enable_prompt_caching=True,
        # prompt_caching_ttl="1h",  # uncomment for 1-hour cache (Claude 4.5+ only)
    )

    llm = BedrockModel(
        model="us.anthropic.claude-sonnet-4-20250514-v1:0",
        config=config,
    )

    agent = LLMfy(
        llm,
        system_message=LARGE_CONTEXT,
    )

    questions = [
        "What providers does LLMfy support?",
        "How do I install LLMfy for AWS Bedrock?",
        "What environment variables are required for Bedrock?",
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

    except LLMfyException as e:
        print(f"Error: {e}")


prompt_caching_bedrock_example()
