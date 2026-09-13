import os
import time

from llmfy import LLMfyException
from llmfy.llmfy_core.embeddings.base_embedding_model import BaseEmbeddingModel
from llmfy.llmfy_core.service_provider import ServiceProvider
from llmfy.llmfy_utils.logger.llmfy_logger import LLMfyLogger

try:
    import openai
except ImportError:
    openai = None

try:
    import numpy as np
except ImportError:
    np = None

logger = LLMfyLogger("LLMfy").get_logger()


class OpenAIEmbedding(BaseEmbeddingModel):
    """OpenAI embedding client."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        """
        Initialize OpenAI embeddings client

        Args:
            model (str): Model name for OpenAI embeddings. Defaults to "text-embedding-3-small".
            api_key (str, optional): OpenAI API key. Defaults to the `OPENAI_API_KEY`
                environment variable if not provided.
            base_url (str, optional): Base URL for the OpenAI API. Defaults to None,
                which uses the OpenAI SDK's default base URL.
        """

        if openai is None:
            raise LLMfyException(
                'openai package is not installed. Install it using `pip install "llmfy[openai]"`'
            )
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMfyException(
                "Please provide `OPENAI_API_KEY` on your environment or pass `api_key`!"
            )

        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.provider = ServiceProvider.OPENAI
        self.model = model

    def __call_openai_embedding(self, model: str, text: str | list[str]):
        from llmfy.llmfy_core.llms.openai.chat.openai_chat_usage import (
            track_openai_embedding_usage,
        )

        @track_openai_embedding_usage
        def _call_openai_impl(model: str, text: str | list[str]):
            response = self.client.embeddings.create(
                model=model,
                input=text,
                encoding_format="float",
            )
            return response

        return _call_openai_impl(model, text)

    def encode(self, text: str) -> list[float]:
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
                logger.error(f"Rate limit exceeded: {e}")
            elif "invalid" in error_message.lower():
                logger.error(f"Invalid request: {text[:100]}...")
            else:
                logger.error(f"OpenAI API error: {e}")
            raise e

    def encode_batch(
        self,
        texts: list[str] | str,
        batch_size: int = 100,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        show_progress_bar: bool = False,
    ):
        """
        Encode texts into embedding with batch process.

        Each chunk of `batch_size` texts is sent as a single `embeddings.create`
        call (OpenAI's `input` accepts a list of strings natively), instead of
        one HTTP request per text. `batch_size` is now safe to raise (OpenAI
        accepts up to 2048 inputs per request); 100 is a conservative default
        that keeps payloads reasonable while cutting request count ~100x
        compared to one-request-per-text.

        Args:
            texts (List[str] | str): Text(s) to embed
            batch_size (int, optional): Number of texts per request. Defaults to 100.
            max_retries (int, optional): Maximum retry attempts per batch. Defaults to 3.
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
            logger.info(f"Generating embeddings for {len(texts)} texts...")

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]

            if show_progress_bar:
                logger.info(
                    f"Processing batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}"
                )

            batch_embeddings = None
            # Retry logic for the whole batch (one request covers all texts in it)
            for attempt in range(max_retries):
                try:
                    response = self.__call_openai_embedding(
                        model=self.model, text=batch_texts
                    )

                    if not response.data or len(response.data) != len(batch_texts):
                        raise ValueError(
                            f"Expected {len(batch_texts)} embeddings, "
                            f"got {len(response.data) if response.data else 0}"
                        )

                    # Preserve input order via the `index` OpenAI returns per item.
                    sorted_data = sorted(response.data, key=lambda d: d.index)
                    batch_embeddings = [d.embedding for d in sorted_data]
                    break
                except Exception as e:
                    error_message = str(e)
                    if (
                        "rate_limit_exceeded" in error_message.lower()
                        or "rate limit" in error_message.lower()
                    ):
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2**attempt)  # Exponential backoff
                            logger.warning(
                                f"Rate limited, waiting {wait_time}s before retry..."
                            )
                            time.sleep(wait_time)
                            continue
                        logger.error(
                            f"Rate limit error after {max_retries} attempts: {e}"
                        )
                        raise
                    logger.error(f"Error processing batch: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    raise

            if batch_embeddings is None:
                raise ValueError("Failed to obtain embeddings for batch")

            embeddings.extend(batch_embeddings)

            # Small delay between batches to avoid rate limits
            if i + batch_size < len(texts):
                time.sleep(0.1)

        return np.array(embeddings)
