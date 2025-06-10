# Content

content is the input to generate a response to llm. Supported content types are: 
- `TEXT`
- `IMAGE` 
- `DOCUMENT`
- `VIDEO` 

To use `IMAGE`, `DOCUMENT` or `VIDEO` input make sure to use a multi-modal llm that supports the input.

## Text

Text on content can be used directly without the `Content` class, example:

```python
content = "Hello"
       
response = agent.invoke(content) 
```

or with list of class `Content`, example

```python
content = [
    Content(
        value="Hello",
    )
]
       
response = agent.invoke(content) 
```

## Image

Image content value has different approaches with the available providers:

- openAI: 
  - image url (e.g. "https://image.link.jpg") or base64 (`f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode("utf-8")}"`)
- bedrock: 
  - image bytes (`image = f.read()`) or link s3 if use s3 (`bucket_owner` required, `use_s3` set to `TRUE`).
  - `ContentType.IMAGE` extension must be in ["gif", "jpeg", "png", "webp"]
Use bytes for bedrock:
```python
input_image = "llmfy/test/simple_flowchart.jpg"
    with open(input_image, "rb") as f:
        image_bytes = f.read()

content = [
    Content(
        value="Jelaskan flowchart berikut.",
    ),
    Content(
        type=ContentType.IMAGE,
        value=image_bytes,
    ),
]
       
response = agent.invoke(content) 
```

Use base64 for openai:
```python
input_image = "llmfy/test/simple_flowchart.jpg"
    with open(input_image, "rb") as f:
        image_base64 = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode("utf-8")}"

content = [
    Content(
        value="Jelaskan flowchart berikut.",
    ),
    Content(
        type=ContentType.IMAGE,
        value=image_base64,
    ),
]
       
response = agent.invoke(content) 
```

Use AWS S3 for bedrock:
```python
content = [
    Content(
        value="Jelaskan flowchart berikut.",
    ),
    Content(
        type=ContentType.IMAGE,
        use_s3=True,
        bucket_owner="111122223333",
        value="s3://amzn-s3-demo-bucket/myImage",
    ),
]
       
response = agent.invoke(content) 
```


## Document

Document (pdf only) content value has different approaches with the available providers:

- openAI: 
  - pdf base64 (`doc = f"data:application/pdf;base64,{base64.b64encode(f.read()).decode("utf-8")}"`)
- bedrock: 
  - pdf bytes (`doc = f.read()`) or link s3 if use s3 (`bucket_owner` required, `use_s3` set to `TRUE`).

Use bytes for bedrock:
```python
input_doc = "llmfy/test/short_stories.pdf"
    with open(input_doc, "rb") as f:
        doc = f.read()

content = [
    Content(
        type=ContentType.DOCUMENT,
        filename="short_stories",
        value=doc,
    ),
    Content(
        type=ContentType.TEXT,
        value="Siapa pemeran dalam cerita di dokumen?",
    ),
]
       
response = agent.invoke(content) 
```

Use base64 for openai (should include `filename` with file extension):
```python
input_doc = "llmfy/test/short_stories.pdf"
    with open(input_doc, "rb") as f:
        doc = (
            f"data:application/pdf;base64,{base64.b64encode(f.read()).decode("utf-8")}"
        )

content = [
    Content(
        type=ContentType.DOCUMENT,
        filename="short_stories.pdf",
        value=doc,
    ),
    Content(
        value="Siapa pemeran dalam cerita di dokumen?",
    ),
]
       
response = agent.invoke(content) 
```

Use AWS S3 for bedrock:
```python
content = [
    Content(
        type=ContentType.DOCUMENT,
        use_s3=True,
        bucket_owner="111122223333",
        value="s3://amzn-s3-demo-bucket/myPdf",
    ),
    Content(
        type=ContentType.TEXT,
        value="Siapa pemeran dalam cerita di dokumen?",
    ),
]
       
response = agent.invoke(content) 
```


## Video

Video input only support with `bedrock` provider, `openai` not support video input yet.

- openAI: not supported yet
- bedrock: 
  - mp4 bytes (`video = f.read()`) or link s3 if use s3 (`bucket_owner` required, `use_s3` set to `TRUE`).
  - `ContentType.VIDEO` extension must be in ["wmv", "mpg", "mpeg", "three_gp", "flv", "mp4", "mov", "mkv", "webm"]

Use bytes for bedrock:
```python
input_video = "llmfy/test/sample_video.mp4"
    with open(input_video, "rb") as f:
        video_bytes = f.read()

content = [
    Content(
        type=ContentType.TEXT,
        value="Apa yg terjadi di video berikut.",
    ),
    Content(
        type=ContentType.VIDEO,
        format="mp4",
        value=video_bytes,
    ),
]
       
response = agent.invoke(content) 
```

Use AWS S3 for bedrock:
```python
content = [
    Content(
        type=ContentType.TEXT,
        value="Apa yg terjadi di video berikut.",
    ),
    Content(
        type=ContentType.VIDEO,
        use_s3=True,
        bucket_owner="111122223333",
        value="s3://amzn-s3-demo-bucket/myVideo",
    )
]
       
response = agent.invoke(content) 
```