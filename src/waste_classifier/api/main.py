"""FastAPI application: image classification + Groq recycling assistant."""

from __future__ import annotations

import base64
import io
import json
import logging
from contextlib import asynccontextmanager

import groq
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from waste_classifier import config
from waste_classifier.api import validation
from waste_classifier.api.schemas import (
    AgentResponse,
    ChatRequest,
    ChatResponse,
    DetectionItem,
    DetectResponse,
    EnvironmentalImpact,
    HealthResponse,
    PredictionResponse,
    ToolCall,
    TranscriptionResponse,
)
from waste_classifier.genai import agent as agent_module
from waste_classifier.genai import assistant
from waste_classifier.genai.groq_client import get_client
from waste_classifier.ml import impact as impact_module
from waste_classifier.ml.classifier import classifier
from waste_classifier.ml.detect import detect_and_classify, draw_detections
from waste_classifier.ml.explain import generate_gradcam
from waste_classifier.rag import retriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


def _warmup_classifier() -> None:
    """Run one dummy inference so the first real request doesn't pay the
    one-time TF graph-build cost while holding up a user."""
    if not classifier.is_ready:
        return
    try:
        dummy = Image.new("RGB", config.IMG_SIZE)
        classifier.predict(dummy)
    except Exception:
        logger.exception("Warmup inference failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        classifier.load()
    except Exception:
        logger.exception("Failed to load classifier model")

    _warmup_classifier()

    try:
        retriever.build()
    except Exception:
        logger.exception("Failed to build knowledge base retriever")

    yield


app = FastAPI(title=config.API_TITLE, version=config.API_VERSION, lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# allow_credentials=True combined with a wildcard allow_origins is an invalid
# combination per the CORS spec (browsers reject it) -- and unnecessary here
# anyway, since the app uses no cookies/session auth.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_loaded=classifier.is_ready,
        retriever_ready=retriever.is_ready,
        groq_configured=bool(config.GROQ_API_KEY),
    )


@app.post("/api/predict", response_model=PredictionResponse)
@limiter.limit(config.RATE_LIMIT_PREDICT)
def predict(
    request: Request, image: UploadFile = File(...), include_gradcam: bool = True
) -> PredictionResponse:
    # Deliberately a sync `def`, not `async def`: the body below is CPU-bound
    # TensorFlow/OpenCV work, and FastAPI only threadpool-offloads sync
    # handlers. An async def here would run this on the event loop directly
    # and block every other concurrent request (including /health).
    if not classifier.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded. Run training first (python -m waste_classifier.ml.train).",
        )

    validation.reject_oversized_content_length(request)
    validation.validate_image_content_type(image.content_type)
    contents = validation.read_upload_bounded(image)
    img = validation.open_and_verify_image(contents)

    result = classifier.predict(img)

    # Grad-CAM adds a gradient pass; skip it for continuous live-camera capture
    # (called every ~2s) where responsiveness matters more than the heatmap, and
    # skip it unconditionally on the lightweight deployment profile where the
    # extra memory would risk exceeding the host's RAM limit.
    gradcam_image = None
    if include_gradcam and not config.DISABLE_GRADCAM:
        try:
            gradcam_image = generate_gradcam(classifier.model, img, pred_index=result.label_index)
        except Exception:
            logger.exception("Grad-CAM generation failed; returning prediction without it")

    fact = impact_module.get_impact(result.label)
    impact_response = (
        EnvironmentalImpact(
            headline=fact.headline,
            co2_saved_per_kg=fact.co2_saved_per_kg,
            energy_saved_pct=fact.energy_saved_pct,
            fact=fact.fact,
        )
        if fact
        else None
    )

    return PredictionResponse(
        label=result.label,
        confidence=result.confidence,
        recyclable=result.recyclable,
        probabilities=result.probabilities,
        gradcam_image=gradcam_image,
        impact=impact_response,
    )


