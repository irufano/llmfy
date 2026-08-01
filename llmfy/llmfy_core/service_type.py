from enum import StrEnum


class ServiceType(StrEnum):
	"""ServiceType enum."""
	LLM = "llm"
	EMBEDDING = "embedding"

	def __str__(self):
		return self.value

	def __repr__(self):
		return f"'{self.value}'"
