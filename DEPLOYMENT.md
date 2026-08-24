# Deployment Guide

This app ships as a Docker container in two profiles:

- **`docker/Dockerfile`** — the full app (embeddings + FAISS RAG, Grad-CAM, YOLO
  multi-item detection). Needs ~1GB+ RAM. Use this for local development,
  self-hosting, or any host with enough RAM.
- **`docker/Dockerfile.lite`** — a memory-optimized profile for free-tier hosts.
  Swaps the sentence-transformers/FAISS/torch RAG stack for a lightweight
  TF-IDF retriever, disables Grad-CAM (which needs an extra gradient pass), and
  pins TensorFlow's thread pools — measured at **~220MB peak RAM** per request
  (vs. ~560MB for the full profile with Grad-CAM enabled). Everything else
  (classification, multi-item detection, Groq chat, Whisper voice input,
  the tool-calling agent) is unchanged.

## Deploy to Render.com

1. Create a free account at https://render.com and connect your GitHub repo.
2. **New → Web Service** → select the `waste-classifier` repo.
3. **Language**: **Docker**. **Dockerfile path**: `docker/Dockerfile.lite`.
4. **Instance type**: **Free**.
5. Under **Environment Variables**, add:
   - `GROQ_API_KEY` — your key from https://console.groq.com/keys
   - `GROQ_MODEL` — `openai/gpt-oss-120b`
6. Click **Create Web Service**. Render builds the image and redeploys
   automatically on every push to `main`.
7. Your live URL appears at the top of the Render dashboard once the build
   finishes (`https://waste-classifier-xxxx.onrender.com`).

**Two free-tier tradeoffs worth knowing (not bugs):**
- The service **spins down after 15 minutes of inactivity** and takes ~30-60s
  to wake up on the next request.
- The lite profile **skips the Grad-CAM heatmap** and uses TF-IDF instead of
  embeddings-based RAG, to fit the free tier's 512MB RAM limit. Both are fully
  implemented in the codebase and active in the full `docker/Dockerfile`
  profile — this is a deliberate memory/feature tradeoff for the free-hosted
  deploy, not a limitation of the underlying work.

## Local Docker run (to test before deploying)

Full profile:
```bash
cp .env.example .env        # then fill in your GROQ_API_KEY
docker compose up --build
```

Lite profile (to test exactly what runs on Render):
```bash
docker build -f docker/Dockerfile.lite -t waste-classifier:lite .
docker run -p 7860:7860 --env-file .env waste-classifier:lite
```
Then open http://localhost:7860

## Local run without Docker

```bash
python -m venv venv && venv\Scripts\activate   # source venv/bin/activate on macOS/Linux
pip install -r requirements-dev.txt
cp .env.example .env        # then fill in your GROQ_API_KEY
uvicorn waste_classifier.api.main:app --app-dir src --reload
```
Then open http://127.0.0.1:8000