@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit(config.RATE_LIMIT_CHAT)
def chat(request: Request, payload: ChatRequest) -> ChatResponse:
    if not config.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured on the server.")

    history = [m.model_dump() for m in payload.history]
    answer = assistant.ask(
        payload.question, payload.classification_label, history, payload.language
    )
    return ChatResponse(answer=answer)


@app.post("/api/agent", response_model=AgentResponse)
@limiter.limit(config.RATE_LIMIT_CHAT)
def agent(request: Request, payload: ChatRequest) -> AgentResponse:
    """Tool-calling agent variant: the LLM autonomously decides which tools to
    invoke (recycling guide lookup, impact estimation, recyclability check)
    before answering, rather than relying solely on RAG context."""
    if not config.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured on the server.")

    history = [m.model_dump() for m in payload.history]
    result = agent_module.run_agent(
        payload.question, payload.classification_label, history, payload.language
    )
    return AgentResponse(
        answer=result.answer,
        tools_used=[ToolCall(name=t["name"], arguments=t["arguments"]) for t in result.tools_used],
    )


@app.post("/api/detect", response_model=DetectResponse)
@limiter.limit(config.RATE_LIMIT_DETECT)
def detect(request: Request, image: UploadFile = File(...)) -> DetectResponse:
    # Sync `def` for the same reason as /api/predict — YOLO/OpenCV/TensorFlow
    # work below is CPU-bound and must not run directly on the event loop.
    if not classifier.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded. Run training first (python -m waste_classifier.ml.train).",
        )

    validation.reject_oversized_content_length(request)
    validation.validate_image_content_type(image.content_type)
    contents = validation.read_upload_bounded(image)
    img = validation.open_and_verify_image(contents)

    detections = detect_and_classify(img, classifier)
    annotated = draw_detections(img, detections)

    buf = io.BytesIO()
    annotated.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")

    return DetectResponse(
        detections=[
            DetectionItem(
                box=list(d.box),
                label=d.label,
                confidence=d.confidence,
                recyclable=d.recyclable,
            )
            for d in detections
        ],
        annotated_image=f"data:image/png;base64,{encoded}",
    )


@app.post("/api/transcribe", response_model=TranscriptionResponse)
@limiter.limit(config.RATE_LIMIT_TRANSCRIBE)
async def transcribe(request: Request, audio: UploadFile = File(...)) -> TranscriptionResponse:
    if not config.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured on the server.")

    validation.reject_oversized_content_length(request)
    contents = validation.read_upload_bounded(audio)
    if not contents:
        raise HTTPException(status_code=400, detail="No audio data received.")

    client = get_client()
    try:
        response = client.audio.transcriptions.create(
            file=(audio.filename or "audio.webm", contents),
            model="whisper-large-v3-turbo",
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Transcription failed: {exc}") from exc

    return TranscriptionResponse(text=response.text)


def _sse(event: str, data: dict) -> str:
    """Format one Server-Sent Events frame."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.post("/api/chat/stream")
@limiter.limit(config.RATE_LIMIT_CHAT)
def chat_stream(request: Request, payload: ChatRequest):
    if not config.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured on the server.")

    history = [m.model_dump() for m in payload.history]

    def event_generator():
        # By the time this generator runs, the HTTP response has already
        # started (200 + headers sent) -- an exception here can't change the
        # status code, so upstream failures must be signaled in-band as a
        # distinct SSE event type rather than an HTTP error response.
        try:
            for delta in assistant.ask_stream(
                payload.question, payload.classification_label, history, payload.language
            ):
                yield _sse("token", {"text": delta})
        except groq.APITimeoutError:
            yield _sse("error", {"detail": "The AI service timed out. Please try again."})
            return
        except groq.GroqError as exc:
            yield _sse("error", {"detail": f"AI service error: {exc}"})
            return
        except Exception:
            logger.exception("Unexpected error during chat stream")
            yield _sse("error", {"detail": "Something went wrong. Please try again."})
            return
        yield _sse("done", {})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Serve the static frontend (web/) at the root, after API routes are registered.
app.mount("/", StaticFiles(directory=str(config.ROOT_DIR / "web"), html=True), name="web")
