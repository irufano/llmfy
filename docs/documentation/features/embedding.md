# Embedding

Embedding is a way to represent data as a vector of numbers, so that a computer can compare and process it.
LLMfy can use embedding.

## Providers

### AWS Bedrock

> See available embedding models: [AWS Bedrock Embedding Models](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html)

```python
embedding = BedrockEmbedding(model="amazon.titan-embed-text-v1")
```

### OpenAI

> See available embedding models: [OpenAI Embedding Models](https://developers.openai.com/api/docs/guides/embeddings#embedding-models)

```python
embedding = OpenAIEmbedding(model="text-embedding-3-small")
```

### Google AI

> See available embedding models: [Google AI Embedding Models](https://ai.google.dev/gemini-api/docs/models#specialized_task_models)

```python
embedding = GoogleAIEmbedding(model="gemini-embedding-001")
```

## Define Embedding

```python
from llmfy import BedrockEmbedding, OpenAIEmbedding, GoogleAIEmbedding
```

### Encode

Encode single text.

```python linenums="4"
text = "The cat sits on the mat"
result = embedding.encode(text=text)
```


### Encode with Batch

Encode texts into embedding with batch process.

```python linenums="5"
texts = [
    "The cat sits on the mat",
    "Dogs are loyal animals",
    "Artificial intelligence is transforming the world",
    "Quantum computing is the future of technology",
    "The sun rises in the east",
]

embeddings = embedding.encode_batch(
    texts,
    batch_size=3,
)
```

### Usage

To view usage embedding you can use `llmfy_usage_tracker` [here](../../documentation/features/usage.md). Usually embedding use `input token` only for usage the output token not count.

> **Note:** Google AI embedding usage tracks input tokens via a separate `count_tokens` call, since the embedding API response does not include token usage metadata.
