"""Unit tests for llmfy/llmfy_core/embeddings/openai/openai_embedding.py."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import llmfy.llmfy_core.embeddings.openai.openai_embedding as openai_embedding_module
from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.embeddings.openai.openai_embedding import OpenAIEmbedding
from llmfy.llmfy_core.service_provider import ServiceProvider


def make_embedding_response(vectors: list[list[float]]):
    data = [SimpleNamespace(embedding=v, index=i) for i, v in enumerate(vectors)]
    return SimpleNamespace(
        data=data, usage=SimpleNamespace(prompt_tokens=10, total_tokens=10)
    )


@pytest.fixture
def embedding(provider_api_keys) -> OpenAIEmbedding:
    return OpenAIEmbedding()


class TestConstruction:
    def test_sets_provider_and_default_model(self, embedding: OpenAIEmbedding):
        assert embedding.provider == ServiceProvider.OPENAI
        assert embedding.model == "text-embedding-3-small"

    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(LLMfyException, match="OPENAI_API_KEY"):
            OpenAIEmbedding()

    def test_raises_when_openai_package_missing(self, provider_api_keys, monkeypatch):
        monkeypatch.setattr(openai_embedding_module, "openai", None)
        with pytest.raises(LLMfyException, match="openai package is not installed"):
            OpenAIEmbedding()


class TestEncode:
    def test_returns_embedding_vector(self, embedding: OpenAIEmbedding):
        embedding.client.embeddings.create = MagicMock(
            return_value=make_embedding_response([[0.1, 0.2, 0.3]])
        )
        result = embedding.encode("hello")
        assert result == [0.1, 0.2, 0.3]

    def test_empty_response_raises_value_error(self, embedding: OpenAIEmbedding):
        embedding.client.embeddings.create = MagicMock(
            return_value=SimpleNamespace(data=[], usage=None)
        )
        with pytest.raises(ValueError, match="No embedding returned"):
            embedding.encode("hello")

    def test_underlying_error_propagates_unwrapped(self, embedding: OpenAIEmbedding):
        embedding.client.embeddings.create = MagicMock(
            side_effect=RuntimeError("network down")
        )
        with pytest.raises(RuntimeError):
            embedding.encode("hello")


class TestEncodeBatch:
    def test_requires_numpy(self, embedding: OpenAIEmbedding, monkeypatch):
        monkeypatch.setattr(openai_embedding_module, "np", None)
        with pytest.raises(LLMfyException, match="numpy"):
            embedding.encode_batch(["a", "b"])

    def test_single_string_is_wrapped_in_list(self, embedding: OpenAIEmbedding):
        embedding.client.embeddings.create = MagicMock(
            return_value=make_embedding_response([[1.0, 2.0]])
        )
        result = embedding.encode_batch("only one")
        assert result.shape == (1, 2)

    def test_batches_respect_batch_size(self, embedding: OpenAIEmbedding):
        call_sizes = []

        def fake_create(model, input, encoding_format):
            call_sizes.append(len(input))
            return make_embedding_response([[float(i)] for i in range(len(input))])

        embedding.client.embeddings.create = MagicMock(side_effect=fake_create)
        texts = [f"text-{i}" for i in range(5)]
        result = embedding.encode_batch(texts, batch_size=2)
        assert call_sizes == [2, 2, 1]
        assert result.shape == (5, 1)

    def test_preserves_input_order_via_response_index(self, embedding: OpenAIEmbedding):
        # OpenAI can return embeddings out of order; encode_batch must
        # re-sort by the `index` field before returning.
        def fake_create(model, input, encoding_format):
            data = [
                SimpleNamespace(embedding=[1.0], index=1),
                SimpleNamespace(embedding=[0.0], index=0),
            ]
            return SimpleNamespace(data=data, usage=None)

        embedding.client.embeddings.create = MagicMock(side_effect=fake_create)
        result = embedding.encode_batch(["a", "b"], batch_size=2)
        assert list(result[:, 0]) == [0.0, 1.0]

    def test_mismatched_response_length_raises_value_error(
        self, embedding: OpenAIEmbedding
    ):
        embedding.client.embeddings.create = MagicMock(
            return_value=make_embedding_response([[1.0]])  # only 1, expected 2
        )
        with pytest.raises(ValueError, match="Expected 2 embeddings"):
            embedding.encode_batch(["a", "b"], batch_size=10, max_retries=1)

    def test_retries_on_rate_limit_then_succeeds(
        self, embedding: OpenAIEmbedding, monkeypatch
    ):
        monkeypatch.setattr(openai_embedding_module.time, "sleep", lambda _: None)  # type: ignore
        attempts = {"n": 0}

        def fake_create(model, input, encoding_format):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise RuntimeError("rate_limit_exceeded: slow down")
            return make_embedding_response([[1.0]])

        embedding.client.embeddings.create = MagicMock(side_effect=fake_create)
        result = embedding.encode_batch(["a"], batch_size=10, max_retries=3)
        assert attempts["n"] == 2
        assert result.shape == (1, 1)

    def test_gives_up_after_max_retries_on_persistent_rate_limit(
        self, embedding: OpenAIEmbedding, monkeypatch
    ):
        monkeypatch.setattr(openai_embedding_module.time, "sleep", lambda _: None)  # type: ignore
        embedding.client.embeddings.create = MagicMock(
            side_effect=RuntimeError("rate limit exceeded")
        )
        with pytest.raises(RuntimeError, match="rate limit"):
            embedding.encode_batch(["a"], batch_size=10, max_retries=2)
        assert embedding.client.embeddings.create.call_count == 2
