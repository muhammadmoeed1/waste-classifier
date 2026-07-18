from waste_classifier.rag.knowledge_base import load_knowledge_base
from waste_classifier.rag.retriever import KnowledgeRetriever


def test_knowledge_base_loads_chunks():
    chunks = load_knowledge_base()
    assert len(chunks) > 5
    doc_ids = {c.doc_id for c in chunks}
    assert "plastic" in doc_ids
    assert "glass" in doc_ids


def test_retriever_returns_relevant_chunk_for_plastic_question():
    retriever = KnowledgeRetriever()
    retriever.build()

    results = retriever.retrieve("Can I recycle a plastic bottle with sauce in it?", top_k=3)

    assert len(results) > 0
    assert any(r.chunk.doc_id == "plastic" for r in results)


def test_retriever_scores_are_descending():
    retriever = KnowledgeRetriever()
    retriever.build()

    results = retriever.retrieve("glass bottle recycling", top_k=5)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
