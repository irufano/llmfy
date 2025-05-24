from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.llmfy.messages.content_type import ContentType


class Content(BaseModel):
    """Content Class.

    Attributes:
        type (ContentType): Content type `TEXT` or `IMAGE`
        value (str): Value content based on type:
            - text: use text string (e.g. "Some text here...").
            - image:
                - openAI: url image (e.g. "https://image.link.jpg") or base64 (`f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode("utf-8")}"`)
                - bedrock: bytes image (`image = f.read()`) or link s3 if use s3 (`bucket_owner` required, `use_s3` set to `TRUE`).
        format (str): [Bedrock ONLY] Image extension be in ["gif", "jpeg", "png", "webp"]
        use_s3 (str): [Bedrock ONLY] Use image file from AWS S3
        bucket_owner (str): [Bedrock ONLY] bucket id (e.g. "111122223333")
    """

    model_config = ConfigDict(extra="forbid")

    type: ContentType = ContentType.TEXT
    """Content type `TEXT` or `IMAGE`"""

    value: str | bytes
    """Value content based on type:
            - text: use text string (e.g. "Some text here...").
            - image:
                - openAI: url image (e.g. "https://image.link.jpg") or base64 (`image = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode("utf-8")}"`)
                - bedrock: bytes image (`image = f.read()`) or link s3 if use s3 (`bucket_owner` required, `use_s3` set to `TRUE`)."""

    format: Optional[str] = None
    """[Bedrock ONLY] Image extension must be in ["gif", "jpeg", "png", "webp"]"""

    use_s3: Optional[bool] = False
    """[Bedrock ONLY] Use image file from AWS S3"""

    bucket_owner: Optional[str] = None
    """[Bedrock ONLY] bucket id (e.g. "111122223333")"""
