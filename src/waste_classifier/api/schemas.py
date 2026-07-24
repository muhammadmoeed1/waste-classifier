"""Pydantic request/response models for the API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EnvironmentalImpact(BaseModel):
    headline: str
    co2_saved_per_kg: float | None = Field(
        None, description="Approximate kg CO2e saved per kg recycled vs. virgin production"
    )
    energy_saved_pct: int | None = Field(
        None, description="Approximate % energy saved vs. producing from raw material"
    )
    fact: str


class PredictionResponse(BaseModel):
    label: str
    confidence: float = Field(..., description="Confidence of the top prediction, as a percentage")
    recyclable: bool
    probabilities: dict[str, float] = Field(
        ..., description="Predicted probability (%) for every class"
    )
    gradcam_image: str | None = Field(
        None, description="Base64 PNG data URI: Grad-CAM heatmap showing where the model looked"
    )
    impact: EnvironmentalImpact | None = Field(
        None, description="Approximate environmental impact of recycling this category"
    )


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    classification_label: str | None = None
    history: list[ChatMessage] = Field(default_factory=list)
    language: str = Field("en", description="Response language: 'en' or 'ur' (Urdu)")


class ChatResponse(BaseModel):
    answer: str


class ToolCall(BaseModel):
    name: str
    arguments: str


class AgentResponse(BaseModel):
    answer: str
    tools_used: list[ToolCall] = Field(
        default_factory=list, description="Tools the agent called, in order, to answer"
    )


class TranscriptionResponse(BaseModel):
    text: str


class DetectionItem(BaseModel):
    box: list[int] = Field(..., description="[x, y, width, height] in original image pixels")
    label: str
    confidence: float
    recyclable: bool


class DetectResponse(BaseModel):
    detections: list[DetectionItem]
    annotated_image: str = Field(..., description="Base64 PNG data URI with drawn bounding boxes")


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    retriever_ready: bool
    groq_configured: bool
