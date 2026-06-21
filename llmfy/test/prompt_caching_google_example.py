import os

from dotenv import load_dotenv

from llmfy import (
    GoogleAIConfig,
    GoogleAIModel,
    LLMfy,
    LLMfyException,
    llmfy_usage_tracker,
)

load_dotenv()

# ─── Shared large context ────────────────────────────────────────────────────
# Google AI context caching requires two steps:
#   1. Create a cache externally with client.caches.create() — done below.
#   2. Pass the returned cache name via GoogleAIConfig(cached_content=...).
#
# Minimum 2,048 tokens required for gemini-2.5-flash/pro.
# The cached content must use the EXACT same model as the generation request.
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
  Google AI — Gemini 2.5 and 3.x families
  OpenAI    — GPT-4o, GPT-4.1, GPT-5, o-series reasoning models
  Bedrock   — Claude 3.x / 4.x / 4.5 / 4.6 / 4.8 / Fable 5, Amazon Nova

Installation:
  pip install llmfy[google-genai] # Google AI
  pip install llmfy[openai]       # OpenAI
  pip install llmfy[boto3]        # AWS Bedrock

Environment variables required for Google AI:
  GOOGLE_API_KEY

Prompt caching on Google AI:
  Google AI supports two types of caching:

  1. Explicit caching (cachedContent):
     - Create a cache object with client.caches.create() containing the large
       stable content (system instruction, documents, etc.).
     - Pass the returned cache resource name via GoogleAIConfig(cached_content=...).
     - Guaranteed cache hits; billed at ~25% of normal input price (~75% savings).
     - Cache storage is charged per token-hour.
     - Default TTL is 1 hour; no minimum or maximum bounds.

  2. Implicit caching (automatic on Gemini 2.5+):
     - No setup required; enabled by default on all Gemini 2.5 and newer models.
     - Cache hits are not guaranteed but apply a billing benefit when they occur.

  Supported models for explicit caching:
    models/gemini-2.5-pro    (min 2,048 tokens)
    models/gemini-2.5-flash  (min 2,048 tokens)
    models/gemini-3.1-pro-preview  (min 4,096 tokens)
    models/gemini-3.5-flash        (min 4,096 tokens)

  Important:
    - Use the full model path format (e.g. models/gemini-2.5-flash) when
      creating the cache. The generation request model must match exactly.
    - Do NOT repeat the cached content in system_message — it is already
      injected by the API.
""" * 3  # repeat to push past the 2,048-token minimum threshold

MODEL = "gemini-2.5-flash"
MODEL_FULL_PATH = f"models/{MODEL}"  # required format for cache creation


def create_cache() -> str:
    """Create a Google AI cache and return its resource name.

    This is a one-time setup step. In production, run this once and store
    the returned cache name for reuse across many requests within the TTL.
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise LLMfyException(
            'google-genai package is not installed. Install it using `pip install "llmfy[google-genai]"`'
        )

    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    cache = client.caches.create(
        model=MODEL_FULL_PATH,
        config=types.CreateCachedContentConfig(
            system_instruction="You are a helpful assistant specializing in LLMfy.",
            contents=[LARGE_CONTEXT],
            ttl="3600s",  # 1 hour — no min/max bounds
        ),
    )

    print(f"Cache created: {cache.name}")
    return cache.name or ""


def prompt_caching_google_example():
    """Demonstrate prompt caching with gemini-2.5-flash on Google AI.

    Two caching modes are attempted in order:

    1. Explicit caching (paid tier only):
       Requires billing enabled on Google AI. Creates a cachedContent object
       and references it by name on every request. Cache hits are guaranteed.

    2. Implicit caching (free tier, Gemini 2.5+ only):
       Falls back automatically when explicit cache creation fails (free tier).
       Gemini 2.5 models cache the prompt prefix automatically — no setup needed.
       Cache hits are not guaranteed but apply a billing benefit when they occur.

    cache_read_tokens appear in usage details when a cache hit occurs.
    """

    # Step 1 — attempt explicit cache creation (requires paid tier)
    cached_content_name = None
    try:
        cached_content_name = create_cache()
        print("Using explicit caching (paid tier).")
    except Exception as e:
        print(f"Explicit cache creation failed: {e}")
        print("Falling back to implicit caching (Gemini 2.5+ automatic).\n")

    # Step 2 — configure the model
    if cached_content_name:
        # Explicit cache: pass the resource name; do NOT set system_message.
        config = GoogleAIConfig(
            temperature=0.7,
            enable_prompt_caching=True,
            cached_content=cached_content_name,
        )
        llm = GoogleAIModel(model=MODEL, config=config)
        # Do NOT pass system_message — the system instruction is inside the cache.
        # Repeating it would send the content twice and waste tokens.
        agent = LLMfy(llm)
    else:
        # Implicit cache: send the large context as the system prompt.
        # Gemini 2.5+ will cache it automatically when the same prefix repeats.
        config = GoogleAIConfig(
            temperature=0.7,
            enable_prompt_caching=True,  # intent flag — implicit caching is automatic
        )
        llm = GoogleAIModel(model=MODEL, config=config)
        agent = LLMfy(llm, system_message=LARGE_CONTEXT)

    questions = [
        "What providers does LLMfy support?",
        "How do I install LLMfy for Google AI?",
        "What environment variables are required for Google AI?",
        "What is the minimum token requirement for explicit caching on gemini-2.5-flash?",
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
        print("Note: cache_read_tokens > 0 on every call when explicit caching")
        print("      is active — hits are guaranteed (unlike implicit caching).")

    except LLMfyException as e:
        print(f"Error: {e}")


prompt_caching_google_example()
