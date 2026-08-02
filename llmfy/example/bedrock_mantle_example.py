import os

import openai
from dotenv import load_dotenv

from llmfy import (
    AnthropicMessagesConfig,
    AnthropicMessagesModel,
    LLMfy,
    LLMfyException,
    OpenAIChatConfig,
    OpenAIChatModel,
    OpenAIResponsesConfig,
    OpenAIResponsesModel,
    llmfy_usage_tracker,
)

load_dotenv()

# ─── AWS Bedrock Mantle ──────────────────────────────────────────────────────
# `bedrock-mantle` is Bedrock's newer endpoint: OpenAI-compatible Chat
# Completions/Responses APIs plus an Anthropic-compatible Messages API,
# authenticated with a Bedrock API key (bearer token) instead of SigV4.
# Docs: https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-mantle.html
#
# None of this needs any llmfy code changes — OpenAIChatModel,
# OpenAIResponsesModel, and AnthropicMessagesModel all accept `api_key` and
# `base_url`, and just forward them into the official openai/anthropic SDK
# clients. Point base_url at bedrock-mantle and use a Bedrock API key.
#
# Environment variables used by this example:
#   BEDROCK_MANTLE_API_KEY      — a short-term or long-term Bedrock API key
#                                  (see https://docs.aws.amazon.com/bedrock/latest/userguide/api-keys.html)
#   BEDROCK_MANTLE_REGION       — defaults to "us-east-1"
#   BEDROCK_MANTLE_WORKSPACE_ID — optional; scopes Messages API requests to a
#                                  Bedrock Workspace (Anthropic-compatible
#                                  resource isolation, see
#                                  https://docs.aws.amazon.com/bedrock/latest/userguide/workspaces.html)
#   BEDROCK_MANTLE_CHAT_MODEL         — model ID for the Chat Completions example
#   BEDROCK_MANTLE_RESPONSES_MODEL    — model ID for the Responses API example
#   BEDROCK_MANTLE_MESSAGES_MODEL     — model ID for the Anthropic Messages example
#   BEDROCK_MANTLE_RESPONSES_BASE_URL — base_url for the Responses API example
#                                        (defaults to the ".../openai/v1" path
#                                        that GPT-5.6 Luna specifically requires
#                                        — see the comment above RESPONSES_BASE_URL)
#
# The *_MODEL vars exist because model availability on bedrock-mantle is both
# per-account (channel-program accounts may not have every model enabled) AND
# per-API-surface (e.g. AWS's own compatibility table lists a model as
# Responses-capable, yet a specific account/model combination can still 400
# with "does not support the '/v1/...' API"). There is no single call that
# confirms "my account can reach model X on surface Y" ahead of time — run
# bedrock_mantle_list_available_models_example() to see which model IDs your
# account can reach at all, then override these env vars with the ones that
# actually work for the surface you need; don't rely on the defaults below.
# Separately, RESPONSES_BASE_URL exists because not all models share the same
# base path on bedrock-mantle — see the comment above that variable.

BEDROCK_API_KEY = os.getenv("BEDROCK_MANTLE_API_KEY")
BEDROCK_REGION = os.getenv("BEDROCK_MANTLE_REGION", "us-east-1")
BEDROCK_WORKSPACE_ID = os.getenv("BEDROCK_MANTLE_WORKSPACE_ID", "default")

CHAT_MODEL = os.getenv("BEDROCK_MANTLE_CHAT_MODEL", "openai.gpt-oss-120b")
RESPONSES_MODEL = os.getenv("BEDROCK_MANTLE_RESPONSES_MODEL", "openai.gpt-5.6-luna")
MESSAGES_MODEL = os.getenv("BEDROCK_MANTLE_MESSAGES_MODEL", "anthropic.claude-haiku-4-5")

# Not every model on bedrock-mantle is served under the same base path.
# gpt-oss-120b's model card lists its bedrock-mantle URL as ".../v1"; GPT-5.6
# Luna's model card explicitly says it's served on the ".../openai/v1"
# path instead ("This is different from the v1/responses path used by other
# models on the responses endpoint" — see
# https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-openai-gpt-56-luna.html).
# There's no way to know a given model's required prefix except by checking
# its own model card's "Programmatic Access" table — if you swap
# BEDROCK_MANTLE_RESPONSES_MODEL for a different model, also check whether it
# needs this "/openai" prefix or the plain one and override this accordingly.
RESPONSES_BASE_URL = os.getenv(
    "BEDROCK_MANTLE_RESPONSES_BASE_URL",
    f"https://bedrock-mantle.{BEDROCK_REGION}.api.aws/openai/v1",
)

