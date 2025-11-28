# FAISS Vector Store Example

This sample contains 3 approach vectore store:

- Load and store knowledge base from directory
- Load and store knowledge base from buffers
- Load and store knowledge base from buffers (S3 + Redis)

## Load and store knowledge base from directory
```python linenums="1"
from dotenv import load_dotenv

from llmfy import (
    BedrockEmbedding,
    OpenAIEmbedding,
    llmfy_usage_tracker,
    Document,
    FAISSVectorStore
)

load_dotenv()


def knowledge_store_path():
    path = "../test/kb/test_kb"
    # --- Simulating create knowledge base ---
    # Sample texts
    texts = [
        "The cat sits on the mat",
        "Dogs are loyal animals",
        "Artificial intelligence is transforming the world",
        "Quantum computing is the future of technology",
        "The sun rises in the east",
    ]

    # Create documents
    docs = []
    for index, text in enumerate(texts):
        metadata = {"index": f"meta_{index}", "author": "irufano"}
        docs.append(Document(id=str(index), text=text, **metadata))

    embedding = BedrockEmbedding(model="amazon.titan-embed-text-v1")
    # embedding = OpenAIEmbedding(model="text-embedding-3-small")
    store = FAISSVectorStore(embedding)
    store.encode_documents(docs)
    store.save_to_path(path)

    # --- Simulating for new store load from path ---
    embedding = BedrockEmbedding(model="amazon.titan-embed-text-v1")
    new_store = FAISSVectorStore(embedding)
    new_store.load_from_path(path)

    # --- Simulating search ---
    query = "Machine learning and AI"
    results = new_store.search(query, k=2)
    for doc, score, idx in results:
        print(
            f"- Match: {doc.text}, Index: {idx}, score: {score:.4f}, author: {doc.author}"  # type: ignore
        )

knowledge_store_path()
```

## Load and store knowledge base from buffers
```python linenums="1"
from dotenv import load_dotenv

from llmfy import (
    BedrockEmbedding,
    OpenAIEmbedding,
    llmfy_usage_tracker,
    Document,
    FAISSVectorStore
)

load_dotenv()

def knowledge_store_buffers():
    # --- Simulating create knowledge base ---
    # Sample texts
    texts = [
        "The cat sits on the mat",
        "Dogs are loyal animals",
        "Artificial intelligence is transforming the world",
        "Quantum computing is the future of technology",
        "The sun rises in the east",
    ]

    # Create documents
    docs = []
    for index, text in enumerate(texts):
        metadata = {"index": f"meta_{index}", "author": "irufano"}
        docs.append(Document(id=str(index), text=text, **metadata))

    embedding = BedrockEmbedding(model="amazon.titan-embed-text-v1")
    # embedding = OpenAIEmbedding(model="text-embedding-3-small")
    store = FAISSVectorStore(embedding)
    store.encode_documents(docs)
    buffers = store.create_buffers()

    # --- Simulating for new store load from path ---
    embedding = BedrockEmbedding(model="amazon.titan-embed-text-v1")
    new_store = FAISSVectorStore(embedding)
    new_store.load_from_buffers(buffers)

    # --- Simulating search ---
    query = "Machine learning and AI"
    results = new_store.search(query, k=2)
    for doc, score, idx in results:
        print(
            f"- Match: {doc.text}, Index: {idx}, score: {score:.4f}, author: {doc.author}"  # type: ignore
        )
    
knowledge_store_buffers()
```

## Load and store knowledge base from buffers (S3 + Redis)

### Upload Buffers to S3 Function
```python linenums="1"
import os
import boto3
from typing import Any

def upload_to_s3(
    bucket: str,
    prefix: str,
    buffers: dict[Any, Any],
    create_folder: bool = True,
):
    """
    Upload FAISS index and metadata directly to S3 without saving locally.
    If the folder (prefix) already exists, files will be replaced.

    Args:
        bucket (str): S3 bucket name
        prefix (str): S3 prefix (folder path)
        buffers (dict[Any, Any]): dict: filename -> BytesIO
        create_folder (bool): If True, create an empty "folder" key in S3 console
    """
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_BEDROCK_REGION"),
    )

    # Normalize prefix
    if not prefix.endswith("/"):
        prefix = prefix + "/"

    # Create empty folder placeholder only if requested
    if create_folder:
        try:
            s3.put_object(Bucket=bucket, Key=prefix)
        except Exception as e:
            print(f"Warning: Could not create folder placeholder ({e}), continuing...")

    # Upload (replace if exists)
    for filename, buffer in buffers.items():
        buffer.seek(0)  # reset pointer before upload
        key = f"{prefix}{filename}"
        s3.upload_fileobj(buffer, bucket, key)

    print(f"Files uploaded to s3://{bucket}/{prefix} (replaced if existed)")
```

### Download Buffers from S3 Function
```python linenums="1"
import io
import boto3


def download_from_s3(bucket: str, prefix: str):
    """
    Download all objects under a given S3 prefix into memory buffers (BytesIO).

    Args:
        bucket (str): S3 bucket name.
        prefix (str): Prefix (directory path) in the bucket.

    Returns:
        dict[str, io.BytesIO]: Dictionary mapping filename -> buffer
    """
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_BEDROCK_REGION"),
    )

    # List all objects under the prefix
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

    if "Contents" not in response:
        raise ValueError(f"No files found in s3://{bucket}/{prefix}")

    buffers = {}
    for obj in response["Contents"]:
        key = obj["Key"]

        # Skip "directory" placeholder keys
        if key.endswith("/"):
            continue

        filename = key.split("/")[-1]  # keep only the file name
        buf = io.BytesIO()
        s3.download_fileobj(bucket, key, buf)
        buf.seek(0)
        buffers[filename] = buf

    return buffers

```

