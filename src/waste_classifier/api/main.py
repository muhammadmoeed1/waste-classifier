"""FastAPI application: image classification + Groq recycling assistant."""

from __future__ import annotations

import base64
import io
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

from waste_classifier import config
from waste_classifier.api.schemas import (
    ChatRequest,
    ChatResponse,
    DetectionItem,
    DetectResponse,
    EnvironmentalImpact,
    HealthResponse,
    PredictionResponse,
    TranscriptionResponse,
)
from waste_classifier.genai import assistant
from waste_classifier.genai.groq_client import get_client
from waste_classifier.ml import impact as impact_module
from waste_classifier.ml.classifier import classifier
from waste_classifier.ml.detect import detect_and_classify, draw_detections
from waste_classifier.ml.explain import generate_gradcam
from waste_classifier.rag import retriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        classifier.load()
    except Exception:
        logger.exception("Failed to load classifier model")

    try:
        retriever.build()
    except Exception:
        logger.exception("Failed to build knowledge base retriever")

    yield


app = FastAPI(title=config.API_TITLE, version=config.API_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
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
async def predict(
    image: UploadFile = File(...), include_gradcam: bool = True
) -> PredictionResponse:
    if not classifier.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded. Run training first (python -m waste_classifier.ml.train).",
        )

    contents = await image.read()
    try:
        img = Image.open(io.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.") from exc

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
def chat(request: ChatRequest) -> ChatResponse:
    if not config.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured on the server.")

    history = [m.model_dump() for m in request.history]
    answer = assistant.ask(request.question, request.classification_label, history)
    return ChatResponse(answer=answer)


@app.post("/api/detect", response_model=DetectResponse)
async def detect(image: UploadFile = File(...)) -> DetectResponse:
    if not classifier.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded. Run training first (python -m waste_classifier.ml.train).",
        )

    contents = await image.read()
    try:
        img = Image.open(io.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.") from exc

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
async def transcribe(audio: UploadFile = File(...)) -> TranscriptionResponse:
    if not config.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured on the server.")

    contents = await audio.read()
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


@app.post("/api/chat/stream")
def chat_stream(request: ChatRequest):
    if not config.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured on the server.")

    history = [m.model_dump() for m in request.history]

    def event_generator():
        yield from assistant.ask_stream(request.question, request.classification_label, history)

    return StreamingResponse(event_generator(), media_type="text/plain")


# Serve the static frontend (web/) at the root, after API routes are registered.
app.mount("/", StaticFiles(directory=str(config.ROOT_DIR / "web"), html=True), name="web")
