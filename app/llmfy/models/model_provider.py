from enum import Enum


class ModelProvider(str, Enum):
	"""ModelProvider enum."""
	OPENAI = "openai"
	BEDROCK = "bedrock"

	def __str__(self):
		return self.value

	def __repr__(self):
		return f"'{self.value}'"
