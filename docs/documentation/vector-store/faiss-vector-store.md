# FAISS Vector Store

FAISS stands for Facebook AI Similarity Search — it’s an open-source library developed by Meta (Facebook AI Research) for efficient similarity search and clustering of dense vectors.


## Create vector store

Provide some sample texts
```python
texts = [
    "The cat sits on the mat",
    "Dogs are loyal animals",
    "Artificial intelligence is transforming the world",
    "Quantum computing is the future of technology",
    "The sun rises in the east",
]
```

## Create documents

Create document each text
```python
from llmfy import Document

docs = []
for index, text in enumerate(texts):
    metadata = {"index": f"meta_{index}", "author": "irufano"}
    docs.append(Document(id=str(index), text=text, **metadata))
```

## Encode documents into vector using embedding

```python
from llmfy import FAISSVectorStore

embedding = BedrockEmbedding(model="amazon.titan-embed-text-v1")
# embedding = OpenAIEmbedding(model="text-embedding-3-small")
store = FAISSVectorStore(embedding)
store.encode_documents(docs)
```

### Save to local
We can save to local
```python
store.save_to_path(path)
```

### Save as buffer (to store to another storage )
We can create as buffers and save to another storage e.g. cloud, s3 etc.
```python
buffers = store.create_buffers()
# Save buffers to another storage process here
```

## Load vector

### From local
```python
embedding = BedrockEmbedding(model="amazon.titan-embed-text-v1")
new_store = FAISSVectorStore(embedding)
new_store.load_from_path(path)
```

### From buffers
```python
embedding = BedrockEmbedding(model="amazon.titan-embed-text-v1")
new_store = FAISSVectorStore(embedding)
new_store.load_from_buffers(buffers)
```


## Do search 
```python
# --- Simulating search ---
query = "Machine learning and AI"
results = new_store.search(query, k=2)
for doc, score, idx in results:
    print(
        f"- Match: {doc.text}, Index: {idx}, score: {score:.4f}, author: {doc.author}"  # type: ignore
    )
```

output:
```txt
- Match: Artificial intelligence is transforming the world, Index: 2, score: 0.5774, author: irufano
- Match: Quantum computing is the future of technology, Index: 3, score: 0.3926, author: irufano
```

You can see advance examples [here](../../examples/example-faiss-vectore-store.md).