# Bedrock Mantle scopes the Messages API to a Workspace via a header rather
# than a constructor kwarg — the `anthropic` SDK sends the fixed headers
# (x-api-key, anthropic-version) itself, so anything beyond that goes through
# `default_headers`, which AnthropicMessagesModel forwards to `anthropic.Anthropic(...)`.
ANTHROPIC_DEFAULT_HEADERS = (
    {"anthropic-workspace-id": BEDROCK_WORKSPACE_ID} if BEDROCK_WORKSPACE_ID else None
)

# Used for the Chat Completions example (CHAT_MODEL = gpt-oss-120b), per that
# model's own model card. Deliberately stops at ".../v1" with NO
# "/chat/completions" suffix — the openai SDK appends that itself:
#   OpenAIChatModel.generate() -> self.client.chat.completions.create()
#                               -> POSTs to {base_url}/chat/completions
# Baking "/chat/completions" into this constant would make the SDK double it
# up into ".../v1/chat/completions/chat/completions" and 404. AWS's docs
# table lists the fully-resolved URL per API for readers using raw HTTP —
# that's not the same thing as the SDK's base_url input.
#
# NOT reused for the Responses example below — see RESPONSES_BASE_URL above;
# GPT-5.6 Luna needs a different prefix than gpt-oss-120b does.
OPENAI_COMPAT_BASE_URL = f"https://bedrock-mantle.{BEDROCK_REGION}.api.aws/v1"

# The anthropic SDK appends "/v1/messages" itself, and Bedrock's real path is
# "/anthropic/v1/messages" — so base_url must stop at ".../anthropic".
ANTHROPIC_COMPAT_BASE_URL = f"https://bedrock-mantle.{BEDROCK_REGION}.api.aws/anthropic"

# Bedrock's per-token price for these models — built-in pricing tables only
# know OpenAI's/Anthropic's own model IDs and rates, not Bedrock's, so a
# custom pricing dict is required for accurate cost tracking. Keyed off the
# *_MODEL env vars above rather than a hardcoded string, since whichever
# model ID you end up using needs a matching entry here to get a real cost
# instead of a "model not found" warning from the usage tracker.
#
# These rates are placeholders — update them to the real per-token price for
# your model from https://aws.amazon.com/bedrock/pricing/ before relying on
# cost tracking.
BEDROCK_MANTLE_ANTHROPIC_PRICING = {
    MESSAGES_MODEL: {
        "input": 3.00,
        "output": 15.00,
        "token_unit": 1_000_000,
    },
}
BEDROCK_MANTLE_OPENAI_PRICING = {
    CHAT_MODEL: {
        "input": 0.15,
        "output": 0.60,
        "token_unit": 1_000_000,
    },
    RESPONSES_MODEL: {
        "input": 0.15,
        "output": 0.60,
        "token_unit": 1_000_000,
    },
}


def bedrock_mantle_list_available_models_example():
    """List models this Bedrock account can actually reach on bedrock-mantle.

    Model catalog access varies per AWS account (e.g. accounts provisioned
    through an AWS Solution Provider / Distributor "channel program" may not
    have every model enabled — trying an unavailable model ID raises an
    LLMfyException with a message like "Access to this model is not available
    for channel program accounts..."). Run this first to see which model IDs
    are actually usable instead of guessing.
    """

    # Any of the OpenAI-compatible model classes expose the same underlying
    # `openai.OpenAI` client, which has a `.models.list()` call.
    llm = OpenAIChatModel(
        model="unused-for-listing",
        api_key=BEDROCK_API_KEY,
        base_url=OPENAI_COMPAT_BASE_URL,
    )

    # This calls the raw openai SDK client directly (not through llmfy's
    # invoke()/generate()), so errors surface as openai.APIError, not
    # LLMfyException.
    try:
        models = llm.client.models.list()
        print("\n[Models available on bedrock-mantle for this account]")
        for model in models.data:
            print(f"  - {model.id}")
    except openai.APIError as e:
        print(f"Error listing models: {e}")
    print("---")


