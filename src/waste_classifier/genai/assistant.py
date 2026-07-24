"""Recycling assistant: RAG over the knowledge base + Groq chat completion."""

from __future__ import annotations

from collections.abc import Iterator

from waste_classifier import config
from waste_classifier.genai.groq_client import get_client
from waste_classifier.rag import retriever

SYSTEM_PROMPT = """\
You are a helpful, concise recycling assistant embedded in a waste-classification app.
Answer questions about recycling, waste disposal, and sustainability using the
provided context snippets when relevant. If the context doesn't cover the question,
answer from general recycling knowledge, but say so if you're not fully sure.
Keep answers short and practical (2-5 sentences unless the user asks for detail).
Never invent local regulations — recommend checking the user's local waste authority
for anything jurisdiction-specific.
"""


def _build_context_block(question: str) -> str:
    if not retriever.is_ready:
        return ""
    matches = retriever.retrieve(question)
    if not matches:
        return ""
    parts = [f"[{m.chunk.doc_id} — {m.chunk.heading}]\n{m.chunk.text}" for m in matches]
    return "\n\n".join(parts)


def _build_messages(
    question: str,
    classification_label: str | None,
    history: list[dict] | None,
    language: str = "en",
) -> list[dict]:
    context = _build_context_block(question)

    context_note = f"\n\nRelevant knowledge base context:\n{context}" if context else ""
    classification_note = (
        f"\n\nThe user's uploaded image was classified as: {classification_label}."
        if classification_label
        else ""
    )
    language_note = (
        "\n\nRespond in Urdu (اردو), regardless of what language the knowledge base "
        "context above is written in."
        if language == "ur"
        else ""
    )

    system_content = SYSTEM_PROMPT + classification_note + context_note + language_note
    messages = [{"role": "system", "content": system_content}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": question})
    return messages


def ask(
    question: str,
    classification_label: str | None = None,
    history: list[dict] | None = None,
    language: str = "en",
) -> str:
    """Non-streaming chat completion (used by tests and simple clients)."""
    client = get_client()
    response = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=_build_messages(question, classification_label, history, language),
        temperature=0.4,
    )
    return response.choices[0].message.content


def ask_stream(
    question: str,
    classification_label: str | None = None,
    history: list[dict] | None = None,
    language: str = "en",
) -> Iterator[str]:
    """Streaming chat completion — yields text chunks as they arrive from Groq."""
    client = get_client()
    stream = client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=_build_messages(question, classification_label, history, language),
        temperature=0.4,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
