FROM python:3.11-slim

WORKDIR /app

# System deps needed by Pillow/matplotlib/OpenCV at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake the sentence-embedding model into the image at build time, so the
# container doesn't need a runtime download from the Hugging Face Hub on
# every cold start (faster startup, and works even if outbound access to
# huggingface.co is restricted in the deploy environment).
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY src/ src/
COPY web/ web/
COPY data/knowledge_base/ data/knowledge_base/
COPY artifacts/waste_model.keras artifacts/waste_model.keras
COPY artifacts/class_names.json artifacts/class_names.json
COPY pyproject.toml .

ENV PYTHONPATH=/app/src
EXPOSE 7860

CMD ["uvicorn", "waste_classifier.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