### Add Buffers to Redis Function

```python linenums="1"
import redis
from typing import Any

def add_to_redis(
    redis_client: redis.Redis,
    prefix: str,
    buffers: dict[Any, Any],
):
    """
    Upload buffers (in-memory files) to Redis.

    Args:
        redis_client (redis.Redis): Redis client instance
        prefix (str): Redis key prefix (like a folder)
        buffers (dict[Any, Any]): dict: filename -> BytesIO
    """
    for filename, buffer in buffers.items():
        buffer.seek(0)
        key = f"{prefix}:{filename}"
        redis_client.set(key, buffer.read())

    print(f"Uploaded {len(buffers)} files to Redis with prefix '{prefix}'")
```

### Get Buffers from Redis

```python linenums="1"
import io


def get_from_redis(
    redis_client: redis.Redis,
    prefix: str,
):
    """
    Download buffers (in-memory files) from Redis.

    Args:
        redis_client (redis.Redis): Redis client instance
        prefix (str): Redis key prefix

    Returns:
        dict[str, io.BytesIO]: Dictionary mapping filename -> BytesIO
    """
    buffers = {}
    for key in redis_client.scan_iter(f"{prefix}:*"):
        filename = key.decode("utf-8").split(":", 1)[1]  # after prefix:
        data = redis_client.get(key)
        if data is not None:
            buffers[filename] = io.BytesIO(data) # type: ignore

    if not buffers:
        return None

    return buffers
```

### Redis First Buffers Logic Function

```python linenums="1"
def get_index_buffers(
    prefix: str,
):
    """
    Get index buffers start from redis then if no data get from s3.

    Args:
        prefix (str): Redis key prefix or S3 bucket path

    Returns:
        dict[str, io.BytesIO]: Dictionary mapping filename -> BytesIO
    """
    # Get redis first
    r = redis.Redis(host="localhost", port=6379, db=4)
    buffers = get_from_redis(r, prefix)

    # Check redis if no data then get from s3
    if buffers is None:
        print("Buffers not found, getting from s3...")
        buffers = download_from_s3(
            bucket="new-ac-agent-research.dlabssaas.io",
            prefix=prefix,
        )
        # then add to redis
        add_to_redis(r, prefix, buffers)

        # RESET ALL BUFFERS after Redis write
        # The BytesIO objects returned from S3 have their file pointers at the end of the stream after being read, causing the EOFError.
        # After downloading from S3, we call `add_to_redis()` which reads all the buffers to store them in Redis. This moves all the file pointers to the end. so it needs reset all buffers.
        for buf in buffers.values():
            buf.seek(0)

        print("Buffers get from s3 and added to redis.")
        return buffers

    print("Buffers exist on redis.")
    return buffers
```

### Simulating create knowledge base
```python linenums="1"
# Sample texts
texts = [
    "The cat sits on the mat",
    "Dogs are loyal animals",
    "Artificial intelligence is transforming the world",
    "Quantum computing is the future of technology",
    "The sun rises in the east",
]

# Create documents
docs = []
for index, text in enumerate(texts):
    metadata = {"index": f"meta_{index}", "page": index + 1, "author": "irufano"}
    docs.append(Document(id=str(index), text=text, **metadata))

knowledge_base_name = "test_redis"
embedding = BedrockEmbedding(model="amazon.titan-embed-text-v1")
store = FAISSVectorStore(embedding)  # type: ignore
store.encode_documents(docs, batch_size=2)
upload_to_s3(
    bucket="new-ac-agent-research.dlabssaas.io",
    prefix=f"knowledge_base/{knowledge_base_name}",
    buffers=store.create_buffers(),
)
```

```shell
Successfully added 5 documents to index `flat`. 
Vectors total: 5 
```

### Simulating load knowledge base redis first

Get index buffers start from redis then if no data get from s3, after downloaded add to redis then return buffers.

```python linenums="1"
kb_name = "test_redis"
prefix = f"knowledge_base/{kb_name}"

# Get buffers
buffers = get_index_buffers(prefix=prefix)

embedding = BedrockEmbedding(model="amazon.titan-embed-text-v1")
new_store = FAISSVectorStore(embedding)

buffers = download_from_s3(
    bucket="new-ac-agent-research.dlabssaas.io",
    prefix=prefix,
)
print(buffers)
new_store.load_from_buffers(buffers)
```

```shell
Vector store loaded from buffers
```

Then you can do search with `new_store` loaded from S3 + Redis:


```python linenums="1"
# --- Simulating search ---
query = "Machine learning and AI"
results = new_store.search(query, k=2)
for doc, score, idx in results:
    print(
        f"- Match: {doc.text}, Index: {idx}, score: {score:.4f}, author: {doc.author}"  # type: ignore
    )
```

```shell
- Match: Artificial intelligence is transforming the world, Index: 2, score: 0.5982, author: irufano
- Match: Quantum computing is the future of technology, Index: 3, score: 0.3153, author: irufano
```