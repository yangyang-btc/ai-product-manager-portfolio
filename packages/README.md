# Shared Packages

These packages contain versioned, business-independent contracts designed for reuse by all three
project runtimes. Project-specific workflow nodes and field mappings remain under `projects/`.

Implemented in Batch B:

- `contracts`: strict Pydantic API, Trace, metric, hypothesis and Run Bundle schemas.
- `model_gateway`: deterministic mock and bounded OpenAI-compatible providers.
- `retrieval`: deterministic lexical/BM25 retrieval with versioned citations.
- `observability`: privacy-safe node timings, counts, warnings and estimated usage.
- `evaluation`: project metric calculation and release-gate results.
- `agent_core`: TTL state, token isolation, idempotency, action transitions and bundle scanning.
