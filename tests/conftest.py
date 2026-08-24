"""Shared pytest fixtures."""

import pytest


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """The rate limiter's counters live on the module-level `app` singleton,
    which is reused across every test in the session (module imports are
    cached) -- without a reset, requests from one test toward a rate-limited
    endpoint would count against a completely unrelated later test."""
    yield
    try:
        from waste_classifier.api.main import limiter

        limiter.reset()
    except ImportError:
        pass
