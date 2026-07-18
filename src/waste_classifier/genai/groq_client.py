"""Thin wrapper around the Groq API client."""

from __future__ import annotations

from functools import lru_cache

from groq import Groq

from waste_classifier import config


@lru_cache(maxsize=1)
def get_client() -> Groq:
    if not config.GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Get a free key at https://console.groq.com "
            "and set it in your .env file."
        )
    return Groq(api_key=config.GROQ_API_KEY)
