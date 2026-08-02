# Content

Content is the input used to generate a response from an LLM. Supported content types are:

- `TEXT`
- `IMAGE`
- `DOCUMENT`
- `VIDEO`

To use `IMAGE`, `DOCUMENT`, or `VIDEO` input, make sure to use a multi-modal model that supports the type.

---

## Text

Text content can be passed directly as a string without the `Content` class:

```python linenums="1"
response = llmfy.invoke("Hello")
```

Or as a list of `Content` objects:

```python linenums="1"
from llmfy import Content

content = [
    Content(value="Hello"),
]

response = llmfy.invoke(content)
```

---

## Image

Image input is supported by **Anthropic**, **OpenAI** (Chat Completions and Responses API), **AWS Bedrock**, and **Google AI**.

### Anthropic

Accepts raw image bytes (auto-encoded to base64) or an already-base64-encoded string. `format` is required. Supported formats: `jpeg`, `png`, `gif`, `webp`.

!!! warning "No data URI, no plain URL, no S3"
    Unlike OpenAI/Google, `Content.value` must be raw bytes or a bare base64 string — **not** a `data:image/...;base64,...` URI and not a plain image URL. `use_s3` is a Bedrock-only field and raises `LLMfyException` on `AnthropicMessagesModel`.

```python linenums="1"
from llmfy import Content, ContentType

input_image = "path/to/image.jpg"
with open(input_image, "rb") as f:
    image_bytes = f.read()

content = [
    Content(value="Describe this image."),
    Content(
        type=ContentType.IMAGE,
        format="jpeg",
        value=image_bytes,
    ),
]

response = llmfy.invoke(content)
```

### OpenAI (Chat Completions)

Accepts a base64 data URI or an image URL.

```python linenums="1"
import base64
from llmfy import Content, ContentType

input_image = "path/to/image.jpg"
with open(input_image, "rb") as f:
    image = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"

# Or use an image URL directly:
# image = "https://example.com/image.jpg"

content = [
    Content(value="Describe this image."),
    Content(type=ContentType.IMAGE, value=image),
]

response = llmfy.invoke(content)
```

### OpenAI (Responses API)

Same as OpenAI (Chat Completions) above — a base64 data URI or an image URL.

```python linenums="1"
import base64
from llmfy import Content, ContentType

input_image = "path/to/image.jpg"
with open(input_image, "rb") as f:
    image = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"

# Or use an image URL directly:
# image = "https://example.com/image.jpg"

content = [
    Content(value="Describe this image."),
    Content(type=ContentType.IMAGE, value=image),
]

response = llmfy.invoke(content)
```

### AWS Bedrock

Accepts raw image bytes or an S3 URI. Supported formats: `gif`, `jpeg`, `png`, `webp`.

**Using bytes:**

```python linenums="1"
from llmfy import Content, ContentType

input_image = "path/to/image.jpg"
with open(input_image, "rb") as f:
    image_bytes = f.read()

content = [
    Content(value="Describe this image."),
    Content(
        type=ContentType.IMAGE,
        format="jpeg",
        value=image_bytes,
    ),
]

response = llmfy.invoke(content)
```

**Using AWS S3:**

```python linenums="1"
content = [
    Content(value="Describe this image."),
    Content(
        type=ContentType.IMAGE,
        use_s3=True,
        bucket_owner="111122223333",
        value="s3://amzn-s3-demo-bucket/myImage",
    ),
]

response = llmfy.invoke(content)
```

### Google AI

Accepts a base64 data URI or an HTTP URL.

```python linenums="1"
import base64
from llmfy import Content, ContentType

input_image = "path/to/image.jpg"
with open(input_image, "rb") as f:
    image = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"

# Or use an HTTP URL directly:
# image = "https://example.com/image.jpg"

content = [
    Content(value="Describe this image."),
    Content(type=ContentType.IMAGE, value=image),
]

response = llmfy.invoke(content)
```

---

## Document

Document (PDF only) input is supported by **Anthropic**, **OpenAI** (Chat Completions only), **AWS Bedrock**, and **Google AI**.

!!! warning "Not supported on OpenAI Responses API"
    `ContentType.DOCUMENT` raises `LLMfyException` on `OpenAIResponsesModel` — only text and image input are implemented there. Use `OpenAIChatModel` for document input on OpenAI.

### Anthropic

Accepts raw PDF bytes (auto-encoded to base64) or an already-base64-encoded string. `filename` is required but is only used as a display title — it does not need a `.pdf` extension. `use_s3` is a Bedrock-only field and raises `LLMfyException` on `AnthropicMessagesModel`.

