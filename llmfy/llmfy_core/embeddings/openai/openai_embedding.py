import os
import time
from typing import List

from llmfy import LLMfyException
from llmfy.llmfy_core.embeddings.base_embedding_model import BaseEmbeddingModel
from llmfy.llmfy_core.service_provider import ServiceProvider

try:
    import openai
except ImportError:
    openai = None

try:
    import numpy as np
except ImportError:
    np = None


class OpenAIEmbedding(BaseEmbeddingModel):
    """OpenAI embedding client."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
    ):
        """
        Initialize OpenAI embeddings client

        Args:
            model (str): Model name for OpenAI embeddings. Defaults to "text-embedding-3-small".
            api_key (str): OpenAI API key. If None, will use OPENAI_API_KEY environment variable.
        """

        if openai is None:
            raise LLMfyException(
                'openai package is not installed. Install it using `pip install "llmfy[openai]"`'
            )
        if not os.getenv("OPENAI_API_KEY"):
            raise LLMfyException("Please provide `OPENAI_API_KEY` on your environment!")

        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.provider = ServiceProvider.OPENAI
        self.model = model

    def __call_openai_embedding(self, model: str, text: str):
        from llmfy.llmfy_core.usage.usage_tracker import track_openai_embedding_usage

        @track_openai_embedding_usage
        def _call_openai_impl(model: str, text: str):
            response = self.client.embeddings.create(
                model=model,
                input=text,
                encoding_format="float",
            )
            return response

        return _call_openai_impl(model, text)

    def encode(self, text: str) -> List[float]:
        """
        Get embedding for a single text

        Args:
            text (str): text to embed

        Raises:
            ValueError: If no embedding returned
            openai.OpenAIError: For API errors

        Returns:
            List[float]: Embedding vector
        """
        try:
            # Call OpenAI API
            response = self.__call_openai_embedding(model=self.model, text=text)

            # Extract embedding
            if not response.data or len(response.data) == 0:
                raise ValueError("No embedding returned from OpenAI")

            embedding = response.data[0].embedding

            return embedding

        except Exception as e:
            error_message = str(e)
            if (
                "rate_limit_exceeded" in error_message.lower()
                or "rate limit" in error_message.lower()
            ):
                print(f"Rate limit exceeded: {e}")
            elif "invalid" in error_message.lower():
                print(f"Invalid request: {text[:100]}...")
            else:
                print(f"OpenAI API error: {e}")
            raise e

    def encode_batch(
        self,
        texts: List[str] | str,
        batch_size: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        show_progress_bar: bool = False,
    ):
        """
        Encode texts into embedding with batch process.

        Args:
            texts (List[str] | str): Text(s) to embed
            batch_size (int, optional): Number of texts per batch. Defaults to 100.
            max_retries (int, optional): Maximum retry attempts. Defaults to 3.
            retry_delay (float, optional): Delay between retries in seconds. Defaults to 1.0.
            show_progress_bar (bool, optional): Whether to show progress. Defaults to False.

        Returns:
            NDArray[Any]: Array of embeddings
        """
        if np is None:
            raise LLMfyException(
                "`encode_batch` operation is using numpy, numpy package is not installed. "
                'Install it using `pip install "llmfy[numpy]"`'
            )

        if isinstance(texts, str):
            texts = [texts]

        embeddings = []

        if show_progress_bar:
            print(f"Generating embeddings for {len(texts)} texts...")

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]

            if show_progress_bar:
                print(
                    f"Processing batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}"
                )

            batch_embeddings = []
            for text in batch_texts:
                # Retry logic for individual text
                for attempt in range(max_retries):
                    try:
                        embedding = self.encode(text)
                        batch_embeddings.append(embedding)
                        break
                    except Exception as e:
                        error_message = str(e)
                        if (
                            "rate_limit_exceeded" in error_message.lower()
                            or "rate limit" in error_message.lower()
                        ):
                            if attempt < max_retries - 1:
                                wait_time = retry_delay * (
                                    2**attempt
                                )  # Exponential backoff
                                print(
                                    f"Rate limited, waiting {wait_time}s before retry..."
                                )
                                time.sleep(wait_time)
                                continue
                            print(f"Rate limit error after {max_retries} attempts: {e}")
                            raise
                        print(f"Error processing text: {e}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        raise

            embeddings.extend(batch_embeddings)

            # Small delay between batches to avoid rate limits
            if i + batch_size < len(texts):
                time.sleep(0.1)

        return np.array(embeddings)
