# Applications

Application boundaries:

- `portfolio-web`: personal GitHub Pages portfolio with project, methodology, Skills, research, and about routes.
- `quality-agent-web`: implemented React evidence console for the quality Agent.
- `contract-console`: static browser console for versioned contract review cases and human review decisions.
- `rag-console`: static browser console for B2B knowledge/Tool routing, evidence, permission, and refusal paths.
- `evaluation_lab`: implemented Streamlit dataset, experiment, metric, gate, and bad-case workbench.
- `quality_agent_api`: implemented FastAPI `/api/v1` backend for the quality Agent.

The API exposes run creation, snapshots, buffered SSE events, HITL actions, privacy-safe Trace,
Run Bundle export, and one-time Evaluation Lab handoff. Its online deployment remains fixed to
offline/mock mode; OpenAI-compatible mode is local-only. The React console hands a privacy-safe Run
Bundle to the lab through a one-time fragment credential, which is cleared from browser history before
redemption.
