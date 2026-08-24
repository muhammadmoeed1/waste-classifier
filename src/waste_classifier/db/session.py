"""Engine/session factory and a fire-and-forget write helper.

SQLite is the local/dev default; the schema in models.py avoids any
SQLite-only types so swapping DATABASE_URL to a Postgres URL (Phase 4 deploy)
is a config change, not a migration.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from waste_classifier import config

logger = logging.getLogger(__name__)

# SQLite connections are single-thread by default; FastAPI's sync `def` handlers
# run in a threadpool, so a shared engine needs check_same_thread disabled.
# Irrelevant (and unset) for Postgres.
_connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(config.DATABASE_URL, connect_args=_connect_args)


def init_db() -> None:
    """Create tables if they don't exist yet. Safe to call on every startup."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a database session."""
    with Session(engine) as session:
        yield session


def safe_write(record: SQLModel) -> None:
    """Persist one row. Never raises -- intended to run as a FastAPI
    BackgroundTask after the response has already been computed, so a
    persistence failure (or a locked/unreachable DB) never breaks the
    user-facing prediction or chat answer."""
    try:
        with Session(engine) as session:
            session.add(record)
            session.commit()
    except Exception:
        logger.exception("Failed to persist %s", type(record).__name__)
