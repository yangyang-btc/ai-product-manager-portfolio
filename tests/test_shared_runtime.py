from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from packages.agent_core import ExpiredError, InMemoryRunRepository, assert_bundle_safe
from packages.contracts.models import (
    BundleIdentity,
    EvaluationMetrics,
    RunBundle,
)
from packages.model_gateway import GatewayConfig, ModelGateway
from packages.observability import TraceRecorder
from packages.retrieval import Document, lexical_search
from projects.quality_anomaly_agent.fixtures import load_fixture
from projects.quality_anomaly_agent.knowledge import retrieve_knowledge
from projects.quality_anomaly_agent.tools import fetch_business_evidence


def test_lexical_retrieval_is_deterministic_and_versioned() -> None:
    documents = [
        Document("D2", "V1", "密封面", "密封面污染导致检漏异常", "FMEA"),
        Document("D1", "V2", "夹具", "氦检治具污染影响漏率", "CASE"),
    ]
    first = lexical_search("氦质谱检漏夹具污染", documents, top_k=2)
    second = lexical_search("氦质谱检漏夹具污染", documents, top_k=2)
    assert first == second
    assert [item.document.document_id for item in first] == ["D1", "D2"]
    assert all(item.document.version for item in first)


def test_mock_gateway_only_references_resolvable_evidence() -> None:
    fixture = load_fixture("incoming_material_001")
    evidence = fetch_business_evidence(fixture).evidence + retrieve_knowledge(fixture)
    response = ModelGateway().generate_hypotheses(
        case_id="incoming_material_001", evidence=evidence
    )
    known = {item.evidence_id for item in evidence}
    assert len(response.hypotheses) == 3
    assert all(
        set(item.supporting_evidence_ids + item.counter_evidence_ids) <= known
        for item in response.hypotheses
    )
    assert all(not item.deterministic_conclusion for item in response.hypotheses)


def test_public_mode_and_kill_switch_force_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_MODE", "public")
    monkeypatch.setenv("MODEL_PROVIDER", "openai-compatible")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "should-not-be-used")
    assert GatewayConfig.from_env().provider == "mock"

    monkeypatch.setenv("APP_MODE", "offline")
    monkeypatch.setenv("MODEL_KILL_SWITCH", "1")
    assert GatewayConfig.from_env().provider == "mock"


def test_repository_tokens_are_isolated_and_ttl_is_enforced() -> None:
    repository: InMemoryRunRepository[dict[str, str]] = InMemoryRunRepository(ttl_minutes=30)
    record, token, _, _ = repository.create(
        case_id="case_a", scenario="incoming", state={}, idempotency_key=None
    )
    assert repository.get(record.run_id, token) is record
    record.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    with pytest.raises(ExpiredError):
        repository.get(record.run_id, token)


def test_run_bundle_rejects_extra_fields_and_pii() -> None:
    now = datetime.now(UTC)
    base = {
        "schema_version": 1,
        "run_id": "run_safe",
        "case_id": "incoming_material_001",
        "scenario": "incoming",
        "status": "completed",
        "identity": BundleIdentity(
            workflow_version="v1",
            dataset_version="v1",
            prompt_version="v1",
            config_version="v1",
            model_provider="mock",
            seed=42,
        ),
        "nodes": [],
        "evidence": [],
        "hypotheses": [],
        "metrics": EvaluationMetrics(
            schema_compliance=1,
            evidence_resolvability=1,
            unsupported_conclusion_rate=0,
            counter_evidence_coverage=1,
            human_boundary_accuracy=1,
        ),
        "estimated_tokens": 0,
        "estimated_cost_usd": 0,
        "warnings": [],
        "generated_at": now,
    }
    with pytest.raises(ValidationError):
        RunBundle.model_validate({**base, "raw_prompt": "forbidden"})

    unsafe = RunBundle.model_validate({**base, "warnings": ["contact a.user@example.com"]})
    with pytest.raises(ValueError, match="email"):
        assert_bundle_safe(unsafe)


def test_trace_records_counts_without_raw_payloads() -> None:
    trace = TraceRecorder("trace_test")
    trace.start("retrieve", input_count=2)
    trace.complete("retrieve", output_count=1, warning_codes=["DEGRADED"])
    view = trace.view()
    assert view.nodes[0].input_count == 2
    assert view.nodes[0].output_count == 1
    assert not hasattr(view.nodes[0], "raw_input")
