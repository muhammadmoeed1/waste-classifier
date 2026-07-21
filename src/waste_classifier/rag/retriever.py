"""Embedding-based retriever over the recycling knowledge base.

Each knowledge base chunk is embedded once (at startup) with a small sentence-
transformer model, then indexed in a FAISS flat index for cosine-similarity
search. This replaces an earlier TF-IDF/keyword implementation with genuine
dense vector search: it matches paraphrased or loosely-worded questions
("is it okay to toss a used bottle in with paper?") to the right knowledge
chunk even when they share few exact words with the source text, which pure
keyword matching cannot do.
"""

from __future__ import annotations

from dataclasses import dataclass

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from waste_classifier import config
from waste_classifier.rag.knowledge_base import Chunk, load_knowledge_base

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float


class KnowledgeRetriever:
    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._model: SentenceTransformer | None = None
        self._index: faiss.Index | None = None

    def build(self) -> None:
        self._chunks = load_knowledge_base()
        texts = [f"{c.heading}\n{c.text}" for c in self._chunks]

        self._model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        embeddings = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        embeddings = np.asarray(embeddings, dtype=np.float32)

        # Cosine similarity via inner product on L2-normalized vectors.
        self._index = faiss.IndexFlatIP(embeddings.shape[1])
        self._index.add(embeddings)

    @property
    def is_ready(self) -> bool:
        return self._index is not None

    def retrieve(self, query: str, top_k: int = config.RAG_TOP_K) -> list[RetrievedChunk]:
        if not self.is_ready:
            raise RuntimeError("Retriever is not built. Call build() first.")

        query_vec = self._model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        query_vec = np.asarray(query_vec, dtype=np.float32)

        scores, indices = self._index.search(query_vec, top_k)

        return [
            RetrievedChunk(chunk=self._chunks[idx], score=round(float(score), 4))
            for score, idx in zip(scores[0], indices[0])
            if idx >= 0 and score > 0
        ]


# Module-level singleton used by the API layer.
retriever = KnowledgeRetriever()
