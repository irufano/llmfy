import os
import time
from typing import List

from llmfy import LLMfyException
from llmfy.llmfy_core.embeddings.base_embedding_model import BaseEmbeddingModel
from llmfy.llmfy_core.service_provider import ServiceProvider
from llmfy.llmfy_utils.logger.llmfy_logger import LLMfyLogger

try:
    from google import genai
except ImportError:
    genai = None

try:
    import numpy as np
except ImportError:
    np = None

logger = LLMfyLogger("LLMfy").get_logger()


class GoogleAIEmbedding(BaseEmbeddingModel):
    """Google AI embedding client."""

    def __init__(
        self,
        model: str = "text-embedding-004",
    ):
        """
        Initialize Google AI embeddings client

        Args:
            model (str): Model name for Google AI embeddings. Defaults to "text-embedding-004".
        """

        if genai is None:
            raise LLMfyException(
                'google-genai package is not installed. Install it using `pip install "llmfy[google-genai]"`'
            )
        if not os.getenv("GOOGLE_API_KEY"):
            raise LLMfyException("Please provide `GOOGLE_API_KEY` on your environment!")

        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.provider = ServiceProvider.GOOGLE
        self.model = model

    def __call_googleai_embedding(self, model: str, text: str):
        from llmfy.llmfy_core.models.google.googleai_usage import (
            track_googleai_embedding_usage,
        )

        @track_googleai_embedding_usage
        def _call_googleai_embedding_impl(model: str, contents: str, client):
            return client.models.embed_content(
                model=model,
                contents=contents,
            )

        return _call_googleai_embedding_impl(model, text, self.client)

    def encode(self, text: str) -> List[float]:
        """
        Get embedding for a single text

        Args:
            text (str): text to embed

        Raises:
            ValueError: If no embedding returned
            google.genai.errors.APIError: For API errors

        Returns:
            List[float]: Embedding vector
        """
        from google.genai import errors

        from llmfy.exception.exception_handler import handle_google_error

        try:
            response = self.__call_googleai_embedding(model=self.model, text=text)

            if not response.embeddings or len(response.embeddings) == 0:
                raise ValueError("No embedding returned from Google AI")

            embedding = response.embeddings[0].values or []

            return embedding

        except errors.APIError as e:
            raise handle_google_error(e)
        except Exception as e:
            error_message = str(e)
            if "invalid" in error_message.lower():
                logger.error(f"Invalid request: {text[:100]}...")
            else:
                logger.error(f"Google AI API error: {e}")
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
            batch_size (int, optional): Number of texts per batch. Defaults to 10.
            max_retries (int, optional): Maximum retry attempts. Defaults to 3.
            retry_delay (float, optional): Delay between retries in seconds. Defaults to 1.0.
            show_progress_bar (bool, optional): Whether to show progress. Defaults to False.

        Returns:
            NDArray[Any]: Array of embeddings
        """
        from google.genai import errors

        if np is None:
            raise LLMfyException(
                "`encode_batch` operation is using numpy, numpy package is not installed. "
                'Install it using `pip install "llmfy[numpy]"`'
            )

        if isinstance(texts, str):
            texts = [texts]

        embeddings = []

        if show_progress_bar:
            logger.info(f"Generating embeddings for {len(texts)} texts...")

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]

            if show_progress_bar:
                logger.info(
                    f"Processing batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}"
                )

            batch_embeddings = []
            for text in batch_texts:
                for attempt in range(max_retries):
                    try:
                        embedding = self.encode(text)
                        batch_embeddings.append(embedding)
                        break
                    except errors.APIError as e:
                        if e.code == 429:
                            if attempt < max_retries - 1:
                                wait_time = retry_delay * (2**attempt)  # Exponential backoff
                                logger.warning(
                                    f"Rate limited, waiting {wait_time}s before retry..."
                                )
                                time.sleep(wait_time)
                                continue
                            logger.error(f"Rate limit error after {max_retries} attempts: {e}")
                            raise
                        logger.error(f"Error processing text: {e}")
                        raise
                    except Exception as e:
                        logger.error(f"Unexpected error: {e}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        raise

            embeddings.extend(batch_embeddings)

            # Small delay between batches to avoid rate limits
            if i + batch_size < len(texts):
                time.sleep(0.1)

        return np.array(embeddings)
