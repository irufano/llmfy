from dotenv import load_dotenv

from llmfy.llmfy_core.embeddings import BedrockEmbedding

# from llmfy.llmfy_core.embeddings.openai.openai_embedding import OpenAIEmbedding
from llmfy.vector_store.document import Document
from llmfy.vector_store.faiss_index.faiss_vector_store import FAISSVectorStore

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
    

knowledge_store_path()
knowledge_store_buffers()

