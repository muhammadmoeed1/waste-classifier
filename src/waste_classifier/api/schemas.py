"""Pydantic request/response models for the API."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from waste_classifier import config


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
    scan_id: int | None = Field(
        None, description="Persisted Scan row id, used to submit feedback on this prediction"
    )


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    classification_label: str | None = None
    history: list[ChatMessage] = Field(default_factory=list)
    language: str = Field("en", description="Response language: 'en' or 'ur' (Urdu)")

    @field_validator("history")
    @classmethod
    def _cap_history_length(cls, value: list[ChatMessage]) -> list[ChatMessage]:
        """Keep only the most recent messages, so a client can't push
        unbounded history into the LLM's token budget (and cost)."""
        limit = config.MAX_CHAT_HISTORY_MESSAGES
        if len(value) > limit:
            return value[-limit:]
        return value


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


class FeedbackRequest(BaseModel):
    corrected_label: str = Field(..., description="The waste category the user says is correct")


class FeedbackResponse(BaseModel):
    scan_id: int
    feedback_label: str


class ConfusionCell(BaseModel):
    predicted: str
    corrected: str
    count: int


class LatencyPoint(BaseModel):
    created_at: str = Field(..., description="ISO 8601 timestamp")
    mode: str
    latency_ms: int


class StatsResponse(BaseModel):
    total_scans: int
    class_distribution: dict[str, int] = Field(
        ..., description="Count of scans per predicted label"
    )
    mean_confidence: float
    recyclable_pct: float = Field(..., description="% of scans predicted as a recyclable class")
    latency_p50_ms: float
    latency_p95_ms: float
    confidence_histogram: list[int] = Field(
        ..., description="Scan counts in 10 buckets of 10 percentage points each, 0-100%"
    )
    training_distribution_pct: dict[str, float] = Field(
        ..., description="Reference: % class share in the TrashNet validation split"
    )
    confusion_matrix: list[ConfusionCell] = Field(
        default_factory=list, description="predicted vs. feedback_label counts, from corrections"
    )
    latency_points: list[LatencyPoint] = Field(
        default_factory=list, description="Most recent scans' latency, for a by-mode trend chart"
    )
    agent_tool_usage: dict[str, int] = Field(
        ..., description="Count of times each agent tool was called, across all agent-mode chats"
    )


class ReviewScan(BaseModel):
    id: int
    created_at: str
    mode: str
    predicted_label: str
    confidence: float
    feedback_label: str | None
    reason: str = Field(..., description="'low_confidence' and/or 'corrected'")


class ReviewQueueResponse(BaseModel):
    scans: list[ReviewScan]


class ModelVersionInfo(BaseModel):
    version: str
    is_active: bool = Field(..., description="Whether this is the currently-loaded model")
    overall_accuracy: float | None = None
    per_class_f1: dict[str, float] = Field(default_factory=dict)
    num_correction_examples: int | None = Field(
        None, description="Present only for versions produced by scripts/retrain.py"
    )


class DriftInfo(BaseModel):
    baseline_accuracy: float | None = Field(
        None, description="The active model's validation accuracy at training time"
    )
    rolling_7day_mean_confidence: float | None = None
    is_drifting: bool = Field(
        False, description="rolling_7day_mean_confidence is meaningfully below baseline_accuracy"
    )


class ModelsResponse(BaseModel):
    active_version: str = Field(..., description="'production' or a v{n} artifacts/models/ version")
    versions: list[ModelVersionInfo]
    drift: DriftInfo
