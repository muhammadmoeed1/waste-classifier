from waste_classifier.rag.lightweight_retriever import LightweightKnowledgeRetriever


def test_lightweight_retriever_builds_and_retrieves():
    r = LightweightKnowledgeRetriever()
    assert r.is_ready is False

    r.build()
    assert r.is_ready is True

    results = r.retrieve("Can I recycle a plastic bottle with sauce in it?", top_k=3)
    assert len(results) > 0
    assert any(res.chunk.doc_id == "plastic" for res in results)


def test_lightweight_retriever_scores_are_descending():
    r = LightweightKnowledgeRetriever()
    r.build()

    results = r.retrieve("glass bottle recycling", top_k=5)
    scores = [res.score for res in results]
    assert scores == sorted(scores, reverse=True)


def test_rag_selector_uses_tfidf_backend_when_configured(monkeypatch):
    import importlib

    from waste_classifier import config

    monkeypatch.setattr(config, "RAG_BACKEND", "tfidf")

    import waste_classifier.rag as rag_module

    importlib.reload(rag_module)
    try:
        assert type(rag_module.retriever).__name__ == "LightweightKnowledgeRetriever"
    finally:
        monkeypatch.setattr(config, "RAG_BACKEND", "embeddings")
        importlib.reload(rag_module)
