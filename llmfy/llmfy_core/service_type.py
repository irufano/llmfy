from enum import Enum


class ServiceType(str, Enum):
	"""ServiceType enum."""
	LLM = "llm"
	EMBEDDING = "embedding"

	def __str__(self):
		return self.value

	def __repr__(self):
		return f"'{self.value}'"
