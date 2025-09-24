from typing import Any, Literal, Optional

from llmfy.exception.llmfy_exception import LLMfyException

try:
    import faiss
except ImportError:
    faiss = None

try:
    import numpy as np
except ImportError:
    np = None


class FAISSIndex:
    def __init__(
        self,
        dim: int,
        index_type: Literal["flat", "hnsw", "lsh", "ivfflat", "ivfpq"] = "flat",
        nlist: int = 100,
        nprobe: int = 10,
        M: int = 32,
        ef_search: int = 50,
        nbits: int = 8,
        index: Optional[Any] = None,
    ):
        """
        Initialize FAISS Index.

        Args:
            dim (int): Dimension of vectors.

            index_type (str): Type of FAISS index (flat, ivfflat, ivfpq, hnsw, lsh).

            nlist (int): Number of clusters (for ivfflat and ivfpq).
                Higher nlist → finer partition, better recall, but more memory and slower training.
                Lower nlist → faster but worse recall.
                Depends on vectors? Yes → set relative to dataset size, depends on dataset size, larger datasets need higher nlist.
                Retraining? Yes. Changing nlist requires re-training and rebuilding index.
                Tunable at query time? ❌ No.
                Rule of thumb:
                    - nlist ≈ √N (where N is the number of vectors),
                    - Example: For 1M vectors → nlist ~ 1000.

            nprobe (int): Number of clusters to search (for ivfflat and ivfpq).
                Higher nprobe → better recall, slower search.
                Lower nprobe → faster, but may miss good neighbors.
                Depends on vectors? No → only affects search speed/recall.
                Retraining? No.
                Tunable at query time? ✅ Yes.
                Rule of thumb:
                    - Start with nprobe = 1–10% of nlist,
                    - Example: nlist = 1000 → nprobe = 10–50.

            M (int): Number of neighbors per node in the HNSW graph (for hnsw).
                Higher M → better recall, more memory, longer build time.
                Lower M → smaller memory, but lower recall.
                Depends on vectors? Not directly, but larger datasets usually benefit from higher M.
                Retraining? Yes → must rebuild graph if M changes.
                Tunable at query time? ❌ No.
                Rule of thumb:
                    - Typical range: 16–64,
                    - M = 32 is a common good default.

            ef_search (int): Size of candidate list during search (search depth) (for hnsw).
                Higher ef_search → better recall, slower query.
                Lower ef_search → faster, but may miss true neighbors.
                Depends on vectors? No.
                Retraining? No.
                Tunable at query time? ✅ Yes.
                Rule of thumb:
                    - Set ef_search around k * 2–10 (where k is top neighbors).
                    - Example: for k=10, ef_search=50 is common.

            nbits (int): Number of bits  per vector used for hashing (for lsh).
                Higher nbits → more fine-grained buckets, better recall, but more memory.
                Lower nbits → fewer buckets, faster, but worse recall.
                Depends on vectors? Yes → tied to dimension.
                Retraining? Yes → index must be rebuilt if nbits changes.
                Tunable at query time? ❌ No.
                Rule of thumb:
                    - Often nbits = 2 * dim or less.
                    - Example: for dim=128, try nbits=128 or nbits=256.


        """

        if faiss is None:
            raise LLMfyException(
                'faiss package is not installed. Install it using `pip install "llmfy[faiss-cpu]"`'
            )

        if np is None:
            raise LLMfyException(
                'numpy package is not installed. Install it using `pip install "llmfy[numpy]"`'
            )

        self.dim = dim
        self.index_type = index_type.lower()
        self.index = (
            self._create_index(dim, self.index_type, nlist, M, nbits)
            if not index
            else index
        )

        # IVF params
        self.nprobe = nprobe
        if "ivfflat" in self.index_type:
            self.index.nprobe = nprobe  # type: ignore

        # HNSW params
        self.ef_search = ef_search
        if "hnsw" in self.index_type:
            self.index.hnsw.efSearch = ef_search  # type: ignore

    def _create_index(
        self,
        dim: int,
        index_type: str,
        nlist: int,
        M: int,
        nbits: int,
    ):
        if faiss is None:
            raise LLMfyException(
                'faiss package is not installed. Install it using `pip install "llmfy[faiss-cpu]"`'
            )

        if np is None:
            raise LLMfyException(
                'numpy package is not installed. Install it using `pip install "llmfy[numpy]"`'
            )

        # Use IP (Inner Product / Cosine Similarity) best for semantic search, retrieval, RAG
        # with embeddings from models like Bedrock Titan, OpenAI, Cohere, etc.
        if index_type == "flat":
            return faiss.IndexFlatIP(dim)
        elif index_type == "hnsw":
            return faiss.IndexHNSWFlat(dim, M, faiss.METRIC_INNER_PRODUCT)
        elif index_type == "lsh":
            return faiss.IndexLSH(dim, nbits)
        elif index_type == "ivfflat":
            quantizer = faiss.IndexFlatIP(dim)
            return faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_INNER_PRODUCT)
        elif index_type == "ivfpq":
            quantizer = faiss.IndexFlatIP(dim)
            return faiss.IndexIVFPQ(
                quantizer, dim, nlist, M, nbits, faiss.METRIC_INNER_PRODUCT
            )
        else:
            raise ValueError(f"Unsupported index type: {index_type}")

    def train(self, vectors):
        """
        Train the index (required for IVF).

        Args:
            vectors (np.ndarray): _description_
        """
        self.index.train(vectors)  # type: ignore

    def add(self, vectors):
        """
        Add vectors to the index.

        Args:
            vectors (np.ndarray): _description_

        Raises:
            ValueError: _description_
        """
        if not self.index:
            raise ValueError("Index not initialized.")

        # Check train if is_trained is false
        if not self.index.is_trained:
            self.train(vectors)

        self.index.add(vectors)  # type: ignore

    def search(
        self,
        query,
        k: int = 5,
        nprobe: Optional[int] = None,
        ef_search: Optional[int] = None,
    ):
        """
        Search the index.

        Args:
            query (np.ndarray): _description_
            k (int, optional): _description_. Defaults to 5.
            nprobe (Optional[int], optional): _description_. Defaults to None.
            ef_search (Optional[int], optional): _description_. Defaults to None.

        Returns:
            distances (np.ndarray), indices (np.ndarray)
        """
        # Tuning HNSW params
        if "hnsw" in self.index_type:
            if ef_search:
                self.index.hnsw.efSearch = ef_search  # type: ignore
            else:
                self.index.hnsw.efSearch = self.ef_search  # type: ignore

        # Tuning IVF params
        if "ivfflat" in self.index_type:
            if nprobe:
                self.index.nprobe = nprobe  # type: ignore
            else:
                self.index.nprobe = self.nprobe  # type: ignore

        distances, indices = self.index.search(query, k)  # type: ignore
        return distances, indices

    def save(self, path: str):
        """
        Save the FAISS index to disk.
        """
        if faiss is None:
            raise LLMfyException(
                'faiss package is not installed. Install it using `pip install "llmfy[faiss-cpu]"`'
            )

        faiss.write_index(self.index, path)

    def load(self, path: str):
        """
        Load the FAISS index from disk.
        """
        if faiss is None:
            raise LLMfyException(
                'faiss package is not installed. Install it using `pip install "llmfy[faiss-cpu]"`'
            )

        self.index = faiss.read_index(path)
