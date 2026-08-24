# Quality Anomaly Agent Runtime

This module contains the project-specific implementation for the semiconductor-equipment quality
anomaly demo. The public synthetic source fixtures remain in the adjacent
`projects/quality-anomaly-agent/fixtures/` directory.

## Workflow

```text
intake
-> validate_case
-> classify_scenario
-> plan_queries
-> fetch_qms_mes_erp_plm
-> retrieve_sop_fmea_8d_cases
-> build_evidence_graph
-> generate_hypothesis_matrix
-> validate_schema_and_evidence
-> await_human
-> supplement_or_finalize
```

The model may organize hypotheses but cannot create evidence IDs, decide production disposition,
or bypass the human checkpoint. Missing or conflicting evidence produces clarification/degraded
output instead of a root-cause claim.

## Implemented Batch B cases

- `incoming_material_001`: full Top 3 hypothesis and HITL path.
- `no_evidence`: clarification path without root-cause generation.
- `tool_timeout`: ERP bounded retry, partial evidence retention and degraded output.
