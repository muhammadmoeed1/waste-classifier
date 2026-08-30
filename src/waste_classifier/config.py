"""Centralized configuration, loaded from environment variables (.env)."""

import os
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image

load_dotenv()

# Decompression-bomb guard: without this, a small file that decodes to a huge
# canvas (e.g. a crafted PNG) can blow up memory during Image.open()/predict()
# well before our own MAX_UPLOAD_BYTES check ever sees a "large" file on disk.
Image.MAX_IMAGE_PIXELS = 40_000_000

ROOT_DIR = Path(__file__).resolve().parents[2]

# --- Model / classifier ---
MODEL_PATH = Path(os.getenv("MODEL_PATH", ROOT_DIR / "artifacts" / "waste_model.keras"))
CLASS_NAMES_PATH = Path(
    os.getenv("CLASS_NAMES_PATH", ROOT_DIR / "artifacts" / "class_names.json")
)
IMG_SIZE = (224, 224)

RECYCLABLE_CLASSES = {"cardboard", "glass", "metal", "paper", "plastic"}

# --- Dataset / training ---
DATASET_DIR = Path(os.getenv("DATASET_DIR", ROOT_DIR / "data" / "dataset"))
METRICS_DIR = Path(os.getenv("METRICS_DIR", ROOT_DIR / "artifacts" / "metrics"))

# --- GenAI (Groq) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# --- Region ---
# "generic" (default): assumes Western-style kerbside recycling infrastructure.
# "pk": Pakistan — swaps in a knowledge base/system prompt tuned for the informal
# kabaria/scrap-dealer resale economy that actually exists locally, where most
# municipal kerbside recycling does not. Default is "generic" so existing
# deployments are unaffected unless this is explicitly opted into.
REGION = os.getenv("REGION", "generic").lower()


def _default_knowledge_base_dir(region: str) -> Path:
    if region == "pk":
        return ROOT_DIR / "data" / "knowledge_base" / "pk"
    return ROOT_DIR / "data" / "knowledge_base"


# --- RAG ---
KNOWLEDGE_BASE_DIR = Path(
    os.getenv("KNOWLEDGE_BASE_DIR", _default_knowledge_base_dir(REGION))
)
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))

# "embeddings" (default): sentence-transformers + FAISS vector search — used for local
# dev, Docker, and any host with enough RAM.
# "tfidf": lightweight scikit-learn keyword retriever with no torch/embeddings model —
# used for the free-tier deployment profile (docker/Dockerfile.lite), which needs to
# fit well under 512MB RAM.
RAG_BACKEND = os.getenv("RAG_BACKEND", "embeddings")

# Grad-CAM needs an extra gradient pass through the CNN, which measurably raises
# peak memory (~150MB in local testing) — enough to push a 512MB free-tier host
# over its limit. The lightweight deployment profile (docker/Dockerfile.lite)
# sets this to disable Grad-CAM server-side regardless of what a client requests.
DISABLE_GRADCAM = os.getenv("DISABLE_GRADCAM", "false").lower() == "true"

# --- API ---
API_TITLE = "Smart Waste Classifier API"
API_VERSION = __import__("waste_classifier").__version__
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# --- Input hardening ---
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(8 * 1024 * 1024)))  # 8 MB
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_CHAT_HISTORY_MESSAGES = int(os.getenv("MAX_CHAT_HISTORY_MESSAGES", "12"))

# --- Rate limiting (requests per minute, keyed by client IP) ---
RATE_LIMIT_PREDICT = os.getenv("RATE_LIMIT_PREDICT", "30/minute")
RATE_LIMIT_DETECT = os.getenv("RATE_LIMIT_DETECT", "30/minute")
RATE_LIMIT_CHAT = os.getenv("RATE_LIMIT_CHAT", "10/minute")
RATE_LIMIT_TRANSCRIBE = os.getenv("RATE_LIMIT_TRANSCRIBE", "5/minute")

# --- Persistence ---
# SQLite file for local/dev by default. The schema (db/models.py) is written to
# be Postgres-compatible so production deploys only need to change this URL.
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{ROOT_DIR / 'data' / 'app.db'}")
