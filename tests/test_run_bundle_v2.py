from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]
from pydantic import ValidationError

from apps.evaluation_lab.lab_core import (
    local_bundle_import_enabled,
    parse_local_run_bundle,
)
from packages.agent_core import assert_bundle_safe
from packages.contracts import (
    BundleV2Citation,
    BundleV2Claim,
    BundleV2Identity,
    BundleV2Node,
    BundleV2Result,
    EvaluationMetrics,
    RunBundle,
    RunBundleV2,
    RunStatus,
    SourceType,
)
from packages.contracts.models import BundleIdentity

SCHEMA_PATH = (
    Path(__file__).parents[1]
    / "packages"
    / "contracts"
    / "schemas"
    / "run-bundle-v2.schema.json"
)


def make_v2_bundle() -> RunBundleV2:
    return RunBundleV2(
        project_id="contract-review-agent",
        case_id="procurement_contract_001",
        run_id="contract-run-001",
        trace_id="contract-trace-001",
        status=RunStatus.AWAITING_HUMAN,
        identity=BundleV2Identity(
            workflow_version="contract-workflow-v1",
            dataset_version="contract-fixtures-v1",
            rules_version="contract-rules-v1",
            prompt_or_policy_version="contract-policy-v1",
            runtime_version="contract-browser-v1",
            seed=42,
        ),
        nodes=[
            BundleV2Node(
                sequence=1,
                node="deterministic_rules",
                status="completed",
                duration_ms=4,
                input_count=2,
                output_count=1,
                source_type=SourceType.PUBLIC_RECONSTRUCTION,
            )
        ],
        citations=[
            BundleV2Citation(
                citation_id="RULE-PROC-012",
                public_summary="付款节点应晚于来料验收。",
                source_type=SourceType.PUBLIC_RECONSTRUCTION,
            )
        ],
        results=[
            BundleV2Result(
                result_id="RF-DEMO-001",
                result_type="finding",
                summary="付款节点早于来料验收完成。",
                citation_ids=["RULE-PROC-012"],
                source_type=SourceType.SIMULATED_RUN_RESULT,
            )
        ],
        claims=[
            BundleV2Claim(
                statement="本次结果来自公开模拟合同。",
                source_type=SourceType.SIMULATED_RUN_RESULT,
            )
        ],
        estimated_tokens=0,
        estimated_cost_usd=0,
        warnings=[],
        generated_at=datetime(2026, 8, 23, tzinfo=UTC),
    )


def make_v1_payload() -> dict[str, object]:
    bundle = RunBundle(
        run_id="quality-run-001",
        case_id="incoming_material_001",
        scenario="incoming",
        status=RunStatus.COMPLETED,
        identity=BundleIdentity(
            workflow_version="quality-workflow-v1",
            dataset_version="quality-fixtures-v1",
            prompt_version="quality-prompt-v1",
            config_version="quality-config-v1",
            model_provider="mock",
            seed=42,
        ),
        nodes=[],
        evidence=[],
        hypotheses=[],
        metrics=EvaluationMetrics(
            schema_compliance=1,
            evidence_resolvability=1,
            unsupported_conclusion_rate=0,
            counter_evidence_coverage=1,
            human_boundary_accuracy=1,
        ),
        estimated_tokens=0,
        estimated_cost_usd=0,
        warnings=[],
        generated_at=datetime(2026, 8, 23, tzinfo=UTC),
    )
    return bundle.model_dump(mode="json")


def test_v2_model_matches_the_versioned_json_schema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    validator.validate(make_v2_bundle().model_dump(mode="json"))


def test_v2_rejects_unresolved_citations_and_extra_fields() -> None:
    payload = make_v2_bundle().model_dump(mode="json")
    results = payload["results"]
    assert isinstance(results, list)
    assert isinstance(results[0], dict)
    results[0]["citation_ids"] = ["MISSING-CITATION"]
    with pytest.raises(ValidationError, match="unresolved citation_ids"):
        RunBundleV2.model_validate(payload)

    clean = make_v2_bundle().model_dump(mode="json")
    clean["raw_prompt"] = "forbidden"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RunBundleV2.model_validate(clean)


def test_historical_source_requires_an_approved_fact_or_claim_id() -> None:
    with pytest.raises(ValidationError, match="requires fact_id or claim_id"):
        BundleV2Claim(
            statement="Unapproved historical statement",
            source_type=SourceType.HISTORICAL_PROJECT_FACT,
        )
    approved = BundleV2Claim(
        statement="Approved historical statement",
        source_type=SourceType.HISTORICAL_PROJECT_FACT,
        fact_id="ER-F003",
    )
    assert approved.fact_id == "ER-F003"


def test_local_parser_migrates_v1_and_accepts_v2_but_rejects_future_versions() -> None:
    migrated = parse_local_run_bundle(make_v1_payload())
    assert migrated["schema_version"] == 2
    assert migrated["project_id"] == "quality-anomaly-agent"
    assert "migrated_from_v1" in migrated["warnings"]

    current = parse_local_run_bundle(make_v2_bundle().model_dump(mode="json"))
    assert current["schema_version"] == 2
    assert current["project_id"] == "contract-review-agent"

    with pytest.raises(ValueError, match="Unsupported Run Bundle"):
        parse_local_run_bundle({"schema_version": 3})


def test_bundle_safety_rejects_absolute_paths() -> None:
    bundle = make_v2_bundle()
    local_path = "/" + "Users/example/private/report.json"
    unsafe = bundle.model_copy(update={"warnings": [local_path]})
    with pytest.raises(ValueError, match="absolute_path"):
        assert_bundle_safe(unsafe)


def test_bundle_import_requires_explicit_local_mode() -> None:
    assert local_bundle_import_enabled(None) is False
    assert local_bundle_import_enabled("public") is False
    assert local_bundle_import_enabled("local") is True
