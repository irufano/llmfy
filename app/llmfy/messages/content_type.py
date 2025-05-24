from enum import Enum


class ContentType(str, Enum):
    """ContentType enum for `Content` class."""

    TEXT = "text"
    IMAGE = "image"

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"'{self.value}'"
