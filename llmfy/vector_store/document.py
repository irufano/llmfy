from pydantic import BaseModel


class Document(BaseModel):
    """Container for text document with dynamic metadata"""

    id: str
    text: str

    model_config = {
        "extra": "allow"  # Allow extra fields to be set dynamically
    }
