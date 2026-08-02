from enum import StrEnum


class ModelBackend(StrEnum):
    """ModelBackend enum."""

    # OpenAI
    OPENAI_CHAT = "openai_chat"  # Chat Completions
    OPENAI_RESPONSES = "openai_responses"  # Responses API

    BEDROCK_CONVERSE = "bedrock_converse"  # Converse API
    GOOGLE = "google"

    # Anthropic
    ANTHROPIC_MESSAGES = "anthropic_messages"  # Messages API

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"'{self.value}'"
