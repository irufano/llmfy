# Embedding

Embedding is a way to represent data as a vector of numbers, so that a computer can compare and process it.
LLMfy can use embedding.

## Define Embedding

```python
embedding = BedrockEmbedding(model="amazon.titan-embed-text-v1")
```

or 

```python
 embedding = OpenAIEmbedding(model="text-embedding-3-small")
```

### Encode

Encode single text.

```python linenums="4"
text = "The cat sits on the mat",
result = embedding.encode(text=text)
```


### Encode with Batch

Encode texts into embedding with batch prosess.

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