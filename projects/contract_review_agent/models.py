from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from packages.contracts.models import TraceNode


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Clause(ContractModel):
    clause_id: str
    heading: str
    page: int = Field(ge=1)
    text: str


class ContractData(ContractModel):
    contract_id: str
    contract_type: Literal["procurement", "sales", "nda", "technical_cooperation"]
    version: str
    party_aliases: list[str]
    business_context: dict[str, Any]
    clauses: list[Clause]


class ReviewRule(ContractModel):
    rule_id: str
    version: str
    severity: Literal["low", "medium", "high", "critical"]
    requirement: str


class ExpectedFinding(ContractModel):
    finding_id: str
    severity: Literal["low", "medium", "high", "critical"]
    source: str
    clause_ids: list[str]
    rule_id: str | None = None
    rationale: str
    human_required: bool


class ExpectedData(ContractModel):
    findings: list[ExpectedFinding]
    non_findings: list[dict[str, str]] = Field(default_factory=list)
    forbidden_behavior: list[str]


class ContractFixture(ContractModel):
    schema_version: Literal[1]
    project_id: Literal["contract-review-agent"]
    scenario_id: str
    synthetic: Literal[True]
    source_label: Literal["公开模拟数据"]
    contract: ContractData
    rules: list[ReviewRule]
    expected: ExpectedData


class RiskFinding(ContractModel):
    finding_id: str
    severity: Literal["low", "medium", "high", "critical"]
    source: Literal["rule", "rag", "llm", "rule_and_cross_clause"]
    clause_ids: list[str]
    original_excerpt: str
    rule_id: str | None = None
    rule_version: str | None = None
    policy_document_id: str | None = None
    rationale: str
    suggestion: str
    human_required: bool
    human_status: Literal["pending_legal_review"] = "pending_legal_review"


class SemanticFindingEnvelope(ContractModel):
    findings: list[RiskFinding]


class ContractMetrics(ContractModel):
    metric_definition_version: Literal["contract-v1"] = "contract-v1"
    case_count: int = Field(ge=1)
    critical_risk_recall: float = Field(ge=0, le=1)
    general_risk_recall: float = Field(ge=0, le=1)
    false_positive_rate: float = Field(ge=0, le=1)
    unsupported_finding_rate: float = Field(ge=0, le=1)
    citation_accuracy: float = Field(ge=0, le=1)
    human_interception_rate: float = Field(ge=0, le=1)
    source_label: Literal["模拟数据运行结果"] = "模拟数据运行结果"


class ContractRunReport(ContractModel):
    schema_version: Literal[1] = 1
    project_id: Literal["contract-review-agent"] = "contract-review-agent"
    case_id: str
    contract_id: str
    contract_type: str
    status: Literal["awaiting_human"] = "awaiting_human"
    model_provider: str
    findings: list[RiskFinding]
    covered_clause_ids: list[str]
    unreviewed_areas: list[str]
    trace: list[TraceNode]
    estimated_tokens: int = Field(ge=0)
    warnings: list[str]
    source_label: Literal["模拟数据运行结果"] = "模拟数据运行结果"


class ContractEvaluationReport(ContractModel):
    schema_version: Literal[1] = 1
    project_id: Literal["contract-review-agent"] = "contract-review-agent"
    dataset_version: Literal["contract-fixtures-v1"] = "contract-fixtures-v1"
    workflow_version: Literal["contract-workflow-v1"] = "contract-workflow-v1"
    metrics: ContractMetrics
    cases: list[ContractRunReport]
    release_passed: bool
    gate_reasons: list[str]
