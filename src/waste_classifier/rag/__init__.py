"""Selects the RAG retriever implementation based on config.RAG_BACKEND.

Kept in __init__.py (rather than importing retriever.py directly everywhere)
so that in "tfidf" mode, the heavy embeddings module — which imports torch and
sentence-transformers at module level — is never even imported. That matters
for the lightweight deployment profile, which doesn't install those packages
at all (see requirements-lite.txt).
"""

from waste_classifier import config

if config.RAG_BACKEND == "tfidf":
    from waste_classifier.rag.lightweight_retriever import (
        LightweightKnowledgeRetriever as _RetrieverCls,
    )
else:
    from waste_classifier.rag.retriever import KnowledgeRetriever as _RetrieverCls

retriever = _RetrieverCls()
