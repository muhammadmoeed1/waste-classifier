# Future ideas

Ideas noticed while building a specific feature but deliberately not built (to
avoid scope creep on the task at hand). Captured here instead of lost.

## Pakistan-localized disposal guidance

- **Per-request region override.** `REGION` is currently a deploy-time env toggle
  (like `RAG_BACKEND`) — one running instance serves one region. A `region` field
  on `ChatRequest`, threaded through to `assistant.ask`/`agent.run_agent` and the
  knowledge-base lookup, would let a single deployment serve multiple regions/users
  without redeploying.
- **More region knowledge bases.** The `REGION`/`KNOWLEDGE_BASE_DIR` pattern
  generalizes cleanly to other informal-economy regions (e.g. India, Bangladesh,
  Nigeria) — would just need a new `data/knowledge_base/<region>/` directory and a
  system-prompt addendum, following the same shape as the `pk` one.
- **Multilingual embedding model.** The embeddings RAG backend uses
  `all-MiniLM-L6-v2`, which is English-centric; cross-lingual retrieval quality for
  the Urdu sections of the `pk` knowledge base is likely weaker than for the
  English sections. A multilingual sentence-transformer model would improve
  retrieval when a user asks a question in Urdu.
- **Live/crowd-sourced scrap rates.** `resale_pkr_per_kg` in `ml/impact.py` is a
  static, hand-picked illustrative estimate. A pluggable data source (e.g.
  periodically updated or user-submitted local rates) would make the resale
  estimates more accurate over time instead of fixed at authoring time.
- **Frontend region selector.** The web UI has a language toggle (`web/src/i18n.js`)
  but no region toggle — a user-facing region switch (rather than only a
  server-side env var) would let the same deployed frontend present the right
  region's guidance without a server redeploy.
