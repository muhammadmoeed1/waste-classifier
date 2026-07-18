"""Pydantic request/response models for the API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    label: str
    confidence: float = Field(..., description="Confidence of the top prediction, as a percentage")
    recyclable: bool
    probabilities: dict[str, float] = Field(
        ..., description="Predicted probability (%) for every class"
    )


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    classification_label: str | None = None
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    retriever_ready: bool
    groq_configured: bool
