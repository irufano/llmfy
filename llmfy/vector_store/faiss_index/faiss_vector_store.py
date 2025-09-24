import io
import json
import math
import os
import pickle
from typing import Any, Dict, List, Literal, Optional, Tuple

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.llmfy_core.embeddings.base_embedding_model import BaseEmbeddingModel
from llmfy.vector_store.document import Document
from llmfy.vector_store.faiss_index.faiss_index import FAISSIndex

try:
    import faiss
except ImportError:
    faiss = None


try:
    import numpy as np
except ImportError:
    np = None


class FAISSVectorStore:
    def __init__(
        self,
        embedding_client: BaseEmbeddingModel,
        index_type: Optional[Literal["flat", "hnsw", "ivfflat", "ivfpq"]] = None,
    ):
        """
        Initialize FAISS Vector Store.

        Args:
            dim (int): Dimension of vectors.
            index_type (str): Type of FAISS index (flat, ivfflat, hnsw). default to `None`.
        """

        if faiss is None:
            raise LLMfyException(
                'faiss package is not installed. Install it using `pip install "llmfy[faiss-cpu]"`'
            )

        if np is None:
            raise LLMfyException(
                'numpy package is not installed. Install it using `pip install "llmfy[numpy]"`'
            )

        self.index_type: Optional[Literal["flat", "hnsw", "ivfflat", "ivfpq"]] = (
            index_type
        )
        self.faiss_index = None
        self.documents: List[Document] = []
        self.embedding_client = embedding_client
        self.embeddings = None
        self.dim_vectors = None
        self.total_vectors = None
        self.index_configs = None

    def _validate_vectors(self, vectors):
        """
         Validate and ensure vectors are in the correct format.

        Args:
            vectors (np.ndarray): _description_

        Returns:
            np.ndarray: _description_
        """
        if np is None:
            raise LLMfyException(
                'numpy package is not installed. Install it using `pip install "llmfy[numpy]"`'
            )

        if not isinstance(vectors, np.ndarray):
            vectors = np.array(vectors)

        if vectors.dtype != np.float32:
            vectors = vectors.astype(np.float32)

        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)
        return vectors

    def _suggestion_index_type(
        self,
        N: int,
        D: int,
    ) -> Literal["flat", "hnsw", "ivfflat", "ivfpq"]:
        """
        Dynamically choose index type based on dataset/vector size size (N) and dimension (D).

        Args:
            N (int): vector size size.
            D (int): vector dimension.
        """
        if N <= 100_000:
            return "flat"
        elif N <= 1_000_000:
            return "hnsw"
        elif N <= 10_000_000:
            return "ivfflat"
        elif N > 10_000_000:
            return "ivfpq"
        return "flat"

    def _get_index_configs(
        self,
        index_type: Literal["flat", "hnsw", "ivfflat", "ivfpq"],
        N: int,
        D: int,
    ) -> dict[Any, Any]:
        """
        Get dynamic config based on index_type.

        Args:
            index_type (Literal["flat", "hnsw", "ivfflat", "ivfpq"]): FAISS index type.
            N (int): Number of vectors.
            D (int): Dimension.

        Returns:
            _type_: _description_
        """
        configs = {}

        if index_type == "flat":
            pass

        elif index_type == "hnsw":
            configs["M"] = min(64, max(16, D // 2))
            configs["ef_search"] = 2 * configs["M"]

        elif index_type == "ivfflat":
            configs["nlist"] = min(
                max(10, int(4 * math.sqrt(N))), N
            )  # Ensures nlist <= N.
            configs["nprobe"] = max(1, configs["nlist"] // 10)

        elif index_type == "ivfpq":
            configs["nlist"] = min(
                max(10, int(4 * math.sqrt(N))), N
            )  # Ensures nlist <= N.
            configs["nprobe"] = max(1, configs["nlist"] // 10)
            configs["M"] = max(8, D // 4)  # subquantizers
            configs["nbits"] = 8

        return configs

    def encode_documents(
        self,
        documents: List[Document],
        batch_size: int = 5,
    ):
        """
        Encode documents to faiss vector store.

        Args:
            documents (List[Document]): List of text documents.
            batch_size (int): Batch size. default 5.
        """
        if np is None:
            raise LLMfyException(
                'numpy package is not installed. Install it using `pip install "llmfy[numpy]"`'
            )

        self.documents = documents

        # Generate embeddings
        texts = [doc.text for doc in documents]

        embeddings = self.embedding_client.encode_batch(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
        )
        # Normalize embeddings for cosine similarity
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        vectors = self._validate_vectors(embeddings)

        # Add to embeddings
        self.embeddings = vectors

        # Number of vectors (N)
        self.total_vectors = self.embeddings.shape[0]

        # Dimension (D)
        self.dim_vectors = self.embeddings.shape[1]

        print("Number of vectors (N):", self.total_vectors)
        print("Dimension (D):", self.dim_vectors)

        # Create  index
        if self.faiss_index is None:
            if self.index_type is None:
                self.index_type = self._suggestion_index_type(
                    N=self.total_vectors, D=self.dim_vectors
                )

            if self.index_type == "ivfpq":
                if self.total_vectors < 256:
                    raise ValueError(
                        f"Vector size = {self.total_vectors} is less than 256 to use `ivfpq`. Minimum vector size is 256."
                    )

            # Get dynamic index config
            index_configs = self._get_index_configs(
                self.index_type,
                N=self.total_vectors,
                D=self.dim_vectors,
            )
            self.index_configs = index_configs

            self.faiss_index = FAISSIndex(
                dim=self.dim_vectors,
                index_type=self.index_type,
                nlist=index_configs.get("nlist", 0),
                nprobe=index_configs.get("nprobe", 0),
                M=index_configs.get("M", 0),
                ef_search=index_configs.get("ef_search", 0),
                nbits=index_configs.get("nbits", 0),
            )

        # Add embedding to index
        self.faiss_index.add(vectors)

        print(
            f"Successfully added {len(self.documents)} documents to index `{self.index_type}`. \n"
            f"Vectors total: {self.faiss_index.index.ntotal} \n"  # type: ignore
            f"Config: {self.index_configs}"
        )

    def search(
        self,
        query: str,
        k: int = 5,
        score_threshold: float = 0.0,
        nprobe: Optional[int] = None,
        ef_search: Optional[int] = None,
    ) -> List[Tuple[Document, float, int]]:
        """
        Search for similar documents using Bedrock embeddings

        Args:
            query (str): _description_
            k (int, optional): _description_. Defaults to 5.
            score_threshold (float, optional): _description_. Defaults to 0.0.
            nprobe (Optional[int], optional): Tuning nprobe . Defaults to None.
            ef_search (Optional[int], optional): Tuning ef_search. Defaults to None.

        Returns:
            List[Tuple[Document, float, int]]: _description_
        """
        if np is None:
            raise LLMfyException(
                'numpy package is not installed. Install it using `pip install "llmfy[numpy]"`'
            )

        if self.faiss_index is None or len(self.documents) == 0:
            return []

        # Generate query embedding
        query_embedding = self.embedding_client.encode_batch(
            [query], show_progress_bar=False
        )
        # Normalize
        query_embedding = query_embedding / np.linalg.norm(
            query_embedding, axis=1, keepdims=True
        )

        # Search
        scores, indices = self.faiss_index.search(
            query_embedding.astype("float32"),
            k=k,
            nprobe=nprobe,
            ef_search=ef_search,
        )

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if self.faiss_index.index_type == "lsh":
                # LSH is Smaller = more similar.
                condition = score <= score_threshold
            else:
                # IP is Larger = more similar
                condition = score >= score_threshold

            if condition and idx < len(self.documents):
                results.append((self.documents[idx], float(score), int(idx)))

        return results

    def save_to_path(self, path: str):
        """
        Save the FAISS index and metadata separately to disk.
        """
        if faiss is None:
            raise LLMfyException(
                'faiss package is not installed. Install it using `pip install "llmfy[faiss-cpu]"`'
            )

        if np is None:
            raise LLMfyException(
                'numpy package is not installed. Install it using `pip install "llmfy[numpy]"`'
            )

        if self.faiss_index is None:
            raise ValueError(
                "`faiss_index` is not initialize. `encode_documents` or `load` first."
            )

        os.makedirs(path, exist_ok=True)

        # Save FAISS index
        faiss.write_index(self.faiss_index.index, os.path.join(path, "index.faiss"))

        # Save documents
        with open(os.path.join(path, "documents.pkl"), "wb") as f:
            pickle.dump(self.documents, f)

        # Save embeddings
        with open(os.path.join(path, "embeddings.pkl"), "wb") as f:
            pickle.dump(self.embeddings, f)

        # Get metadata fields
        if self.documents:
            doc = self.documents[0]  # Safe access
        else:
            doc = Document(id="", text="")  # Handle empty
        primary_fields = set(doc.__dict__.keys())
        dynamic_fields = set(doc.model_extra.keys()) if doc.model_extra else set()
        metadata = list(primary_fields) + list(dynamic_fields)

        # Save configuration
        config = {
            "dimension": self.dim_vectors,
            "total_vectors": self.total_vectors,
            "index_type": self.index_type,
            "index_configs": self.index_configs,
            "embedding_provider": self.embedding_client.provider,
            "embedding_model": self.embedding_client.model,
            "metadata": metadata,
        }
        config_path = os.path.join(path, "config.json")
        # save config as json for readability
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        # Save config as pkl
        with open(os.path.join(path, "config.pkl"), "wb") as f:
            pickle.dump(config, f)

        print(f"Index saved to {path}")

    def load_from_path(self, path: str):
        """
        Load the FAISS vector store from disk
        """
        if faiss is None:
            raise LLMfyException(
                'faiss package is not installed. Install it using `pip install "llmfy[faiss-cpu]"`'
            )

        # Load config first
        with open(os.path.join(path, "config.pkl"), "rb") as f:
            configs: Dict = pickle.load(f)

        # Set configs
        self.index_type = configs.get("index_type", "flat")
        self.total_vectors = configs.get("total_vectors", 0)
        self.dim_vectors = configs.get("dimension", 0)
        self.index_configs = configs.get("index_configs", {})

        # Load FAISS index
        index = faiss.read_index(os.path.join(path, "index.faiss"))
        self.faiss_index = FAISSIndex(
            index=index,
            dim=self.dim_vectors,
            index_type=self.index_type,  # type: ignore
            nlist=self.index_configs.get("nlist", 0),
            nprobe=self.index_configs.get("nprobe", 0),
            M=self.index_configs.get("M", 0),
            ef_search=self.index_configs.get("ef_search", 0),
            nbits=self.index_configs.get("nbits", 0),
        )

        # Load documents
        with open(os.path.join(path, "documents.pkl"), "rb") as f:
            self.documents = pickle.load(f)

        # Load embeddings
        with open(os.path.join(path, "embeddings.pkl"), "rb") as f:
            self.embeddings = pickle.load(f)

        print(f"Vector store loaded from {path}")
        print(f"Model: {configs['embedding_model']}, Documents: {len(self.documents)}")

    def create_buffers(self) -> dict[Any, Any]:
        """
        Return in-memory buffers for `index.faiss`, `documents.pkl`, `embeddings.pkl`,
        `config.json`, and `config.pkl`.

        Returns:
            dict[str, io.BytesIO]: Dictionary of filename → buffer
        """
        if faiss is None:
            raise LLMfyException(
                'faiss package is not installed. Install it using `pip install "llmfy[faiss-cpu]"`'
            )

        if self.faiss_index is None:
            raise ValueError(
                "`faiss_index` is not initialized. Run `encode_documents` or `load` first."
            )

        buffers = {}

        # FAISS index
        faiss_bytes = faiss.serialize_index(self.faiss_index.index)
        buffers["index.faiss"] = io.BytesIO(faiss_bytes)

        # Documents
        doc_buffer = io.BytesIO()
        pickle.dump(self.documents, doc_buffer)
        doc_buffer.seek(0)
        buffers["documents.pkl"] = doc_buffer

        # Embeddings
        emb_buffer = io.BytesIO()
        pickle.dump(self.embeddings, emb_buffer)
        emb_buffer.seek(0)
        buffers["embeddings.pkl"] = emb_buffer

        # Config
        if self.documents:
            doc = self.documents[0]
        else:
            doc = Document(id="", text="")

        primary_fields = set(doc.__dict__.keys())
        dynamic_fields = set(doc.model_extra.keys()) if doc.model_extra else set()
        metadata = list(primary_fields) + list(dynamic_fields)

        config = {
            "dimension": self.dim_vectors,
            "total_vectors": self.total_vectors,
            "index_type": self.index_type,
            "index_configs": self.index_configs,
            "embedding_provider": self.embedding_client.provider,
            "embedding_model": self.embedding_client.model,
            "metadata": metadata,
        }

        # JSON config
        json_buffer = io.BytesIO(json.dumps(config, indent=2).encode("utf-8"))
        buffers["config.json"] = json_buffer

        # Pickle config
        config_buffer = io.BytesIO()
        pickle.dump(config, config_buffer)
        config_buffer.seek(0)
        buffers["config.pkl"] = config_buffer

        return buffers

    def load_from_buffers(self, buffers: dict):
        """
        Load the FAISS vector store from in-memory buffers (e.g., from S3).

        Args:
            buffers (dict[str, io.BytesIO]): Dictionary mapping filename -> BytesIO buffer
        """
        if faiss is None:
            raise LLMfyException(
                'faiss package is not installed. Install it using `pip install "llmfy[faiss-cpu]"`'
            )

        if np is None:
            raise LLMfyException(
                'numpy package is not installed. Install it using `pip install "llmfy[numpy]"`'
            )

        # Load config
        configs = pickle.load(buffers["config.pkl"])

        # Set configs
        self.index_type = configs.get("index_type", "flat")
        self.total_vectors = configs.get("total_vectors", 0)
        self.dim_vectors = configs.get("dimension", 0)
        self.index_configs = configs.get("index_configs", {})

        # Load FAISS index
        index_buffer = buffers["index.faiss"].getvalue()
        np_data = np.frombuffer(index_buffer, dtype=np.uint8)
        index = faiss.deserialize_index(np_data)
        self.faiss_index = FAISSIndex(
            index=index,
            dim=self.dim_vectors,
            index_type=self.index_type,  # type: ignore
            nlist=self.index_configs.get("nlist", 0),
            nprobe=self.index_configs.get("nprobe", 0),
            M=self.index_configs.get("M", 0),
            ef_search=self.index_configs.get("ef_search", 0),
            nbits=self.index_configs.get("nbits", 0),
        )

        # Load documents
        self.documents = pickle.load(buffers["documents.pkl"])

        # Load embeddings
        self.embeddings = pickle.load(buffers["embeddings.pkl"])

        print("Vector store loaded from buffers")
        print(f"Model: {configs['embedding_model']}, Documents: {len(self.documents)}")
