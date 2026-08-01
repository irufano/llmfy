from enum import StrEnum


class ServiceProvider(StrEnum):
	"""ServiceProvider enum."""
	OPENAI = "openai"
	BEDROCK = "bedrock"
	GOOGLE = "google"

	def __str__(self):
		return self.value

	def __repr__(self):
		return f"'{self.value}'"
