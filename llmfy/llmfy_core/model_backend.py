from enum import StrEnum


class ModelBackend(StrEnum):
    """ModelBackend enum."""

    # OpenAI
    OPENAI_CHAT = "openai_chat"  # Chat Completions API
    OPENAI_RESPONSES = "openai_responses"  # Responses API

    # AWS Bedrock
    BEDROCK_CONVERSE = "bedrock_converse"  # Converse API

    # Google AI
    GOOGLE_GENERATE = "google_generate"  # generate_content API

    # Anthropic
    ANTHROPIC_MESSAGES = "anthropic_messages"  # Messages API

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"'{self.value}'"
