from __future__ import annotations

import json
from pathlib import Path

from packages.model_gateway import GatewayConfig
from projects.enterprise_rag_assistant.cases import QUERY_CASE_COLLECTION, QUERY_CASES
from projects.enterprise_rag_assistant.evaluation import evaluate_enterprise_cases
from projects.enterprise_rag_assistant.runtime import (
    load_enterprise_data_fixture,
    normalize_enterprise_report,
    run_enterprise_query,
)
from projects.enterprise_rag_assistant.taxonomy import INTENT_DEFINITIONS, classify_intent


def test_all_intent_definitions_have_executable_examples() -> None:
    assert len(INTENT_DEFINITIONS) == 24
    assert len({item.level_2 for item in INTENT_DEFINITIONS}) == 24
    for definition in INTENT_DEFINITIONS:
        match = classify_intent(definition.example)
        assert (match.level_1, match.level_2) == (
            definition.level_1,
            definition.level_2,
        )


def test_query_cases_and_business_data_are_versioned_canonical_fixtures() -> None:
    assert QUERY_CASE_COLLECTION.dataset_version == "enterprise-query-cases-v1"
    assert QUERY_CASE_COLLECTION.synthetic is True
    assert QUERY_CASE_COLLECTION.source_label == "公开模拟数据"
    assert len(QUERY_CASES) == 10

    fixture = load_enterprise_data_fixture()
    assert fixture.dataset_version == "enterprise-business-data-v1"
    assert fixture.knowledge_data.source_type == "public_reconstruction"
    assert fixture.realtime_data.source_type == "simulated_extension"
    supplier_ids = {item.supplier_id for item in fixture.knowledge_data.suppliers}
    inquiry_ids = {fixture.realtime_data.inquiry.inquiry_id}
    assert all(
        item.supplier_id in supplier_ids for item in fixture.knowledge_data.relationships
    )
    assert all(item.supplier_id in supplier_ids for item in fixture.realtime_data.quotations)
    assert all(item.inquiry_id in inquiry_ids for item in fixture.realtime_data.quotations)


def test_compound_query_separates_knowledge_from_realtime_tool() -> None:
    report = run_enterprise_query("compound_query_001")
    assert report.route == "rag_and_tool"
    assert report.result_type == "table"
    assert report.answer.facts == [
        "具备精密清洗有效供应证据的供应商有 2 家。",
        "当前询价已有 2 家提交报价。",
    ]
    assert {item.source_type for item in report.answer.citations} == {"knowledge", "tool"}
    assert "当前" in report.protected_constraints


def test_refusal_clarification_permission_and_version_paths_are_explicit() -> None:
    refusal = run_enterprise_query("no_answer_001")
    clarification = run_enterprise_query("missing_constraint_001")
    permission = run_enterprise_query("permission_denied_001")
    conflict = run_enterprise_query("conflicting_sources_001")
    assert refusal.result_type == "refusal" and "NO_EVIDENCE_REFUSAL" in refusal.warnings
    assert clarification.result_type == "clarification"
    assert permission.result_type == "permission_denied" and not permission.answer.citations
    assert (
        conflict.result_type == "clarification" and "SOURCE_VERSION_CONFLICT" in conflict.warnings
    )


def test_boundary_and_tool_routes_never_call_or_defer_to_real_model() -> None:
    unreachable_real_model = GatewayConfig(
        provider="openai-compatible",
        base_url="http://127.0.0.1:1/v1",
        api_key="not-used",
        model="not-used",
        timeout_seconds=0.01,
    )
    for case_id in (
        "compound_query_001",
        "realtime_order_001",
        "missing_constraint_001",
        "no_answer_001",
        "permission_denied_001",
        "conflicting_sources_001",
    ):
        report = run_enterprise_query(case_id, unreachable_real_model)
        assert report.model_provider == "mock"


def test_rewrite_preserves_hard_business_constraints() -> None:
    report = run_enterprise_query("rewrite_fidelity_001")
    assert report.protected_constraints == ["华东", "两周内", "ISO", "交期"]
    assert all(item in report.rewritten_query for item in report.protected_constraints)


def test_enterprise_evaluation_enforces_all_safety_and_quality_gates() -> None:
    evaluation = evaluate_enterprise_cases()
    assert evaluation.release_passed is True
    assert evaluation.metrics.case_count == 10
    for name, value in evaluation.metrics.model_dump().items():
        if isinstance(value, float):
            assert value == 1, name


def test_python_runtime_matches_browser_parity_golden() -> None:
    golden_path = Path(__file__).parent / "golden" / "rag-browser-parity.json"
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    reports = [
        normalize_enterprise_report(run_enterprise_query(case_id))
        for case_id in QUERY_CASES
    ]
    assert reports == golden
