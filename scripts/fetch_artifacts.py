"""Download the trained model artifacts from the GitHub Release, if they
aren't already present locally.

Run this before starting the server on any host where artifacts/ isn't
already populated (see docker/Dockerfile and docker/Dockerfile.lite, which
both run this at build time instead of COPYing the files from git).

Local dev doesn't need this: artifacts/waste_model.keras is already on disk
after cloning (or after running `python -m waste_classifier.ml.train`), so
the download is skipped.
"""

from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = "muhammadmoeed1/waste-classifier"
RELEASE_TAG = "model-v1"
ROOT_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT_DIR / "artifacts"

FILES = ["waste_model.keras", "class_names.json"]


def _download(filename: str) -> None:
    dest = ARTIFACTS_DIR / filename
    if dest.exists() and dest.stat().st_size > 0:
        print(f"[fetch_artifacts] {filename} already present, skipping")
        return

    url = f"https://github.com/{REPO}/releases/download/{RELEASE_TAG}/{filename}"
    print(f"[fetch_artifacts] downloading {url}")
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, dest)
    except urllib.error.URLError as exc:
        print(f"[fetch_artifacts] failed to download {filename}: {exc}", file=sys.stderr)
        raise


def main() -> None:
    for filename in FILES:
        _download(filename)


if __name__ == "__main__":
    main()
