"""FastAPI application: image classification + Groq recycling assistant."""

from __future__ import annotations

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
    HealthResponse,
    PredictionResponse,
)
from waste_classifier.genai import assistant
from waste_classifier.ml.classifier import classifier
from waste_classifier.rag.retriever import retriever

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
async def predict(image: UploadFile = File(...)) -> PredictionResponse:
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
    return PredictionResponse(
        label=result.label,
        confidence=result.confidence,
        recyclable=result.recyclable,
        probabilities=result.probabilities,
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if not config.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured on the server.")

    history = [m.model_dump() for m in request.history]
    answer = assistant.ask(request.question, request.classification_label, history)
    return ChatResponse(answer=answer)


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