```python linenums="1"
from llmfy import Content, ContentType

input_doc = "path/to/document.pdf"
with open(input_doc, "rb") as f:
    doc = f.read()

content = [
    Content(
        type=ContentType.DOCUMENT,
        filename="document",
        value=doc,
    ),
    Content(value="Who are the characters in this document?"),
]

response = llmfy.invoke(content)
```

### OpenAI (Chat Completions)

Accepts a base64 data URI. The `filename` must include the `.pdf` extension.

```python linenums="1"
import base64
from llmfy import Content, ContentType

input_doc = "path/to/document.pdf"
with open(input_doc, "rb") as f:
    doc = f"data:application/pdf;base64,{base64.b64encode(f.read()).decode('utf-8')}"

content = [
    Content(
        type=ContentType.DOCUMENT,
        filename="document.pdf",
        value=doc,
    ),
    Content(value="Who are the characters in this document?"),
]

response = llmfy.invoke(content)
```

### OpenAI (Responses API)

Not supported. `ContentType.DOCUMENT` raises `LLMfyException` — use `OpenAIChatModel` instead.

### AWS Bedrock

Accepts raw PDF bytes or an S3 URI.

**Using bytes:**

```python linenums="1"
from llmfy import Content, ContentType

input_doc = "path/to/document.pdf"
with open(input_doc, "rb") as f:
    doc = f.read()

content = [
    Content(
        type=ContentType.DOCUMENT,
        filename="document",
        value=doc,
    ),
    Content(
        type=ContentType.TEXT,
        value="Who are the characters in this document?",
    ),
]

response = llmfy.invoke(content)
```

**Using AWS S3:**

```python linenums="1"
content = [
    Content(
        type=ContentType.DOCUMENT,
        use_s3=True,
        bucket_owner="111122223333",
        value="s3://amzn-s3-demo-bucket/myPdf",
    ),
    Content(
        type=ContentType.TEXT,
        value="Who are the characters in this document?",
    ),
]

response = llmfy.invoke(content)
```

### Google AI

Accepts a base64 data URI. The `filename` must include the `.pdf` extension.

```python linenums="1"
import base64
from llmfy import Content, ContentType

input_doc = "path/to/document.pdf"
with open(input_doc, "rb") as f:
    doc = f"data:application/pdf;base64,{base64.b64encode(f.read()).decode('utf-8')}"

content = [
    Content(
        type=ContentType.DOCUMENT,
        filename="document.pdf",
        value=doc,
    ),
    Content(value="Who are the characters in this document?"),
]

response = llmfy.invoke(content)
```

---

## Video

Video input is supported by **AWS Bedrock** and **Google AI**. Anthropic and OpenAI do not support video input.

### Anthropic

Not supported. `ContentType.VIDEO` raises `LLMfyException` — the native Messages API has no video input support.

### OpenAI (Chat Completions)

Not supported yet.

### OpenAI (Responses API)

Not supported yet.

### AWS Bedrock

Accepts raw video bytes or an S3 URI. Supported formats: `wmv`, `mpg`, `mpeg`, `three_gp`, `flv`, `mp4`, `mov`, `mkv`, `webm`.

**Using bytes:**

```python linenums="1"
from llmfy import Content, ContentType

input_video = "path/to/video.mp4"
with open(input_video, "rb") as f:
    video_bytes = f.read()

content = [
    Content(type=ContentType.TEXT, value="What happens in this video?"),
    Content(
        type=ContentType.VIDEO,
        format="mp4",
        value=video_bytes,
    ),
]

response = llmfy.invoke(content)
```

**Using AWS S3:**

```python linenums="1"
content = [
    Content(type=ContentType.TEXT, value="What happens in this video?"),
    Content(
        type=ContentType.VIDEO,
        use_s3=True,
        bucket_owner="111122223333",
        value="s3://amzn-s3-demo-bucket/myVideo",
    ),
]

response = llmfy.invoke(content)
```

### Google AI

Accepts an HTTP URL, a YouTube URL, or raw video bytes (recommended for files under 20 MB).

**Using a URL:**

```python linenums="1"
from llmfy import Content, ContentType

content = [
    Content(type=ContentType.TEXT, value="What happens in this video?"),
    Content(
        type=ContentType.VIDEO,
        value="https://example.com/video.mp4",
    ),
]

response = llmfy.invoke(content)
```

**Using bytes (< 20 MB):**

```python linenums="1"
from llmfy import Content, ContentType

input_video = "path/to/video.mp4"
with open(input_video, "rb") as f:
    video_bytes = f.read()

content = [
    Content(type=ContentType.TEXT, value="What happens in this video?"),
    Content(
        type=ContentType.VIDEO,
        value=video_bytes,
        format="mp4",  # optional, defaults to mp4
    ),
]

response = llmfy.invoke(content)
```
