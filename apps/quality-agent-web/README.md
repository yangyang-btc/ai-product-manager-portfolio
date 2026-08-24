# Quality Agent Evidence Console

React interface for the quality anomaly Agent. It renders the backend workflow as an evidence rail,
node timeline, evidence ledger, hypothesis matrix, human checkpoint, and privacy-safe run artifacts.

Run locally after starting the API on port 8000:

```bash
pnpm --filter @portfolio/quality-agent-web dev
```

The browser never accepts an API key. `VITE_API_URL` may point to another `/api/v1` deployment; the
default is `http://localhost:8000`. The three built-in cases cover the standard, no-evidence, and
tool-timeout paths.
