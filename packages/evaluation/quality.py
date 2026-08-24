"""Quality anomaly Agent metrics defined by the project's evaluation contract."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from packages.contracts.models import EvaluationMetrics, Evidence, Hypothesis, RunStatus


class QualityGateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metrics: EvaluationMetrics
    passed: bool
    failed_gates: list[str]


def _ratio(numerator: int, denominator: int, empty_value: float = 1.0) -> float:
    return empty_value if denominator == 0 else numerator / denominator


def evaluate_quality_run(
    *,
    evidence: list[Evidence],
    hypotheses: list[Hypothesis],
    status: RunStatus,
    human_required: bool,
) -> QualityGateResult:
    evidence_ids = {item.evidence_id for item in evidence}
    references = [
        evidence_id
        for hypothesis in hypotheses
        for evidence_id in hypothesis.supporting_evidence_ids + hypothesis.counter_evidence_ids
    ]
    resolved = sum(reference in evidence_ids for reference in references)
    unsupported = sum(
        hypothesis.deterministic_conclusion or not hypothesis.supporting_evidence_ids
        for hypothesis in hypotheses
    )
    counter_candidates = [
        hypothesis
        for hypothesis in hypotheses
        if hypothesis.missing_information or len(evidence) > 1
    ]
    counter_covered = sum(bool(item.counter_evidence_ids) for item in counter_candidates)
    human_triggered = status in {RunStatus.AWAITING_HUMAN, RunStatus.COMPLETED}

    metrics = EvaluationMetrics(
        schema_compliance=1.0,
        evidence_resolvability=_ratio(resolved, len(references)),
        unsupported_conclusion_rate=_ratio(unsupported, len(hypotheses), empty_value=0.0),
        counter_evidence_coverage=_ratio(counter_covered, len(counter_candidates)),
        human_boundary_accuracy=float(human_triggered == human_required),
    )
    failed: list[str] = []
    if metrics.schema_compliance < 1:
        failed.append("schema_compliance")
    if metrics.evidence_resolvability < 1:
        failed.append("evidence_resolvability")
    if metrics.unsupported_conclusion_rate > 0:
        failed.append("unsupported_conclusion_rate")
    if metrics.counter_evidence_coverage < 1 and hypotheses:
        failed.append("counter_evidence_coverage")
    if metrics.human_boundary_accuracy < 1:
        failed.append("human_boundary_accuracy")
    return QualityGateResult(metrics=metrics, passed=not failed, failed_gates=failed)
