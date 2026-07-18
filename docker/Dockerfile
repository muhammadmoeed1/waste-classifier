FROM python:3.11-slim

WORKDIR /app

# System deps needed by Pillow/matplotlib at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY web/ web/
COPY data/knowledge_base/ data/knowledge_base/
COPY artifacts/waste_model.keras artifacts/waste_model.keras
COPY artifacts/class_names.json artifacts/class_names.json
COPY pyproject.toml .

ENV PYTHONPATH=/app/src
EXPOSE 7860

CMD ["uvicorn", "waste_classifier.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
