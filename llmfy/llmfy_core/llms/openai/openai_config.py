from typing import Optional

from pydantic import BaseModel


class OpenAIConfig(BaseModel):
    """Configuration for OpenAIModel."""

    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

    # Thinking / reasoning
    enable_thinking: bool = False
    """Enable reasoning mode via the Chat Completions API. Supported models:
      - o1
      - o1-mini
      - o3
      - o3-mini
      - o4-mini
      (and any future o-series reasoning models)
    """
    reasoning_effort: Optional[str] = None
    """'low', 'medium', or 'high'. Used with o1/o3/o4-mini reasoning models via
    the Chat Completions API. Defaults to 'medium' when enable_thinking=True and not set."""

    # Prompt caching
    enable_prompt_caching: bool = False
    """Intent flag documenting that prompt caching is desired.

    Reference: https://platform.openai.com/docs/guides/prompt-caching

    OpenAI applies caching automatically for all API requests — no explicit
    markers or request changes are needed. This flag does not alter the request;
    it signals intent and ensures cache usage stats appear in usage details.

    How it works:
      - The longest common prompt prefix is cached server-side automatically.
      - Requests that reuse the same prefix within the TTL window benefit from
        cached tokens. No additional fees are associated with prompt caching.
      - Static content (system prompt, documents) must appear at the beginning
        of the prompt; images and tool definitions must be identical across calls.

    Cache TTL:
      - Standard:          5–10 minutes of inactivity; maximum 1 hour
      - Extended (24h):    gpt-5.5, gpt-5.5-pro, gpt-5.4, gpt-5.2, gpt-5.1, gpt-5,
                           gpt-4.1, and select other models

    Minimum: prompts must contain at least 1,024 tokens to be cached. Requests
    below this threshold show zero cached tokens.

    Supported models (all gpt-4o and newer — caching is automatic):
      GPT-4o family:
        - gpt-4o, gpt-4o-mini (and all dated snapshots)
      GPT-4.1 family:
        - gpt-4.1, gpt-4.1-mini, gpt-4.1-nano
      o-series reasoning models:
        - o1, o1-mini, o3, o3-mini, o3-pro, o4-mini
      GPT-5 family (extended 24h retention):
        - gpt-5, gpt-5.1, gpt-5.2, gpt-5.4, gpt-5.5, gpt-5.5-pro

    Not supported: gpt-3.5-turbo, gpt-4 (non-turbo), and older generation models.

    Cached tokens are reported in usage details as cache_read_tokens whenever
    the API returns prompt_tokens_details.cached_tokens.
    """
