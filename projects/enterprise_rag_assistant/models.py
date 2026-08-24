from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from packages.contracts.models import TraceNode


class EnterpriseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class QueryCase(EnterpriseModel):
    case_id: str
    query: str
    user_role: str
    permission_scope: Literal["public", "internal", "restricted"]
    expected_l1: str
    expected_l2: str
    expected_route: Literal[
        "rag", "tool", "rag_and_tool", "clarify", "refuse", "permission_stop", "version_check"
    ]


class QueryCaseCollection(EnterpriseModel):
    schema_version: Literal[1]
    project_id: Literal["enterprise-rag-assistant"]
    dataset_version: Literal["enterprise-query-cases-v1"]
    synthetic: Literal[True]
    source_label: Literal["公开模拟数据"]
    cases: list[QueryCase]


class IntentDefinitionAsset(EnterpriseModel):
    level_1: str
    level_2: str
    keywords: list[str]
    example: str


class IntentTaxonomyFixture(EnterpriseModel):
    schema_version: Literal[1]
    project_id: Literal["enterprise-rag-assistant"]
    taxonomy_version: Literal["enterprise-intent-taxonomy-v1"]
    synthetic: Literal[True]
    source_label: Literal["公开模拟数据"]
    definitions: list[IntentDefinitionAsset]


class TerminologyEntry(EnterpriseModel):
    canonical: str
    aliases: list[str]
    confused_with: list[str] = Field(default_factory=list)


class SupplierRecord(EnterpriseModel):
    supplier_id: str
    region: str
    capabilities: list[str]
    certifications: list[str]


class SupplyRelationship(EnterpriseModel):
    relationship_id: str
    supplier_id: str
    item_category: str
    capability: str
    valid_from: str
    valid_to: str
    evidence_id: str


class KnowledgeDocument(EnterpriseModel):
    document_id: str
    version: str
    source: str
    title: str
    text: str


class KnowledgeData(EnterpriseModel):
    source_type: Literal["public_reconstruction"]
    terminology: list[TerminologyEntry]
    suppliers: list[SupplierRecord]
    relationships: list[SupplyRelationship]
    documents: list[KnowledgeDocument]


class InquiryRecord(EnterpriseModel):
    inquiry_id: str
    item_category: str
    status: str
    updated_at: str


class QuotationRecord(EnterpriseModel):
    quotation_id: str
    inquiry_id: str
    supplier_id: str
    status: str
    updated_at: str


class OrderRecord(EnterpriseModel):
    order_id: str
    status: str
    updated_at: str


class RealtimeData(EnterpriseModel):
    source_type: Literal["simulated_extension"]
    inquiry: InquiryRecord
    quotations: list[QuotationRecord]
    orders: list[OrderRecord]


class EnterpriseDataFixture(EnterpriseModel):
    schema_version: Literal[1]
    project_id: Literal["enterprise-rag-assistant"]
    dataset_version: Literal["enterprise-business-data-v1"]
    synthetic: Literal[True]
    source_label: Literal["公开模拟数据"]
    clock: str
    knowledge_data: KnowledgeData
    realtime_data: RealtimeData


class IntentMatch(EnterpriseModel):
    level_1: str
    level_2: str
    confidence: float = Field(ge=0, le=1)
    alternatives: list[str] = Field(default_factory=list)


class Citation(EnterpriseModel):
    citation_id: str
    source_type: Literal["knowledge", "tool"]
    title: str
    version_or_freshness: str


class AnswerDraft(EnterpriseModel):
    facts: list[str]
    table: list[dict[str, str | int]] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class EnterpriseRunReport(EnterpriseModel):
    schema_version: Literal[1] = 1
    project_id: Literal["enterprise-rag-assistant"] = "enterprise-rag-assistant"
    case_id: str
    original_query: str
    normalized_query: str
    rewritten_query: str
    protected_constraints: list[str]
    intent: IntentMatch
    route: str
    result_type: Literal["answer", "table", "clarification", "refusal", "permission_denied"]
    answer: AnswerDraft
    model_provider: str
    trace: list[TraceNode]
    estimated_tokens: int = Field(ge=0)
    warnings: list[str]
    source_label: Literal["模拟数据运行结果"] = "模拟数据运行结果"


class EnterpriseMetrics(EnterpriseModel):
    metric_definition_version: Literal["enterprise-rag-v1"] = "enterprise-rag-v1"
    case_count: int = Field(ge=1)
    intent_accuracy: float = Field(ge=0, le=1)
    route_accuracy: float = Field(ge=0, le=1)
    rewrite_fidelity: float = Field(ge=0, le=1)
    citation_accuracy: float = Field(ge=0, le=1)
    faithfulness: float = Field(ge=0, le=1)
    refusal_accuracy: float = Field(ge=0, le=1)
    clarification_accuracy: float = Field(ge=0, le=1)
    permission_interception: float = Field(ge=0, le=1)
    source_label: Literal["模拟数据运行结果"] = "模拟数据运行结果"


class EnterpriseEvaluationReport(EnterpriseModel):
    schema_version: Literal[1] = 1
    project_id: Literal["enterprise-rag-assistant"] = "enterprise-rag-assistant"
    dataset_version: Literal["enterprise-query-cases-v1"] = "enterprise-query-cases-v1"
    workflow_version: Literal["enterprise-rag-workflow-v1"] = "enterprise-rag-workflow-v1"
    metrics: EnterpriseMetrics
    cases: list[EnterpriseRunReport]
    release_passed: bool
    gate_reasons: list[str]
