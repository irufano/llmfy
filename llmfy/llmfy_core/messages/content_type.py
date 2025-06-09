from enum import Enum


class ContentType(str, Enum):
    """ContentType enum for `Content` class."""

    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"'{self.value}'"
