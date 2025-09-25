# Content

Content is the input to generate a response to llm. Supported content types are: 

- `TEXT`
- `IMAGE` 
- `DOCUMENT`
- `VIDEO` 

To use `IMAGE`, `DOCUMENT` or `VIDEO` input make sure to use a multi-modal llm that supports the input.

## Text

Text on content can be used directly without the `Content` class, example:

```python linenums="7"
content = "Hello"
       
response = llmfy.invoke(content) 
```

or with list of class `Content`, example

```python linenums="7"
content = [
    Content(
        value="Hello",
    )
]
       
response = llmfy.invoke(content) 
```

## Image

Image content value has different approaches with the available providers:

### OpenAI
  
  - image url (e.g. "https://image.link.jpg") or base64 (`f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode("utf-8")}"`)

  - Example using base64 for openai:
    ```python linenums="7"
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
        
    response = llmfy.invoke(content) 
    ```
  
### Bedrock

  - image bytes (`image = f.read()`) or link s3 if use s3 (`bucket_owner` required, `use_s3` set to `TRUE`).
  - `ContentType.IMAGE` extension must be in ["gif", "jpeg", "png", "webp"]
Use bytes for bedrock:
```python linenums="7"
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
       
response = llmfy.invoke(content) 
```
  - Example use AWS S3 for bedrock:
    ```python linenums="7"
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
        
    response = llmfy.invoke(content) 
    ```


## Document

Document (pdf only) content value has different approaches with the available providers:

### OpenAI
  
  - pdf base64 (`doc = f"data:application/pdf;base64,{base64.b64encode(f.read()).decode("utf-8")}"`)
  - Example use base64 for openai (should include `filename` with file extension):
    ```python linenums="7"
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
        
    response = llmfy.invoke(content) 
    ```

### Bedrock

  - pdf bytes (`doc = f.read()`) or link s3 if use s3 (`bucket_owner` required, `use_s3` set to `TRUE`).
  - Example use bytes for bedrock:
    ```python linenums="7"
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
        
    response = llmfy.invoke(content) 
    ```
  - Example use AWS S3 for bedrock:
    ```python linenums="7"
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
        
    response = llmfy.invoke(content) 
    ```


## Video

Video input only support with `bedrock` provider, `openai` not support video input yet.

### OpenAI

- Not supported yet
  
### Bedrock
  - mp4 bytes (`video = f.read()`) or link s3 if use s3 (`bucket_owner` required, `use_s3` set to `TRUE`).
  - `ContentType.VIDEO` extension must be in ["wmv", "mpg", "mpeg", "three_gp", "flv", "mp4", "mov", "mkv", "webm"]
  - Example use bytes for bedrock:
    ```python linenums="7"
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
        
    response = llmfy.invoke(content) 
    ```
  - Example use AWS S3 for bedrock:
    ```python linenums="7"
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
        
    response = llmfy.invoke(content) 
    ```