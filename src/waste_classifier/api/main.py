"""FastAPI application: image classification + Groq recycling assistant."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from functools import lru_cache

import groq
import numpy as np
from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlmodel import Session, select

from waste_classifier import config
from waste_classifier.api import validation
from waste_classifier.api.schemas import (
    AgentResponse,
    ChatRequest,
    ChatResponse,
    ConfusionCell,
    DetectionItem,
    DetectResponse,
    DriftInfo,
    EnvironmentalImpact,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    LatencyPoint,
    ModelsResponse,
    ModelVersionInfo,
    PredictionResponse,
    ReviewQueueResponse,
    ReviewScan,
    StatsResponse,
    ToolCall,
    TranscriptionResponse,
)
from waste_classifier.db.models import ChatTurn, Scan
from waste_classifier.db.session import get_session, init_db, safe_write, write_and_get_id
from waste_classifier.genai import agent as agent_module
from waste_classifier.genai import assistant
from waste_classifier.genai.groq_client import get_client
from waste_classifier.ml import confidence as confidence_module
from waste_classifier.ml import impact as impact_module
from waste_classifier.ml.classifier import classifier
from waste_classifier.ml.detect import detect_and_classify, draw_detections
from waste_classifier.ml.explain import generate_gradcam
from waste_classifier.ml.onnx_classifier import onnx_classifier
from waste_classifier.rag import retriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


def _fast_classifier():
    """The classifier used for camera and multi-item modes, where Grad-CAM
    isn't shown anyway and per-request latency matters more: ONNX Runtime
    when its export is available (~12.75x faster per
    artifacts/metrics/onnx_benchmark.json), falling back to the same Keras
    classifier the upload flow uses otherwise."""
    return onnx_classifier if onnx_classifier.is_ready else classifier


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
        init_db()
    except Exception:
        logger.exception("Failed to initialize database")

    try:
        classifier.load()
    except Exception:
        logger.exception("Failed to load classifier model")

    try:
        onnx_classifier.load()
    except Exception:
        logger.exception("Failed to load ONNX classifier (optional; falls back to Keras)")

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
        onnx_model_loaded=onnx_classifier.is_ready,
        retriever_ready=retriever.is_ready,
        groq_configured=bool(config.GROQ_API_KEY),
    )


@app.post("/api/predict", response_model=PredictionResponse)
@limiter.limit(config.RATE_LIMIT_PREDICT)
def predict(
    request: Request,
    image: UploadFile = File(...),
    include_gradcam: bool = True,
    mode: str = "upload",
) -> PredictionResponse:
    # Deliberately a sync `def`, not `async def`: the body below is CPU-bound
    # TensorFlow/OpenCV work, and FastAPI only threadpool-offloads sync
    # handlers. An async def here would run this on the event loop directly
    # and block every other concurrent request (including /health).
    #
    # Input validation runs before the model-readiness check: a malformed or
    # oversized request is wrong regardless of server state and should always
    # get a 4xx, not have that masked by a 503 if the model happens not to be
    # loaded.
    start = time.perf_counter()
    validation.reject_oversized_content_length(request)
    validation.validate_image_content_type(image.content_type)
    contents = validation.read_upload_bounded(image)
    img = validation.open_and_verify_image(contents)

    if not classifier.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded. Run training first (python -m waste_classifier.ml.train).",
        )

    # Upload mode always uses the Keras model (Grad-CAM needs real gradient-tape
    # access, which ONNX Runtime's inference-only session can't provide). Camera
    # mode uses the faster ONNX export when available -- see _fast_classifier().
    active_classifier = classifier if mode == "upload" else _fast_classifier()
    result = active_classifier.predict(img)

    # Grad-CAM adds a gradient pass; skip it for continuous live-camera capture
    # (called every ~2s) where responsiveness matters more than the heatmap, and
    # skip it unconditionally on the lightweight deployment profile where the
    # extra memory would risk exceeding the host's RAM limit.
    gradcam_image = None
    if include_gradcam and not config.DISABLE_GRADCAM and active_classifier is classifier:
        try:
            gradcam_image = generate_gradcam(classifier.model, img, pred_index=result.label_index)
        except Exception:
            logger.exception("Grad-CAM generation failed; returning prediction without it")

    is_ood = confidence_module.is_out_of_distribution(result.probabilities)
    margin, runner_up_label, runner_up_confidence = confidence_module.top2_margin_and_runnerup(
        result.probabilities
    )

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

    # Written synchronously (not via BackgroundTasks like the other endpoints)
    # so the response below can include the new row's id -- the frontend
    # needs it to attach feedback ("wrong? tap the right category") to this
    # exact prediction. write_and_get_id() still never raises on its own.
    scan_id = write_and_get_id(
        Scan(
            session_id=request.headers.get("X-Session-Id", "anonymous"),
            mode=mode,
            predicted_label=result.label,
            confidence=result.confidence,
            all_probabilities=json.dumps(result.probabilities),
            latency_ms=int((time.perf_counter() - start) * 1000),
            image_hash=hashlib.sha256(contents).hexdigest(),
        )
    )

    return PredictionResponse(
        label=result.label,
        confidence=result.confidence,
        recyclable=result.recyclable,
        probabilities=result.probabilities,
        gradcam_image=gradcam_image,
        impact=impact_response,
        scan_id=scan_id,
        is_out_of_distribution=is_ood,
        is_ambiguous=margin < confidence_module.TOP2_MARGIN_THRESHOLD,
        runner_up_label=runner_up_label,
        runner_up_confidence=runner_up_confidence if runner_up_label else None,
    )


@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit(config.RATE_LIMIT_CHAT)
def chat(request: Request, payload: ChatRequest, background_tasks: BackgroundTasks) -> ChatResponse:
    if not config.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured on the server.")

    start = time.perf_counter()
    history = [m.model_dump() for m in payload.history]
    answer = assistant.ask(
        payload.question, payload.classification_label, history, payload.language
    )

    background_tasks.add_task(
        safe_write,
        ChatTurn(
            session_id=request.headers.get("X-Session-Id", "anonymous"),
            mode="rag",
            question=payload.question,
            latency_ms=int((time.perf_counter() - start) * 1000),
            language=payload.language,
        ),
    )

    return ChatResponse(answer=answer)


@app.post("/api/agent", response_model=AgentResponse)
@limiter.limit(config.RATE_LIMIT_CHAT)
def agent(
    request: Request, payload: ChatRequest, background_tasks: BackgroundTasks
) -> AgentResponse:
    """Tool-calling agent variant: the LLM autonomously decides which tools to
    invoke (recycling guide lookup, impact estimation, recyclability check)
    before answering, rather than relying solely on RAG context."""
    if not config.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured on the server.")

    start = time.perf_counter()
    history = [m.model_dump() for m in payload.history]
    result = agent_module.run_agent(
        payload.question, payload.classification_label, history, payload.language
    )

    background_tasks.add_task(
        safe_write,
        ChatTurn(
            session_id=request.headers.get("X-Session-Id", "anonymous"),
            mode="agent",
            question=payload.question,
            tools_used=json.dumps(result.tools_used),
            latency_ms=int((time.perf_counter() - start) * 1000),
            language=payload.language,
        ),
    )

    return AgentResponse(
        answer=result.answer,
        tools_used=[ToolCall(name=t["name"], arguments=t["arguments"]) for t in result.tools_used],
    )


@app.post("/api/detect", response_model=DetectResponse)
@limiter.limit(config.RATE_LIMIT_DETECT)
def detect(
    request: Request, background_tasks: BackgroundTasks, image: UploadFile = File(...)
) -> DetectResponse:
    # Sync `def` for the same reason as /api/predict — YOLO/OpenCV/TensorFlow
    # work below is CPU-bound and must not run directly on the event loop.
    # Input validation runs before the model-readiness check; see /api/predict.
    start = time.perf_counter()
    validation.reject_oversized_content_length(request)
    validation.validate_image_content_type(image.content_type)
    contents = validation.read_upload_bounded(image)
    img = validation.open_and_verify_image(contents)

    if not classifier.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded. Run training first (python -m waste_classifier.ml.train).",
        )

    # Multi-item mode uses the faster ONNX export when available -- see
    # _fast_classifier(); Grad-CAM isn't shown for individual crops anyway.
    detections = detect_and_classify(img, _fast_classifier())
    annotated = draw_detections(img, detections)

    buf = io.BytesIO()
    annotated.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")

    # Scan has a single predicted_label/confidence pair, but /api/detect finds
    # zero or more items -- record the highest-confidence detection there (or
    # "none" if nothing was found), and the full per-item breakdown in
    # all_probabilities so no detection data is lost.
    top = max(detections, key=lambda d: d.confidence, default=None)
    background_tasks.add_task(
        safe_write,
        Scan(
            session_id=request.headers.get("X-Session-Id", "anonymous"),
            mode="multi",
            predicted_label=top.label if top else "none",
            confidence=top.confidence if top else 0.0,
            all_probabilities=json.dumps(
                [{"label": d.label, "confidence": d.confidence} for d in detections]
            ),
            latency_ms=int((time.perf_counter() - start) * 1000),
            image_hash=hashlib.sha256(contents).hexdigest(),
        ),
    )

    return DetectResponse(
        detections=[
            DetectionItem(
                box=list(d.box),
                label=d.label,
                confidence=d.confidence,
                recyclable=d.recyclable,
                is_out_of_distribution=d.is_out_of_distribution,
                is_ambiguous=d.is_ambiguous,
            )
            for d in detections
        ],
        annotated_image=f"data:image/png;base64,{encoded}",
    )


@app.post("/api/scans/{scan_id}/feedback", response_model=FeedbackResponse)
@limiter.limit(config.RATE_LIMIT_PREDICT)
def scan_feedback(
    request: Request,
    scan_id: int,
    payload: FeedbackRequest,
    session: Session = Depends(get_session),
) -> FeedbackResponse:
    """Records a user's correction of a past prediction. This is the data
    source Phase 3's retraining pipeline depends on."""
    scan = session.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found.")

    known_labels = classifier.class_names
    if payload.corrected_label not in known_labels:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown label '{payload.corrected_label}'. "
                f"Must be one of: {sorted(known_labels)}"
            ),
        )

    scan.feedback_label = payload.corrected_label
    scan.feedback_at = datetime.now(UTC)
    session.add(scan)
    session.commit()

    return FeedbackResponse(scan_id=scan_id, feedback_label=scan.feedback_label)


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
    session_id = request.headers.get("X-Session-Id", "anonymous")
    start = time.perf_counter()

    def event_generator():
        # By the time this generator runs, the HTTP response has already
        # started (200 + headers sent) -- an exception here can't change the
        # status code, so upstream failures must be signaled in-band as a
        # distinct SSE event type rather than an HTTP error response.
        try:
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
        finally:
            # The response has already been sent by this point, so writing
            # here (success or error) can't add latency to what the user saw.
            safe_write(
                ChatTurn(
                    session_id=session_id,
                    mode="rag",
                    question=payload.question,
                    latency_ms=int((time.perf_counter() - start) * 1000),
                    language=payload.language,
                )
            )

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@lru_cache(maxsize=1)
def _training_distribution_pct() -> dict[str, float]:
    """Reference class distribution from the TrashNet validation split the
    model was scored against (artifacts/metrics/metrics.json), as
    percentages -- so the dashboard can compare live traffic against it."""
    try:
        with open(config.METRICS_DIR / "metrics.json") as f:
            metrics = json.load(f)
        per_class = metrics.get("per_class", {})
        total = sum(v["support"] for v in per_class.values())
        if not total:
            return {}
        return {name: round(v["support"] / total * 100, 2) for name, v in per_class.items()}
    except Exception:
        logger.exception("Failed to load training distribution from metrics.json")
        return {}


