"""Phase 3.3: the REGION config toggle.

REGION defaults to "generic" (unchanged existing behavior). Setting REGION=pk
should swap the default knowledge base directory to data/knowledge_base/pk,
without requiring KNOWLEDGE_BASE_DIR to be set explicitly. Follows the same
monkeypatch-env-var + importlib.reload pattern already used for RAG_BACKEND in
tests/test_lightweight_rag.py.
"""

from __future__ import annotations

import importlib


def test_region_defaults_to_generic_and_generic_knowledge_base_dir():
    from waste_classifier import config

    assert config.REGION == "generic"
    assert config.KNOWLEDGE_BASE_DIR == config.ROOT_DIR / "data" / "knowledge_base"


def test_default_knowledge_base_dir_helper_maps_pk_and_generic():
    from waste_classifier import config

    assert config._default_knowledge_base_dir("pk") == (
        config.ROOT_DIR / "data" / "knowledge_base" / "pk"
    )
    assert config._default_knowledge_base_dir("generic") == (
        config.ROOT_DIR / "data" / "knowledge_base"
    )
    # Unknown values fall back to the generic (existing-behavior) directory.
    assert config._default_knowledge_base_dir("unknown") == (
        config.ROOT_DIR / "data" / "knowledge_base"
    )


def test_region_pk_env_var_switches_the_loaded_knowledge_base_dir(monkeypatch):
    """Reload config with REGION=pk set and confirm KNOWLEDGE_BASE_DIR points at
    the pk/ subdirectory, and that it actually contains distinct, pk-specific
    content (not just a differently-named copy of the generic docs)."""
    from waste_classifier import config
    from waste_classifier.rag.knowledge_base import load_knowledge_base

    monkeypatch.setenv("REGION", "pk")
    importlib.reload(config)
    try:
        assert config.REGION == "pk"
        assert config.KNOWLEDGE_BASE_DIR == config.ROOT_DIR / "data" / "knowledge_base" / "pk"
        assert config.KNOWLEDGE_BASE_DIR.is_dir()

        chunks = load_knowledge_base(config.KNOWLEDGE_BASE_DIR)
        assert len(chunks) > 5
        doc_ids = {c.doc_id for c in chunks}
        assert "metal" in doc_ids

        combined_text = "\n".join(c.text for c in chunks).lower()
        assert "kabaria" in combined_text
        assert "pkr" in combined_text
    finally:
        monkeypatch.delenv("REGION", raising=False)
        importlib.reload(config)
        assert config.REGION == "generic"
        assert config.KNOWLEDGE_BASE_DIR == config.ROOT_DIR / "data" / "knowledge_base"


def test_explicit_knowledge_base_dir_env_var_overrides_region_default(monkeypatch, tmp_path):
    """An explicit KNOWLEDGE_BASE_DIR should still win over the REGION-derived
    default, matching the existing env-driven config pattern."""
    from waste_classifier import config

    monkeypatch.setenv("REGION", "pk")
    monkeypatch.setenv("KNOWLEDGE_BASE_DIR", str(tmp_path))
    importlib.reload(config)
    try:
        assert config.KNOWLEDGE_BASE_DIR == tmp_path
    finally:
        monkeypatch.delenv("REGION", raising=False)
        monkeypatch.delenv("KNOWLEDGE_BASE_DIR", raising=False)
        importlib.reload(config)
