# Deployment Guide

This app is a single Docker container, so it can be deployed anywhere that runs
containers. There are two Docker profiles:

- **`docker/Dockerfile`** — the full app (embeddings + FAISS RAG, Grad-CAM). Needs
  ~1GB+ RAM. Use this for local dev, self-hosting, or any host with enough RAM.
- **`docker/Dockerfile.lite`** — a lightweight profile for free-tier hosts with
  limited RAM. Drops the sentence-transformers/FAISS/torch stack in favor of the
  TF-IDF retriever fallback, disables Grad-CAM (which needs an extra gradient pass),
  and limits TensorFlow's thread pools — measured at **~220MB peak RAM** per
  request (vs. ~560MB for the full profile with Grad-CAM enabled). Everything else
  (image classification, multi-item detection, Groq chat, Whisper voice input) is
  unchanged.

**On hosting costs (checked live, since these change often):**
- **Hugging Face Spaces** now requires a **paid PRO plan ($9/month)** for any
  compute-backed Space (Docker, Gradio, or Streamlit) — only static (no backend)
  Spaces stay free, which doesn't work for this app.
- **Google Cloud Run**'s free quota is genuinely generous, but Google now requires
  a **billing account (card on file)** to enable it, even if you're never charged.
- **Render.com**'s free web service tier requires **no card at all** and gives
  512MB RAM — which is why this project ships the lite profile above, sized to
  fit comfortably inside that limit.

## Recommended: Render.com (free, no card, using the lite profile)

1. Create a free account at https://render.com (no card required) and connect your GitHub repo.
2. **New → Web Service** → select the `waste-classifier` repo.
3. Environment: **Docker**. Set the **Dockerfile path** to `docker/Dockerfile.lite`.
4. Instance type: **Free**.
5. Under **Environment Variables**, add:
   - `GROQ_API_KEY` = your key from https://console.groq.com/keys
   - `GROQ_MODEL` = `llama-3.3-70b-versatile`
6. Click **Create Web Service**. Render builds the image and deploys automatically
   on every push to `main`.
7. Your live demo URL appears at the top of the Render dashboard once the build
   finishes (looks like `https://waste-classifier-xxxx.onrender.com`).

**Two free-tier tradeoffs worth knowing:**
- The service **spins down after 15 minutes of inactivity** and takes ~30-60s to
  wake up on the next request (a "cold start") — normal for free hosting, not a bug.
- The lite profile **skips the Grad-CAM heatmap** and uses simpler keyword-based
  (not embeddings-based) RAG retrieval, to fit the 512MB limit. Both are fully
  implemented and demonstrated in the codebase (and in the full `docker/Dockerfile`
  profile) — this is a deliberate memory/feature tradeoff for the free-hosted demo,
  not a limitation of the underlying work.

## Alternative — Google Cloud Run (free quota, but requires a billing card on file)

Only consider this if you're fine adding a card (you won't be charged for a
low-traffic demo, but Google requires one to enable the Cloud Run API at all).
Runs the full profile (Grad-CAM + embeddings RAG) with no memory concerns.

1. Create a project at https://console.cloud.google.com, enable billing, and enable
   the **Cloud Run API** and **Cloud Build API**.
2. Install the gcloud CLI: https://cloud.google.com/sdk/docs/install, then `gcloud init`.
3. Build with the included `cloudbuild.yaml` (points Cloud Build at `docker/Dockerfile`):
   ```bash
   gcloud builds submit --config cloudbuild.yaml \
     --substitutions=_IMAGE="us-central1-docker.pkg.dev/YOUR_PROJECT_ID/waste-classifier/app:latest" .
   ```
4. Deploy:
   ```bash
   gcloud run deploy waste-classifier \
     --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/waste-classifier/app:latest \
     --region us-central1 --allow-unauthenticated --memory 2Gi \
     --set-env-vars GROQ_API_KEY=YOUR_GROQ_KEY,GROQ_MODEL=llama-3.3-70b-versatile
   ```
5. `gcloud run deploy` prints your live **Service URL** at the end.

## Alternative — Hugging Face Spaces (requires PRO, $9/month)

1. Subscribe to [PRO](https://huggingface.co/pricing), then create a new
   **Space** (SDK: Docker) at https://huggingface.co/new-space.
2. Add secret `GROQ_API_KEY` under the Space's **Settings → Variables and secrets**.
3. Push this repo to the Space's git remote:
   ```bash
   git remote add space https://huggingface.co/spaces/<your-username>/<space-name>
   git push space main
   ```
   Requires a YAML metadata block at the top of the Space's README.md — see
   `.github/workflows/deploy-hf-spaces.yml` for an automated way to inject it.

## Local Docker run (to test before deploying)

Full profile:
```bash
cp .env.example .env        # then fill in your GROQ_API_KEY
docker compose up --build
```

Lite profile (to test what will actually run on Render):
```bash
docker build -f docker/Dockerfile.lite -t waste-classifier:lite .
docker run -p 7860:7860 --env-file .env waste-classifier:lite
```
Then open http://localhost:7860
