# Enterprise RAG Console

Static browser console for the public B2B supply-chain question-answering reconstruction. It visualizes query normalization, terminology rewrite, layered intent classification, RAG/Tool routing, evidence, permission decisions, clarification, and refusal.

```bash
pnpm --filter @portfolio/rag-console dev
```

The knowledge path is a public reconstruction. Inquiry, quotation, order, and logistics Tool results are clearly labeled simulated extensions. Custom input is limited to 500 Unicode characters, stays in the browser, and is excluded from exported Run Bundle v2 files.
