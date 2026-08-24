"""Persistence schema for scans and chat turns.

Written to be Postgres-compatible (only plain types: str, int, float, bool,
datetime) so Phase 4's production deploy only needs to change `DATABASE_URL`,
not this schema.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Scan(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=_utcnow)
    session_id: str = Field(index=True)  # anonymous UUID, client-generated, stored in localStorage
    mode: str  # "upload" | "camera" | "multi"
    predicted_label: str
    confidence: float
    all_probabilities: str  # JSON-encoded dict
    latency_ms: int
    image_hash: str  # SHA-256 of the uploaded bytes -- never store the image itself
    feedback_label: str | None = None
    feedback_at: datetime | None = None


class ChatTurn(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=_utcnow)
    session_id: str = Field(index=True)
    mode: str  # "rag" | "agent"
    question: str
    tools_used: str | None = None  # JSON-encoded list, agent mode only
    latency_ms: int
    language: str
