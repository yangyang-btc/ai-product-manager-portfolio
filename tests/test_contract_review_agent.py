from __future__ import annotations

import json
from pathlib import Path

from projects.contract_review_agent.evaluation import evaluate_contract_cases
from projects.contract_review_agent.fixtures import (
    CASE_IDS,
    PUBLIC_FIXTURE_IDS,
    load_contract_fixture,
)
from projects.contract_review_agent.runtime import (
    normalize_contract_report,
    run_contract_review,
)


def test_all_four_contract_types_have_runnable_domain_fixtures() -> None:
    fixtures = [load_contract_fixture(case_id) for case_id in CASE_IDS]
    assert {item.contract.contract_type for item in fixtures} == {
        "procurement",
        "sales",
        "nda",
        "technical_cooperation",
    }
    assert all(item.synthetic and item.source_label == "公开模拟数据" for item in fixtures)


def test_public_contract_fixtures_include_negative_and_cross_clause_boundaries() -> None:
    fixtures = {case_id: load_contract_fixture(case_id) for case_id in PUBLIC_FIXTURE_IDS}
    assert set(fixtures) == {
        "procurement_contract_001",
        "sales_contract_001",
        "nda_001",
        "technical_cooperation_001",
        "procurement_safe_001",
        "cross_clause_context_loss",
    }
    assert fixtures["procurement_safe_001"].expected.findings == []
    boundary = fixtures["cross_clause_context_loss"]
    assert boundary.expected.findings[0].clause_ids == [
        "CL-LIMIT-BOUNDARY-001",
        "CL-ATTACH-BOUNDARY-001",
    ]
    for fixture in fixtures.values():
        known_clauses = {item.clause_id for item in fixture.contract.clauses}
        known_rules = {item.rule_id for item in fixture.rules}
        assert all(set(item.clause_ids) <= known_clauses for item in fixture.expected.findings)
        assert all(
            item.rule_id is None or item.rule_id in known_rules
            for item in fixture.expected.findings
        )


def test_procurement_review_preserves_cross_clause_risk_and_human_boundary() -> None:
    report = run_contract_review("procurement_contract_001")
    assert report.status == "awaiting_human"
    assert [item.finding_id for item in report.findings] == ["RF-DEMO-002", "RF-DEMO-001"]
    assert all(item.source == "rule_and_cross_clause" for item in report.findings)
    assert all(item.human_status == "pending_legal_review" for item in report.findings)
    assert len(report.trace) == 10


def test_semantic_contract_cases_remain_evidence_bound() -> None:
    for case_id in ("nda_001", "technical_cooperation_001"):
        report = run_contract_review(case_id)
        fixture = load_contract_fixture(case_id)
        known = {item.clause_id for item in fixture.contract.clauses}
        assert report.model_provider == "mock"
        assert all(set(item.clause_ids) <= known for item in report.findings)
        assert all(item.rule_id and item.policy_document_id for item in report.findings)


def test_contract_evaluation_enforces_release_gates() -> None:
    evaluation = evaluate_contract_cases()
    assert evaluation.release_passed is True
    assert evaluation.metrics.case_count == 4
    assert evaluation.metrics.critical_risk_recall == 1
    assert evaluation.metrics.general_risk_recall == 1
    assert evaluation.metrics.false_positive_rate == 0
    assert evaluation.metrics.unsupported_finding_rate == 0
    assert evaluation.metrics.human_interception_rate == 1


def test_python_runtime_matches_browser_parity_golden() -> None:
    golden_path = Path(__file__).parent / "golden" / "contract-browser-parity.json"
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    reports = [
        normalize_contract_report(run_contract_review(case_id))
        for case_id in PUBLIC_FIXTURE_IDS
    ]
    assert reports == golden
