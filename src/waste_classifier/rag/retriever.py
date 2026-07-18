"""TF-IDF based retriever over the recycling knowledge base.

A lightweight, dependency-friendly retrieval approach: TF-IDF vectors +
cosine similarity over a small, curated knowledge base. Deliberately avoids
a heavy sentence-embedding model (e.g. sentence-transformers/torch) since the
knowledge base is small and a full neural embedding model would add a large
dependency/deploy cost for negligible quality gain at this scale. Swapping in
a proper embedding model + vector DB (FAISS/Chroma) is a natural upgrade path
if the knowledge base grows significantly.
"""

from __future__ import annotations

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from waste_classifier import config
from waste_classifier.rag.knowledge_base import Chunk, load_knowledge_base


@dataclass
class RetrievedChunk:
    chunk: Chunk
    score: float


class KnowledgeRetriever:
    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix = None

    def build(self) -> None:
        self._chunks = load_knowledge_base()
        texts = [f"{c.heading}\n{c.text}" for c in self._chunks]
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = self._vectorizer.fit_transform(texts)

    @property
    def is_ready(self) -> bool:
        return self._vectorizer is not None

    def retrieve(self, query: str, top_k: int = config.RAG_TOP_K) -> list[RetrievedChunk]:
        if not self.is_ready:
            raise RuntimeError("Retriever is not built. Call build() first.")

        query_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self._matrix)[0]
        ranked_idx = scores.argsort()[::-1][:top_k]

        return [
            RetrievedChunk(chunk=self._chunks[i], score=round(float(scores[i]), 4))
            for i in ranked_idx
            if scores[i] > 0
        ]


# Module-level singleton used by the API layer.
retriever = KnowledgeRetriever()
