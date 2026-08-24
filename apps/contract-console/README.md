# Contract Review Console

Static browser console for the public contract-review reconstruction. It loads six versioned synthetic semiconductor-equipment contract cases and executes the deterministic TypeScript runtime entirely in the browser.

```bash
pnpm --filter @portfolio/contract-console dev
```

The console does not accept uploads or API keys. A completed run can export a redacted Run Bundle v2; full clause text remains in the visible public fixture but is excluded from the bundle. Configure portfolio, Evaluation Lab, and source links with `VITE_PORTFOLIO_URL`, `VITE_EVALUATION_LAB_URL`, and `VITE_GITHUB_REPO_URL`.
