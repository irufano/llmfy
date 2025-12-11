from typing import Any

from pydantic import BaseModel


class Document(BaseModel):
    """Container for text document with dynamic metadata

    Example usage:
    ```python
    metadata = {
        "source": "llmfy",
    }
    meta = {
        "header_level": 1,
        "header_text": "Hello",
        **(metadata or {}),
    }
    doc = Document(
        id="doc_1",
        text="Sample",
        **meta,
    )
    print(doc)
    print(doc.source)
    print(doc.not_exist)
    ```
    """

    id: str
    text: str

    model_config = {
        "extra": "allow"  # Allow extra fields to be set dynamically (for metadata needs)
    }

    def __getattr__(self, name: str) -> Any:
        # Check normal attributes first
        try:
            return super().__getattribute__(name)
        except AttributeError:
            pass

        # Check Pydantic v2 dynamic fields
        extra = getattr(self, "model_extra", {})
        if name in extra:
            return extra[name]

        # Not found
        return None
