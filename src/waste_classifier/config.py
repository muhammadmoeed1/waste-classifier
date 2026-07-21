"""Centralized configuration, loaded from environment variables (.env)."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

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
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# --- RAG ---
KNOWLEDGE_BASE_DIR = Path(
    os.getenv("KNOWLEDGE_BASE_DIR", ROOT_DIR / "data" / "knowledge_base")
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
