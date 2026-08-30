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

### 1. Create a free Postgres database first

Render's free web service has an **ephemeral filesystem** — anything written
to disk (including a local SQLite file) is wiped on every redeploy or restart.
Since scans, chat turns, and feedback corrections are all persisted, use a
real Postgres database instead:

1. In the Render dashboard: **New → PostgreSQL**.
2. Name it (e.g. `waste-classifier-db`), pick the **Free** plan, create it.
3. Once it's provisioned, copy the **Internal Database URL** shown on its
   page (starts with `postgresql://`) — you'll need it in step 3 below.

### 2. Create the web service

1. Create a free account at https://render.com and connect your GitHub repo.
2. **New → Web Service** → select the `waste-classifier` repo.
3. **Language**: **Docker**. **Dockerfile path**: `docker/Dockerfile.lite`.
4. **Instance type**: **Free**.

### 3. Set environment variables

Under the web service's **Environment** tab, add:

- `GROQ_API_KEY` — your key from https://console.groq.com/keys
- `GROQ_MODEL` — `openai/gpt-oss-120b`
- `DATABASE_URL` — the Internal Database URL you copied in step 1
- (optional) `REGION=pk` — for Pakistan-localized disposal guidance instead
  of the generic default

### 4. Deploy

Click **Create Web Service**. Render builds the image (fetching model weights
from the GitHub Release at build time) and redeploys automatically on every
push to `main`. Your live URL appears at the top of the Render dashboard once
the build finishes (`https://waste-classifier-xxxx.onrender.com`).

**Two free-tier tradeoffs worth knowing (not bugs):**
- The service **spins down after 15 minutes of inactivity** and takes ~30-60s
  to wake up on the next request. If you're sharing the link (e.g. with a
  recruiter), an external uptime pinger such as [UptimeRobot](https://uptimerobot.com/)
  hitting `/health` every ~10 minutes keeps it warm, for free.
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
