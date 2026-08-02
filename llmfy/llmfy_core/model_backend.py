from enum import StrEnum


class ModelBackend(StrEnum):
	"""ModelBackend enum."""
	# OpenAI
	OPENAI = "openai"                      # Chat Completions
	OPENAI_RESPONSES = "openai_responses"  # Responses API

	BEDROCK = "bedrock"
	GOOGLE = "google"

	def __str__(self):
		return self.value

	def __repr__(self):
		return f"'{self.value}'"
