# Hello

```python
def bedrock_embed_text():
    # Sample texts
    with llmfy_usage_tracker() as usage:
        texts = "Artificial intelligence is transforming the world"
        embedding = BedrockEmbedding(model="amazon.titan-embed-text-v1")
        result = embedding.encode(text=texts)
        print(result)
        print(usage)

```


[Attribute Lists](irufano.github.io){ data-preview }
