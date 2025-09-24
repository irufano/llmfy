from enum import Enum


class ServiceProvider(str, Enum):
	"""ServiceProvider enum."""
	OPENAI = "openai"
	BEDROCK = "bedrock"

	def __str__(self):
		return self.value

	def __repr__(self):
		return f"'{self.value}'"
