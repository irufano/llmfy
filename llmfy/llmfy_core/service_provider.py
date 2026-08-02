from enum import StrEnum


class ServiceProvider(StrEnum):
	"""ServiceProvider enum. Vendor-level identity (e.g. "openai") — unlike
	`ModelBackend`, which identifies the specific implementation path
	(e.g. "openai" Chat Completions vs "openai_responses" Responses API) used
	for formatter/usage/error-handling dispatch, `ServiceProvider` collapses
	those back to the vendor they both belong to."""
	OPENAI = "openai"
	BEDROCK = "bedrock"
	GOOGLE = "google"

	def __str__(self):
		return self.value

	def __repr__(self):
		return f"'{self.value}'"
