from typing import Optional
from pydantic import BaseModel, ConfigDict

from llmfy.llmfy_core.messages.content_type import ContentType


class Content(BaseModel):
    """Content Class.

    Attributes:
        type (ContentType): Content type `TEXT`, `IMAGE`, `DOCUMENT` or `VIDEO`, for image, document and video type make sure using multimodal llm that support them.
            OpenAI not supported `VIDEO` input yet.
        value (str): Value content based on type:
            - text: use text string (e.g. "Some text here...").
            - image:
                - openAI: image url (e.g. "https://image.link.jpg") or base64 (`f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode("utf-8")}"`)
                - bedrock: image bytes (`image = f.read()`) or link s3 if use s3 (`bucket_owner` required, `use_s3` set to `TRUE`).
            - document:
                - openAI: pdf base64 (`doc = f"data:application/pdf;base64,{base64.b64encode(f.read()).decode("utf-8")}"`)
                - bedrock: pdf bytes (`doc = f.read()`) or link s3 if use s3 (`bucket_owner` required, `use_s3` set to `TRUE`).
        format (str): [Bedrock ONLY] format based on ContentType:
            - `ContentType.IMAGE` extension must be in ["gif", "jpeg", "png", "webp"]
            - `ContentType.VIDEO` extension must be in ["mp4"]
        use_s3 (str): [Bedrock ONLY] Use file from AWS S3
        bucket_owner (str): [Bedrock ONLY] bucket id (e.g. "111122223333")
    """

    model_config = ConfigDict(extra="forbid")

    type: ContentType = ContentType.TEXT
    """Content type `TEXT`, `IMAGE`, `DOCUMENT` or `VIDEO`, for image, document and video type make sure using multimodal llm that support them.
    
    OpenAI not supported `VIDEO` input yet."""

    value: str | bytes
    """Value content based on type:
            - text: use text string (e.g. "Some text here...").
            - image:
                - openAI: image url (e.g. "https://image.link.jpg") or base64 (`image = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode("utf-8")}"`)
                - bedrock: image bytes (`image = f.read()`) or link s3 if use s3 (`bucket_owner` required, `use_s3` set to `TRUE`).
            - document:
                - openAI: pdf base64 (`doc = f"data:application/pdf;base64,{base64.b64encode(f.read()).decode("utf-8")}"`)
                - bedrock: pdf bytes (`doc = f.read()`) or link s3 if use s3 (`bucket_owner` required, `use_s3` set to `TRUE`).
            - video:
                - openAI: not supported yet
                - bedrock: mp4 bytes (`video = f.read()`) or link s3 if use s3 (`bucket_owner` required, `use_s3` set to `TRUE`).
    """

    filename: Optional[str] = None
    """PDF file name for content type document"""

    format: Optional[str] = None
    """[Bedrock ONLY] format based on ContentType:
        - `ContentType.IMAGE` extension must be in ["gif", "jpeg", "png", "webp"]
        - `ContentType.VIDEO` extension must be in ["wmv", "mpg", "mpeg", "three_gp", "flv", "mp4", "mov", "mkv", "webm"]
    """

    use_s3: Optional[bool] = False
    """[Bedrock ONLY] Use file from AWS S3"""

    bucket_owner: Optional[str] = None
    """[Bedrock ONLY] bucket id (e.g. "111122223333")"""
