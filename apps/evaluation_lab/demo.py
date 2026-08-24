"""CLI smoke path for the deterministic evaluation and release gate."""

from __future__ import annotations

import json

from apps.evaluation_lab.lab_core import (
    ExperimentConfig,
    compare_versions,
    run_retrieval_experiment,
)


def main() -> None:
    baseline = run_retrieval_experiment(
        ExperimentConfig(top_k=3, score_threshold=0, rerank=False)
    )
    candidate = run_retrieval_experiment(
        ExperimentConfig(top_k=5, score_threshold=0, rerank=False)
    )
    result = compare_versions(baseline, candidate)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
