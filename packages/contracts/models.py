"""Public, versioned Pydantic contracts.

These schemas intentionally forbid unversioned extension fields. They are the
boundary between the API, workflow, evaluation UI, and exported run bundles.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RunStatus(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    AWAITING_HUMAN = "awaiting_human"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    REPLAY_READY = "replay_ready"


class ActionName(StrEnum):
    CONFIRM = "confirm"
    REJECT = "reject"
    SUPPLEMENT = "supplement"
    RESUME = "resume"


class Evidence(StrictModel):
    evidence_id: str = Field(pattern=r"^EV-[A-Z]+-[0-9]{3}$")
    source: Literal["QMS", "MES", "ERP", "PLM", "FMEA", "CASE"]
    source_record_id: str
    title: str
    public_summary: str
    supports: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    observed_at: datetime | None = None


class ValidationAction(StrictModel):
    action_id: str
    action: str
    owner_role: str
    target: str
    expected_result: str


class Hypothesis(StrictModel):
    hypothesis_id: str = Field(pattern=r"^H[1-9][0-9]*$")
    direction: str
    confidence: Literal["high", "medium", "low"]
    reasoning_summary: str
    supporting_evidence_ids: list[str]
    counter_evidence_ids: list[str]
    missing_information: list[str]
    validation_actions: list[ValidationAction]
    deterministic_conclusion: bool = False


class EvaluationMetrics(StrictModel):
    metric_definition_version: str = "quality-v1"
    schema_compliance: float = Field(ge=0, le=1)
    evidence_resolvability: float = Field(ge=0, le=1)
    unsupported_conclusion_rate: float = Field(ge=0, le=1)
    counter_evidence_coverage: float = Field(ge=0, le=1)
    human_boundary_accuracy: float = Field(ge=0, le=1)
    source_label: Literal["模拟数据运行结果"] = "模拟数据运行结果"


class TraceNode(StrictModel):
    sequence: int = Field(ge=1)
    node: str
    status: Literal["completed", "failed", "skipped"]
    duration_ms: int = Field(ge=0)
    input_count: int = Field(ge=0)
    output_count: int = Field(ge=0)
    warning_codes: list[str] = Field(default_factory=list)


class TraceView(StrictModel):
    schema_version: Literal[1] = 1
    trace_id: str
    nodes: list[TraceNode]
    total_duration_ms: int = Field(ge=0)
    estimated_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)


class RunResult(StrictModel):
    result_type: Literal["hypothesis_matrix", "clarification", "degraded"]
    summary: str
    facts: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    required_clarifications: list[str] = Field(default_factory=list)
    human_decision: str | None = None


class RunCreateRequest(StrictModel):
    case_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9_]+$")
    scenario: Literal["incoming", "assembly", "debug", "delivery"]
    mode: Literal["offline"] = "offline"
    client_version: str = Field(min_length=1, max_length=40)


class RunCreateResponse(StrictModel):
    schema_version: Literal[1] = 1
    run_id: str
    case_id: str
    trace_id: str
    session_token: str
    stream_token: str
    status: RunStatus
    expires_at: datetime


class RunSnapshot(StrictModel):
    schema_version: Literal[1] = 1
    run_id: str
    case_id: str
    status: RunStatus
    current_node: str
    result_summary: RunResult | None
    allowed_actions: list[ActionName]
    updated_at: datetime
    expires_at: datetime


class ActionRequest(StrictModel):
    action: ActionName
    payload: dict[str, str] = Field(default_factory=dict)
    client_action_id: str = Field(min_length=1, max_length=80)


class ActionResponse(StrictModel):
    schema_version: Literal[1] = 1
    run_id: str
    status: RunStatus
    accepted_action: ActionName
    next_node: str


class BundleIdentity(StrictModel):
    workflow_version: str
    dataset_version: str
    prompt_version: str
    config_version: str
    model_provider: Literal["mock", "openai-compatible"]
    seed: int


class RunBundle(StrictModel):
    schema_version: Literal[1] = 1
    run_id: str
    case_id: str
    scenario: str
    status: RunStatus
    identity: BundleIdentity
    nodes: list[TraceNode]
    evidence: list[Evidence]
    hypotheses: list[Hypothesis]
    metrics: EvaluationMetrics
    estimated_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)
    warnings: list[str]
    generated_at: datetime
