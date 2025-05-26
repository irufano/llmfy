from enum import Enum


class Role(str, Enum):
	"""Role enum for `Message` class."""
	SYSTEM = "system"
	USER = "user"
	ASSISTANT = "assistant"
	TOOL = "tool"

	def __str__(self):
		return self.value

	def __repr__(self):
		return f"'{self.value}'"
