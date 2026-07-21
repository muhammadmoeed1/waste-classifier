# Deployment Guide

This app is a single Docker container (see [docker/Dockerfile](docker/Dockerfile)), so it can
be deployed anywhere that runs containers.

**A note on hosting costs (checked live, since these change often):**
- **Hugging Face Spaces** now requires a **paid PRO plan ($9/month)** to run a Docker
  SDK Space, even on free CPU hardware — only Gradio/Streamlit/static Spaces stay free.
- **Render.com**'s free web service tier is only **512MB RAM**, which is very likely
  too small for this app (TensorFlow + PyTorch + FAISS all loaded at once).
- **Google Cloud Run** (below) is genuinely free for a low-traffic demo like this one —
  it scales to zero when idle (no cost while nobody's using it) and comfortably fits
  within its generous "Always Free" monthly quota. Recommended.

## Option A — Google Cloud Run (recommended, free for this use case)

### 1. One-time account setup
1. Create a Google Cloud account at https://console.cloud.google.com if you don't have one.
2. Create a new project (or use an existing one) — note its **Project ID**.
3. Enable billing on the project (**Billing → Link a billing account**). This requires
   a card on file, but you will not be charged as long as usage stays within the
   [Always Free](https://cloud.google.com/free) monthly quota (2M requests,
   180,000 vCPU-seconds, 360,000 GiB-seconds) — a portfolio demo with light traffic
   stays well inside this.
4. Enable two APIs for your project (Console → search each → **Enable**):
   - **Cloud Run API**
   - **Cloud Build API**

### 2. Install the gcloud CLI
Download and install from https://cloud.google.com/sdk/docs/install, then:
```bash
gcloud init                     # logs you in via browser, sets your default project
gcloud auth login                # if init doesn't already prompt this
```

### 3. Build the image with Cloud Build
From the repo root (this project already includes `cloudbuild.yaml`, which points
Cloud Build at `docker/Dockerfile` instead of the repo root):
```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_IMAGE="us-central1-docker.pkg.dev/YOUR_PROJECT_ID/waste-classifier/app:latest" \
  .
```
Replace `YOUR_PROJECT_ID` with your actual project ID. The first time you do this,
`gcloud` will offer to create an Artifact Registry repo for you — accept it.

### 4. Deploy to Cloud Run
```bash
gcloud run deploy waste-classifier \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/waste-classifier/app:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --set-env-vars GROQ_API_KEY=YOUR_GROQ_KEY,GROQ_MODEL=llama-3.3-70b-versatile
```
(For a real project you'd put `GROQ_API_KEY` in
[Secret Manager](https://cloud.google.com/run/docs/configuring/services/secrets)
instead of a plain env var — fine to skip that extra step for a portfolio demo.)

### 5. Get your live URL
`gcloud run deploy` prints a **Service URL** at the end
(`https://waste-classifier-xxxxx-uc.a.run.app`) — that's your public, shareable demo link.

### Redeploying after future changes
Just re-run steps 3 and 4 (the build + deploy commands) — Cloud Run keeps the URL
the same across deployments.

## Option B — Hugging Face Spaces (requires PRO, $9/month)

1. Create a free account at https://huggingface.co/join, then subscribe to
   [PRO](https://huggingface.co/pricing) (Docker Spaces are gated behind this).
2. Create a new **Space**: https://huggingface.co/new-space — SDK: **Docker**, visibility: public.
3. In the Space's **Settings → Variables and secrets**, add secret `GROQ_API_KEY`.
4. Push this repo's code to the Space's git remote:
   ```bash
   git remote add space https://huggingface.co/spaces/<your-username>/<space-name>
   git push space main
   ```
   (Requires a YAML metadata block at the top of the Space's README.md — see
   `.github/workflows/deploy-hf-spaces.yml` for an automated way to inject it, or add manually:)
   ```yaml
   ---
   title: Smart Waste Classifier
   emoji: ♻️
   colorFrom: green
   colorTo: blue
   sdk: docker
   app_port: 7860
   ---
   ```
5. Live demo: `https://huggingface.co/spaces/<your-username>/<space-name>`

## Option C — Render.com (free tier likely too small for this app)

Only consider this if you're willing to either upgrade to a paid instance (≥1GB RAM,
~$7/month) or significantly lighten the app's dependencies first (e.g. drop the
sentence-transformers/FAISS RAG stack in favor of the earlier TF-IDF retriever).

1. Create a free account at https://render.com and connect your GitHub repo.
2. New → Web Service → select this repo.
3. Environment: **Docker**, Dockerfile path: `docker/Dockerfile`.
4. Add environment variable `GROQ_API_KEY` in the Render dashboard.
5. Pick an instance type with at least 1GB RAM if the free tier fails to start (OOM).

## Local Docker run (to test before deploying)

```bash
cp .env.example .env        # then fill in your GROQ_API_KEY
docker compose up --build
```
Then open http://localhost:7860
