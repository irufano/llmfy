from enum import StrEnum


class Role(StrEnum):
	"""Role enum for `Message` class."""
	SYSTEM = "system"
	USER = "user"
	ASSISTANT = "assistant"
	TOOL = "tool"

	def __str__(self):
		return self.value

	def __repr__(self):
		return f"'{self.value}'"
