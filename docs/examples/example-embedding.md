# Embedding Example

```python linenums="1"
from dotenv import load_dotenv

from llmfy import (
    BedrockEmbedding,
    OpenAIEmbedding,
    llmfy_usage_tracker,
)

load_dotenv()


def bedrock_embed_text():
    # Sample texts
    with llmfy_usage_tracker() as usage:
        texts = "Artificial intelligence is transforming the world"
        embedding = BedrockEmbedding(model="amazon.titan-embed-text-v1")
        result = embedding.encode(text=texts)
        print(result)
        print(usage)

def openai_embed_text():
    # Sample texts
    with llmfy_usage_tracker() as usage:
        texts = "Artificial intelligence is transforming the world"
        embedding = OpenAIEmbedding(model="text-embedding-3-small")
        result = embedding.encode(text=texts)
        print(result)
        print(usage)



bedrock_embed_text()
openai_embed_text()

```