@app.get("/api/stats", response_model=StatsResponse)
def stats(session: Session = Depends(get_session)) -> StatsResponse:
    """Aggregate traffic stats, driven entirely by the Scan/ChatTurn rows
    written above. Phase 2's dashboard reads from this endpoint."""
    scans = session.exec(select(Scan)).all()
    agent_turns = session.exec(select(ChatTurn).where(ChatTurn.mode == "agent")).all()

    class_distribution: dict[str, int] = {}
    for s in scans:
        class_distribution[s.predicted_label] = class_distribution.get(s.predicted_label, 0) + 1

    confidences = [s.confidence for s in scans]
    latencies = [s.latency_ms for s in scans]
    mean_confidence = float(np.mean(confidences)) if confidences else 0.0
    latency_p50 = float(np.percentile(latencies, 50)) if latencies else 0.0
    latency_p95 = float(np.percentile(latencies, 95)) if latencies else 0.0

    recyclable_count = sum(1 for s in scans if s.predicted_label in config.RECYCLABLE_CLASSES)
    recyclable_pct = round(recyclable_count / len(scans) * 100, 2) if scans else 0.0

    confidence_histogram = [0] * 10
    for s in scans:
        bucket = min(int(s.confidence // 10), 9)
        confidence_histogram[bucket] += 1

    confusion_counts: dict[tuple[str, str], int] = {}
    for s in scans:
        if not s.feedback_label:
            continue
        key = (s.predicted_label, s.feedback_label)
        confusion_counts[key] = confusion_counts.get(key, 0) + 1
    confusion_matrix = [
        ConfusionCell(predicted=pred, corrected=corrected, count=count)
        for (pred, corrected), count in confusion_counts.items()
    ]

    recent_scans = session.exec(select(Scan).order_by(Scan.created_at.desc()).limit(200)).all()
    latency_points = [
        LatencyPoint(created_at=s.created_at.isoformat(), mode=s.mode, latency_ms=s.latency_ms)
        for s in recent_scans
    ]

    agent_tool_usage: dict[str, int] = {}
    for turn in agent_turns:
        if not turn.tools_used:
            continue
        for tool_call in json.loads(turn.tools_used):
            name = tool_call["name"] if isinstance(tool_call, dict) else tool_call
            agent_tool_usage[name] = agent_tool_usage.get(name, 0) + 1

    return StatsResponse(
        total_scans=len(scans),
        class_distribution=class_distribution,
        mean_confidence=mean_confidence,
        recyclable_pct=recyclable_pct,
        latency_p50_ms=latency_p50,
        latency_p95_ms=latency_p95,
        confidence_histogram=confidence_histogram,
        training_distribution_pct=_training_distribution_pct(),
        confusion_matrix=confusion_matrix,
        latency_points=latency_points,
        agent_tool_usage=agent_tool_usage,
    )


# Matches web/src/constants.js's UNCERTAINTY_THRESHOLD -- kept in sync manually,
# same as the app's own "not fully sure" warning threshold.
REVIEW_LOW_CONFIDENCE_THRESHOLD = 60


@app.get("/api/scans/review", response_model=ReviewQueueResponse)
def scans_review(session: Session = Depends(get_session)) -> ReviewQueueResponse:
    """Scans worth a human look: low-confidence predictions, or ones already
    corrected via feedback. Metadata only, driving a manual curation
    workflow -- raw images are never stored (see db/models.py), so this
    can't surface thumbnails, only point at what needs attention."""
    scans = session.exec(select(Scan).order_by(Scan.created_at.desc()).limit(500)).all()

    items = []
    for s in scans:
        is_low_confidence = s.confidence < REVIEW_LOW_CONFIDENCE_THRESHOLD
        is_corrected = bool(s.feedback_label) and s.feedback_label != s.predicted_label
        if not (is_low_confidence or is_corrected):
            continue
        reasons = []
        if is_low_confidence:
            reasons.append("low_confidence")
        if is_corrected:
            reasons.append("corrected")
        items.append(
            ReviewScan(
                id=s.id,
                created_at=s.created_at.isoformat(),
                mode=s.mode,
                predicted_label=s.predicted_label,
                confidence=s.confidence,
                feedback_label=s.feedback_label,
                reason="+".join(reasons),
            )
        )
    return ReviewQueueResponse(scans=items)


def _load_version_metrics(metrics_path) -> dict:
    try:
        with open(metrics_path) as f:
            return json.load(f)
    except Exception:
        return {}


@app.get("/api/models", response_model=ModelsResponse)
def models_endpoint(session: Session = Depends(get_session)) -> ModelsResponse:
    """Compares the production model against any versions produced by
    scripts/retrain.py (artifacts/models/v*/), plus a drift indicator:
    rolling 7-day mean confidence vs. the active model's training-time
    validation accuracy, flagged if it's fallen meaningfully below that
    baseline."""
    active_version = config.MODEL_VERSION or "production"

    prod_metrics = _load_version_metrics(config.METRICS_DIR / "metrics.json")
    versions = [
        ModelVersionInfo(
            version="production",
            is_active=(active_version == "production"),
            overall_accuracy=prod_metrics.get("accuracy"),
            per_class_f1={
                name: v.get("f1", 0.0) for name, v in prod_metrics.get("per_class", {}).items()
            },
        )
    ]

    if config.MODELS_DIR.exists():
        for version_dir in sorted(config.MODELS_DIR.iterdir()):
            if not version_dir.is_dir():
                continue
            metrics = _load_version_metrics(version_dir / "metrics.json")
            if not metrics:
                continue
            versions.append(
                ModelVersionInfo(
                    version=version_dir.name,
                    is_active=(active_version == version_dir.name),
                    overall_accuracy=metrics.get("accuracy"),
                    per_class_f1={
                        name: v.get("f1", 0.0) for name, v in metrics.get("per_class", {}).items()
                    },
                    num_correction_examples=metrics.get("num_correction_examples"),
                )
            )

    active_metrics = next((v for v in versions if v.is_active), versions[0])
    baseline_accuracy = active_metrics.overall_accuracy

    week_ago = datetime.now(UTC) - timedelta(days=7)
    recent_scans = session.exec(select(Scan).where(Scan.created_at >= week_ago)).all()
    rolling_confidence = (
        float(np.mean([s.confidence for s in recent_scans])) / 100 if recent_scans else None
    )
    is_drifting = (
        baseline_accuracy is not None
        and rolling_confidence is not None
        and rolling_confidence < baseline_accuracy - 0.10
    )

    return ModelsResponse(
        active_version=active_version,
        versions=versions,
        drift=DriftInfo(
            baseline_accuracy=baseline_accuracy,
            rolling_7day_mean_confidence=rolling_confidence,
            is_drifting=is_drifting,
        ),
    )


@app.get("/dashboard", include_in_schema=False)
def dashboard_page() -> FileResponse:
    return FileResponse(config.ROOT_DIR / "web" / "dashboard.html")


@app.get("/dashboard/review", include_in_schema=False)
def dashboard_review_page() -> FileResponse:
    return FileResponse(config.ROOT_DIR / "web" / "dashboard-review.html")


@app.get("/dashboard/models", include_in_schema=False)
def dashboard_models_page() -> FileResponse:
    return FileResponse(config.ROOT_DIR / "web" / "dashboard-models.html")


# Serve the static frontend (web/) at the root, after API routes are registered.
app.mount("/", StaticFiles(directory=str(config.ROOT_DIR / "web"), html=True), name="web")
