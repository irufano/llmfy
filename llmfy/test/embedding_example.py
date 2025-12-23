from dotenv import load_dotenv

from llmfy.llmfy_core.embeddings import BedrockEmbedding
from llmfy.llmfy_core.embeddings.openai.openai_embedding import OpenAIEmbedding
from llmfy.llmfy_core.usage.usage_tracker import llmfy_usage_tracker

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


def bedrock_embed_batch_text():
    # Sample texts
    with llmfy_usage_tracker() as usage:
        texts = [
            "The cat sits on the mat",
            "Dogs are loyal animals",
            "Artificial intelligence is transforming the world",
            "Quantum computing is the future of technology",
            "The sun rises in the east",
        ]
        embedding = BedrockEmbedding(model="amazon.titan-embed-text-v1")
        result = embedding.encode_batch(texts=texts, show_progress_bar=True)
        print(result)
        print(usage)

def openai_embed_batch_text():
    # Sample texts
    with llmfy_usage_tracker() as usage:
        texts = [
            "The cat sits on the mat",
            "Dogs are loyal animals",
            "Artificial intelligence is transforming the world",
            "Quantum computing is the future of technology",
            "The sun rises in the east",
        ]
        embedding = OpenAIEmbedding(model="text-embedding-3-small")
        result = embedding.encode_batch(texts=texts,  show_progress_bar=True)
        print(result)
        print(usage)

# bedrock_embed_text()
# openai_embed_text()
# bedrock_embed_batch_text()
openai_embed_batch_text()