def bedrock_mantle_openai_chat_example():
    """OpenAIChatModel pointed at bedrock-mantle's Chat Completions API."""

    llm = OpenAIChatModel(
        model=CHAT_MODEL,
        config=OpenAIChatConfig(temperature=0.7),
        api_key=BEDROCK_API_KEY,
        base_url=OPENAI_COMPAT_BASE_URL,
    )

    agent = LLMfy(llm, system_message="You are a helpful assistant.")

    try:
        with llmfy_usage_tracker(
            openai_pricing=BEDROCK_MANTLE_OPENAI_PRICING
        ) as usage:
            response = agent.invoke(
                "Jelaskan quantum computing dalam 1 kalimat pendek."
            )
        print("\n[OpenAI Chat Completions via bedrock-mantle]")
        print(f">> {response.result.content}")
        print(usage)
    except LLMfyException as e:
        print(f"Error: {e}")
        print(f"Status code: {e.status_code}")
        if "does not support" in str(e):
            print(
                "Hint: this model/API combination isn't available for your "
                "account on bedrock-mantle. Run "
                "bedrock_mantle_list_available_models_example() and set the "
                "matching BEDROCK_MANTLE_*_MODEL env var to a model ID your "
                "account can actually use on this API surface."
            )
    print("---")


def bedrock_mantle_openai_responses_example():
    """OpenAIResponsesModel pointed at bedrock-mantle's Responses API."""

    llm = OpenAIResponsesModel(
        model=RESPONSES_MODEL,
        # GPT-5.6 Luna rejects `temperature`/`top_p` outright (400
        # unsupported_parameter) rather than accepting a default for them —
        # None omits the field from the request entirely.
        config=OpenAIResponsesConfig(temperature=None, top_p=None),
        api_key=BEDROCK_API_KEY,
        base_url=RESPONSES_BASE_URL,  # note: NOT OPENAI_COMPAT_BASE_URL — see comment above
    )

    agent = LLMfy(llm, system_message="You are a helpful assistant.")

    try:
        with llmfy_usage_tracker(openai_pricing=BEDROCK_MANTLE_OPENAI_PRICING) as usage:
            response = agent.invoke("Jelaskan quantum computing dalam 1 kalimat pendek")
        print("\n[OpenAI Responses API via bedrock-mantle]")
        print(f">> {response.result.content}")
        print(usage)
    except LLMfyException as e:
        print(f"Error: {e}")
        print(f"Status code: {e.status_code}")
        if "does not support" in str(e):
            print(
                "Hint: either the model doesn't support this API for your "
                "account (run bedrock_mantle_list_available_models_example() "
                "and set BEDROCK_MANTLE_RESPONSES_MODEL to one that does), or "
                "this model needs a different base_url — some models on "
                "bedrock-mantle are served under '/openai/v1' instead of the "
                "plain '/v1' (check the model's 'Programmatic Access' table "
                "on its AWS model card) — override with "
                "BEDROCK_MANTLE_RESPONSES_BASE_URL if so."
            )
        elif "unsupported_parameter" in str(e):
            print(
                "Hint: this model rejects a sampling param outright (e.g. "
                "temperature/top_p) rather than accepting a default — set it "
                "to None in OpenAIResponsesConfig(...) to omit it from the "
                "request, as done above for GPT-5.6 Luna."
            )
    print("---")


def bedrock_mantle_anthropic_messages_example():
    """AnthropicMessagesModel pointed at bedrock-mantle's Messages API."""

    llm = AnthropicMessagesModel(
        model=MESSAGES_MODEL,
        config=AnthropicMessagesConfig(max_tokens=4096, temperature=0.7),
        api_key=BEDROCK_API_KEY,
        base_url=ANTHROPIC_COMPAT_BASE_URL,
        default_headers=ANTHROPIC_DEFAULT_HEADERS,  # None if BEDROCK_MANTLE_WORKSPACE_ID unset
    )

    agent = LLMfy(llm, system_message="You are a helpful assistant.")

    try:
        with llmfy_usage_tracker(
            anthropic_pricing=BEDROCK_MANTLE_ANTHROPIC_PRICING
        ) as usage:
            response = agent.invoke("Jelaskan quantum computing dalam 1 kalimat pendek")
        print("\n[Anthropic Messages API via bedrock-mantle]")
        print(f">> {response.result.content}")
        print(usage)
    except LLMfyException as e:
        print(f"Error: {e}")
        print(f"Status code: {e.status_code}")
        if "does not support" in str(e):
            print(
                "Hint: this model/API combination isn't available for your "
                "account on bedrock-mantle. Run "
                "bedrock_mantle_list_available_models_example() and set the "
                "matching BEDROCK_MANTLE_*_MODEL env var to a model ID your "
                "account can actually use on this API surface."
            )
    print("---")


bedrock_mantle_list_available_models_example()
bedrock_mantle_openai_chat_example()
bedrock_mantle_openai_responses_example()
bedrock_mantle_anthropic_messages_example()
