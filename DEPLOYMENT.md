# Deployment Guide

This app is a single Docker container (see [docker/Dockerfile](docker/Dockerfile)), so it can
be deployed anywhere that runs containers. Two easy free options below.

## Option A — Hugging Face Spaces (recommended, free, easiest)

1. Create a free account at https://huggingface.co/join if you don't have one.
2. Create a new **Space**: https://huggingface.co/new-space
   - Space SDK: **Docker**
   - Visibility: public (so recruiters/links work without login)
3. In the Space's **Settings -> Variables and secrets**, add a secret:
   - `GROQ_API_KEY` = your key from https://console.groq.com/keys
4. Push this repo's code to the Space's git remote:
   ```bash
   git remote add space https://huggingface.co/spaces/<your-username>/<space-name>
   git push space main
   ```
   (Hugging Face Spaces requires a YAML metadata block at the top of the Space's
   README.md — see `.github/workflows/deploy-hf-spaces.yml` for an automated way
   to inject it on every push, or add it manually:)
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
5. **To automate this on every push to `main`** instead of pushing manually:
   - Get a Hugging Face access token (write access): https://huggingface.co/settings/tokens
   - In your GitHub repo -> Settings -> Secrets and variables -> Actions, add:
     - `HF_TOKEN` = the token above
     - `HF_SPACE_REPO` = `<your-username>/<space-name>`
   - The included workflow (`.github/workflows/deploy-hf-spaces.yml`) will then
     deploy automatically on every push to `main`.
6. Your live demo will be at:
   `https://huggingface.co/spaces/<your-username>/<space-name>`

## Option B — Render.com

1. Create a free account at https://render.com and connect your GitHub repo.
2. New -> Web Service -> select this repo.
3. Environment: **Docker**, Dockerfile path: `docker/Dockerfile`.
4. Add environment variable `GROQ_API_KEY` in the Render dashboard.
5. Deploy — Render builds the Dockerfile and gives you a public URL automatically
   on every push to `main`.

## Local Docker run (to test before deploying)

```bash
cp .env.example .env        # then fill in your GROQ_API_KEY
docker compose up --build
```
Then open http://localhost:7860
