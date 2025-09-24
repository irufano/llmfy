import json
import os
import time
from typing import List

from llmfy import LLMfyException
from llmfy.llmfy_core.embeddings.base_embedding_model import BaseEmbeddingModel
from llmfy.llmfy_core.service_provider import ServiceProvider

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None

try:
    import numpy as np
except ImportError:
    np = None


class BedrockEmbedding(BaseEmbeddingModel):
    """AWS Bedrock embedding client."""

    def __init__(
        self,
        model: str,
    ):
        """
        Initialize Bedrock embeddings client

        Args:
            model (str): Model id embedding on bedrock.
        """

        if boto3 is None:
            raise LLMfyException(
                'boto3 package is not installed. Install it using `pip install "llmfy[boto3]"`'
            )

        if not os.getenv("AWS_ACCESS_KEY_ID"):
            raise LLMfyException(
                "Please provide `AWS_ACCESS_KEY_ID` on your environment!"
            )
        if not os.getenv("AWS_SECRET_ACCESS_KEY"):
            raise LLMfyException(
                "Please provide `AWS_SECRET_ACCESS_KEY` on your environment!"
            )
        if not os.getenv("AWS_BEDROCK_REGION"):
            raise LLMfyException(
                "Please provide `AWS_BEDROCK_REGION` on your environment!"
            )

        self.provider = ServiceProvider.BEDROCK
        self.model = model
        self.client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_BEDROCK_REGION"),
        )

    def __call_bedrock_embedding(self, model: str, body: str):
        from llmfy.llmfy_core.usage.usage_tracker import track_bedrock_embedding_usage

        @track_bedrock_embedding_usage
        def _call_bedrock_impl(model: str, body: str):
            response = self.client.invoke_model(
                body=body,
                modelId=model,
                accept="application/json",
                contentType="application/json",
            )
            return response

        return _call_bedrock_impl(model, body)

    def encode(self, text: str) -> List[float]:
        """
        Get embedding for a single text

        Args:
            text (str): text to embed

        Raises:
            ValueError: _description_
            e: _description_

        Returns:
            List[float]: _description_
        """
        # Prepare the request body bedrock embedding
        body = json.dumps({"inputText": text})

        try:
            # Call Bedrock
            response = self.__call_bedrock_embedding(model=self.model, body=body)

            # Parse response
            response_body = json.loads(response["body"].read())
            embedding = response_body.get("embedding", [])

            if not embedding:
                raise ValueError("No embedding returned from Bedrock")

            return embedding

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ValidationException":
                print(f"Input text too long or invalid: {text[:100]}...")
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
        Encode texts into embedding with batch prosess.

        Args:
            texts (List[str] | str): _description_
            batch_size (int, optional): _description_. Defaults to 10.
            show_progress_bar (bool, optional): _description_. Defaults to True.
            max_retries (int, optional): _description_. Defaults to 3.
            retry_delay (float, optional): _description_. Defaults to 1.0.

        Returns:
            NDArray[Any]: _description_
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
                    except ClientError as e:
                        error_code = e.response["Error"]["Code"]
                        if error_code == "ThrottlingException":
                            if attempt < max_retries - 1:
                                wait_time = retry_delay * (
                                    2**attempt
                                )  # Exponential backoff
                                print(
                                    f"Rate limited, waiting {wait_time}s before retry..."
                                )
                                time.sleep(wait_time)
                                continue
                        print(f"Error processing text: {e}")
                        raise
                    except Exception as e:
                        print(f"Unexpected error: {e}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        raise

            embeddings.extend(batch_embeddings)

            # Small delay between batches to avoid rate limits
            if i + batch_size < len(texts):
                time.sleep(0.1)

        return np.array(embeddings)
