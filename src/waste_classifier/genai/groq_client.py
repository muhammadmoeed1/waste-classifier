"""Thin wrapper around the Groq API client."""

from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from typing import Any, TypeVar

import groq
from fastapi import HTTPException
from groq import Groq

from waste_classifier import config

GROQ_TIMEOUT_SECONDS = 30.0

T = TypeVar("T")


@lru_cache(maxsize=1)
def get_client() -> Groq:
    if not config.GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Get a free key at https://console.groq.com "
            "and set it in your .env file."
        )
    return Groq(api_key=config.GROQ_API_KEY, timeout=GROQ_TIMEOUT_SECONDS)


def safe_call(fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Call a Groq SDK function, mapping SDK exceptions to clean HTTP errors.

    Wrap any client.*.create(...) call with this so an upstream Groq failure
    (rate limit, auth, model not found, connection drop, ...) surfaces as a
    502/504 with a useful detail message instead of an unhandled 500.
    """
    try:
        return fn(*args, **kwargs)
    except groq.APITimeoutError as exc:
        raise HTTPException(
            status_code=504, detail="The AI service timed out. Please try again."
        ) from exc
    except groq.GroqError as exc:
        raise HTTPException(status_code=502, detail=f"AI service error: {exc}") from exc
