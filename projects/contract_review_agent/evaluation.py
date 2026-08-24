from __future__ import annotations

from projects.contract_review_agent.fixtures import CASE_IDS, load_contract_fixture
from projects.contract_review_agent.models import (
    ContractEvaluationReport,
    ContractMetrics,
    ContractRunReport,
)
from projects.contract_review_agent.runtime import run_contract_review


def _ratio(value: int, total: int, empty: float = 1.0) -> float:
    return round(value / total, 4) if total else empty


def evaluate_contract_cases() -> ContractEvaluationReport:
    reports: list[ContractRunReport] = [run_contract_review(case_id) for case_id in CASE_IDS]
    expected = {
        case_id: {
            item.finding_id: item for item in load_contract_fixture(case_id).expected.findings
        }
        for case_id in CASE_IDS
    }
    expected_ids = {item for cases in expected.values() for item in cases}
    actual_ids = {item.finding_id for report in reports for item in report.findings}
    critical_ids = {
        item.finding_id
        for case_id in CASE_IDS
        for item in load_contract_fixture(case_id).expected.findings
        if item.severity == "critical"
    }
    citations = [item for report in reports for item in report.findings]
    supported = sum(
        bool(item.clause_ids and (item.rule_id or item.policy_document_id)) for item in citations
    )
    high_risk = [item for item in citations if item.severity in {"high", "critical"}]
    intercepted = sum(
        item.human_required and item.human_status == "pending_legal_review" for item in high_risk
    )
    metrics = ContractMetrics(
        case_count=len(reports),
        critical_risk_recall=_ratio(len(critical_ids & actual_ids), len(critical_ids)),
        general_risk_recall=_ratio(len(expected_ids & actual_ids), len(expected_ids)),
        false_positive_rate=_ratio(len(actual_ids - expected_ids), len(actual_ids), empty=0.0),
        unsupported_finding_rate=_ratio(len(citations) - supported, len(citations), empty=0.0),
        citation_accuracy=_ratio(supported, len(citations)),
        human_interception_rate=_ratio(intercepted, len(high_risk)),
    )
    reasons: list[str] = []
    if metrics.critical_risk_recall < 1:
        reasons.append("critical_risk_recall")
    if metrics.unsupported_finding_rate > 0:
        reasons.append("unsupported_finding_rate")
    if metrics.citation_accuracy < 1:
        reasons.append("citation_accuracy")
    if metrics.human_interception_rate < 1:
        reasons.append("human_interception_rate")
    return ContractEvaluationReport(
        metrics=metrics,
        cases=reports,
        release_passed=not reasons,
        gate_reasons=reasons,
    )
