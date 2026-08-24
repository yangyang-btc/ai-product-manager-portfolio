"""Run Bundle v2 contracts for deterministic browser runtimes.

Version 1 remains the Quality Agent wire format. Version 2 is a generic,
strict export contract for the contract and enterprise-RAG browser runtimes.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from packages.contracts.models import RunBundle, RunStatus


class BundleV2Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceType(StrEnum):
    HISTORICAL_PROJECT_FACT = "historical_project_fact"
    PUBLIC_RECONSTRUCTION = "public_reconstruction"
    SIMULATED_RUN_RESULT = "simulated_run_result"
    SIMULATED_EXTENSION = "simulated_extension"


class SourceAnnotated(BundleV2Model):
    source_type: SourceType
    fact_id: str | None = Field(default=None, pattern=r"^[A-Z]{2}-F[0-9]{3}$")
    claim_id: str | None = Field(default=None, pattern=r"^[A-Z]{2}-C[0-9]{3}$")

    @model_validator(mode="after")
    def historical_sources_require_an_approved_reference(self) -> Self:
        if (
            self.source_type == SourceType.HISTORICAL_PROJECT_FACT
            and self.fact_id is None
            and self.claim_id is None
        ):
            raise ValueError("historical_project_fact requires fact_id or claim_id")
        return self


class BundleV2Identity(BundleV2Model):
    workflow_version: str = Field(min_length=1, max_length=80)
    dataset_version: str = Field(min_length=1, max_length=80)
    rules_version: str = Field(min_length=1, max_length=80)
    prompt_or_policy_version: str = Field(min_length=1, max_length=80)
    runtime_version: str = Field(min_length=1, max_length=80)
    model_provider: Literal["mock"] = "mock"
    seed: int


class BundleV2Node(SourceAnnotated):
    sequence: int = Field(ge=1)
    node: str = Field(min_length=1, max_length=100)
    status: Literal["completed", "failed", "skipped"]
    duration_ms: int = Field(ge=0)
    input_count: int = Field(ge=0)
    output_count: int = Field(ge=0)
    warning_codes: list[str] = Field(default_factory=list, max_length=20)


class BundleV2Citation(SourceAnnotated):
    citation_id: str = Field(min_length=1, max_length=100)
    public_summary: str = Field(min_length=1, max_length=500)


class BundleV2Result(SourceAnnotated):
    result_id: str = Field(min_length=1, max_length=100)
    result_type: Literal["finding", "answer", "clarification", "refusal", "human_gate"]
    summary: str = Field(min_length=1, max_length=1000)
    citation_ids: list[str] = Field(default_factory=list, max_length=50)


class BundleV2Claim(SourceAnnotated):
    statement: str = Field(min_length=1, max_length=500)


class RunBundleV2(BundleV2Model):
    schema_version: Literal[2] = 2
    project_id: Literal[
        "quality-anomaly-agent",
        "contract-review-agent",
        "enterprise-rag-assistant",
    ]
    case_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9_]+$")
    run_id: str = Field(min_length=1, max_length=120)
    trace_id: str = Field(min_length=1, max_length=120)
    status: RunStatus
    identity: BundleV2Identity
    nodes: list[BundleV2Node] = Field(max_length=100)
    citations: list[BundleV2Citation] = Field(default_factory=list, max_length=200)
    results: list[BundleV2Result] = Field(default_factory=list, max_length=100)
    claims: list[BundleV2Claim] = Field(default_factory=list, max_length=100)
    estimated_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)
    warnings: list[str] = Field(default_factory=list, max_length=50)
    generated_at: datetime

    @model_validator(mode="after")
    def citations_must_resolve(self) -> Self:
        known = {item.citation_id for item in self.citations}
        unresolved = sorted(
            {
                citation_id
                for result in self.results
                for citation_id in result.citation_ids
                if citation_id not in known
            }
        )
        if unresolved:
            raise ValueError(f"unresolved citation_ids: {unresolved}")
        return self


def migrate_v1_bundle(bundle: RunBundle) -> RunBundleV2:
    """Create a generic v2 in-memory view without changing the v1 wire payload."""

    nodes = [
        BundleV2Node(
            sequence=item.sequence,
            node=item.node,
            status=item.status,
            duration_ms=item.duration_ms,
            input_count=item.input_count,
            output_count=item.output_count,
            warning_codes=item.warning_codes,
            source_type=SourceType.SIMULATED_RUN_RESULT,
        )
        for item in bundle.nodes
    ]
    citations = [
        BundleV2Citation(
            citation_id=item.evidence_id,
            public_summary=item.public_summary,
            source_type=SourceType.SIMULATED_RUN_RESULT,
        )
        for item in bundle.evidence
    ]
    results = [
        BundleV2Result(
            result_id=item.hypothesis_id,
            result_type="finding",
            summary=item.reasoning_summary,
            citation_ids=item.supporting_evidence_ids + item.counter_evidence_ids,
            source_type=SourceType.SIMULATED_RUN_RESULT,
        )
        for item in bundle.hypotheses
    ]
    return RunBundleV2(
        project_id="quality-anomaly-agent",
        case_id=bundle.case_id,
        run_id=bundle.run_id,
        trace_id=f"migrated-{bundle.run_id}",
        status=bundle.status,
        identity=BundleV2Identity(
            workflow_version=bundle.identity.workflow_version,
            dataset_version=bundle.identity.dataset_version,
            rules_version="quality-rules-v1",
            prompt_or_policy_version=bundle.identity.prompt_version,
            runtime_version=bundle.identity.config_version,
            model_provider="mock",
            seed=bundle.identity.seed,
        ),
        nodes=nodes,
        citations=citations,
        results=results,
        claims=[],
        estimated_tokens=bundle.estimated_tokens,
        estimated_cost_usd=bundle.estimated_cost_usd,
        warnings=[*bundle.warnings, "migrated_from_v1"],
        generated_at=bundle.generated_at,
    )
