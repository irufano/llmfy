from typing import Any

from pydantic import BaseModel


class Document(BaseModel):
    """Container for text document with dynamic metadata"""

    id: str
    text: str

    model_config = {
        "extra": "allow"  # Allow extra fields to be set dynamically (for metadata needs)
    }

    def __getattr__(self, name: str) -> Any:
        """Allow dynamic attribute access for type checking"""
        try:
            return super().__getattribute__(name)
        except AttributeError:
            # Return from __dict__ for dynamic attributes
            return self.__dict__.get(name)
