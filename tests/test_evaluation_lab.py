from __future__ import annotations

from apps.evaluation_lab.lab_core import (
    BAD_CASES,
    ExperimentConfig,
    compare_versions,
    load_retrieval_dataset,
    load_versioned_project_report,
    local_bundle_import_enabled,
    run_retrieval_experiment,
)
from projects.contract_review_agent.evaluation import evaluate_contract_cases
from projects.enterprise_rag_assistant.evaluation import evaluate_enterprise_cases


def test_retrieval_dataset_is_versioned_and_domain_realistic() -> None:
    dataset = load_retrieval_dataset()
    assert dataset.dataset_id == "quality-retrieval-v1"
    assert dataset.source_label == "公开模拟数据"
    assert len(dataset.documents) == 6
    assert len(dataset.relevant_document_ids) == 3
    assert {item.source for item in dataset.documents} >= {"CASE", "FMEA", "SOP"}


def test_top_k_experiment_is_deterministic_and_exposes_cost_tradeoff() -> None:
    top_3 = run_retrieval_experiment(ExperimentConfig(top_k=3, score_threshold=0, rerank=False))
    repeated = run_retrieval_experiment(ExperimentConfig(top_k=3, score_threshold=0, rerank=False))
    top_5 = run_retrieval_experiment(ExperimentConfig(top_k=5, score_threshold=0, rerank=False))
    assert top_3 == repeated
    assert top_3.recall_at_k == 1
    assert top_5.estimated_tokens > top_3.estimated_tokens


def test_release_gate_blocks_a_retrieval_regression() -> None:
    baseline = run_retrieval_experiment(ExperimentConfig(top_k=3, score_threshold=0, rerank=False))
    regression = run_retrieval_experiment(
        ExperimentConfig(top_k=1, score_threshold=0, rerank=False)
    )
    comparison = compare_versions(baseline, regression)
    assert comparison.release_passed is False
    assert comparison.recall_delta < 0
    assert "recall_regression" in comparison.gate_reasons


def test_bad_cases_map_to_regression_layers() -> None:
    assert BAD_CASES["no_evidence"]["category"] == "data"
    assert BAD_CASES["tool_timeout"]["category"] == "tool"
    assert all(item["regression_assertion"] for item in BAD_CASES.values())


def test_other_projects_expose_versioned_read_only_evaluation_reports() -> None:
    contract = load_versioned_project_report("contract-review-agent")
    enterprise = load_versioned_project_report("enterprise-rag-assistant")
    contract_runtime = evaluate_contract_cases()
    enterprise_runtime = evaluate_enterprise_cases()
    assert contract["release_passed"] is True
    assert contract["metrics"]["case_count"] == 4
    assert enterprise["release_passed"] is True
    assert enterprise["metrics"]["case_count"] == 10
    assert contract["metric_definition_version"] == (
        contract_runtime.metrics.metric_definition_version
    )
    assert enterprise["metric_definition_version"] == (
        enterprise_runtime.metrics.metric_definition_version
    )
    for key, value in contract["metrics"].items():
        assert contract_runtime.metrics.model_dump()[key] == value
    for key, value in enterprise["metrics"].items():
        assert enterprise_runtime.metrics.model_dump()[key] == value


def test_public_lab_does_not_enable_bundle_upload() -> None:
    assert local_bundle_import_enabled("public") is False
    assert local_bundle_import_enabled("local") is True
