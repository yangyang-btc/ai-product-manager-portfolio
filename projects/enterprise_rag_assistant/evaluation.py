from __future__ import annotations

from projects.enterprise_rag_assistant.cases import QUERY_CASES
from projects.enterprise_rag_assistant.models import (
    EnterpriseEvaluationReport,
    EnterpriseMetrics,
    EnterpriseRunReport,
)
from projects.enterprise_rag_assistant.runtime import run_enterprise_query


def _ratio(value: int, total: int, empty: float = 1.0) -> float:
    return round(value / total, 4) if total else empty


def evaluate_enterprise_cases() -> EnterpriseEvaluationReport:
    reports: list[EnterpriseRunReport] = [run_enterprise_query(case_id) for case_id in QUERY_CASES]
    intent_correct = sum(
        report.intent.level_1 == QUERY_CASES[report.case_id].expected_l1
        and report.intent.level_2 == QUERY_CASES[report.case_id].expected_l2
        for report in reports
    )
    route_correct = sum(
        report.route == QUERY_CASES[report.case_id].expected_route for report in reports
    )
    constrained = [report for report in reports if report.protected_constraints]
    preserved = sum(
        all(item in report.rewritten_query for item in report.protected_constraints)
        for report in constrained
    )
    citations = [item for report in reports for item in report.answer.citations]
    valid_citations = sum(item.citation_id.startswith(("CIT-DEMO-", "TOOL-")) for item in citations)
    factual_reports = [report for report in reports if report.answer.facts]
    faithful = sum(
        bool(report.answer.citations) or report.result_type in {"clarification", "refusal"}
        for report in factual_reports
    )
    refusal_cases = [
        report for report in reports if QUERY_CASES[report.case_id].expected_route == "refuse"
    ]
    clarification_cases = [
        report
        for report in reports
        if QUERY_CASES[report.case_id].expected_route in {"clarify", "version_check"}
    ]
    permission_cases = [
        report
        for report in reports
        if QUERY_CASES[report.case_id].expected_route == "permission_stop"
    ]
    metrics = EnterpriseMetrics(
        case_count=len(reports),
        intent_accuracy=_ratio(intent_correct, len(reports)),
        route_accuracy=_ratio(route_correct, len(reports)),
        rewrite_fidelity=_ratio(preserved, len(constrained)),
        citation_accuracy=_ratio(valid_citations, len(citations)),
        faithfulness=_ratio(faithful, len(factual_reports)),
        refusal_accuracy=_ratio(
            sum(item.result_type == "refusal" for item in refusal_cases), len(refusal_cases)
        ),
        clarification_accuracy=_ratio(
            sum(item.result_type == "clarification" for item in clarification_cases),
            len(clarification_cases),
        ),
        permission_interception=_ratio(
            sum(item.result_type == "permission_denied" for item in permission_cases),
            len(permission_cases),
        ),
    )
    reasons = [
        name
        for name, value in metrics.model_dump().items()
        if isinstance(value, float) and value < 1
    ]
    return EnterpriseEvaluationReport(
        metrics=metrics, cases=reports, release_passed=not reasons, gate_reasons=reasons
    )
