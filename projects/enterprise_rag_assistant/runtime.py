from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from packages.model_gateway import GatewayConfig, StructuredGateway
from packages.observability import TraceRecorder
from packages.retrieval import Document, lexical_search
from projects.enterprise_rag_assistant.cases import QUERY_CASES
from projects.enterprise_rag_assistant.models import (
    AnswerDraft,
    Citation,
    EnterpriseDataFixture,
    EnterpriseRunReport,
    QueryCase,
)
from projects.enterprise_rag_assistant.taxonomy import classify_intent

FIXTURE_PATH = (
    Path(__file__).parents[1]
    / "enterprise-rag-assistant"
    / "fixtures"
    / "business_data_v1.json"
)


def load_enterprise_data_fixture() -> EnterpriseDataFixture:
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return EnterpriseDataFixture.model_validate(raw)


def _fixture() -> dict[str, Any]:
    return load_enterprise_data_fixture().model_dump(mode="json")


def _normalize(query: str, data: dict[str, Any]) -> str:
    normalized = query.strip().replace("，", "、").replace("。", "")
    for entry in data["knowledge_data"]["terminology"]:
        for alias in entry["aliases"]:
            normalized = normalized.replace(alias, f"{alias}（{entry['canonical']}）")
    return normalized


def _protected_constraints(query: str) -> list[str]:
    return [item for item in ("华东", "两周内", "ISO", "交期", "当前") if item in query]


def _route(case: QueryCase, intent_level_2: str) -> str:
    if case.permission_scope == "public" and any(
        item in case.query for item in ("受限", "合同价格", "报价明细")
    ):
        return "permission_stop"
    if intent_level_2 == "supplier_comparison" and not any(
        item in case.query for item in ("产品", "工艺", "区域", "资质", "数量", "交期")
    ):
        return "clarify"
    if "未收录" in case.query or "无可靠证据" in case.query:
        return "refuse"
    if intent_level_2 == "process_parameter" and "有效" in case.query:
        return "version_check"
    if intent_level_2 in {"inquiry_status", "quotation_status", "order_status", "logistics_status"}:
        return "tool"
    if intent_level_2 == "knowledge_and_realtime":
        return "rag_and_tool"
    return "rag"


def _knowledge_documents(data: dict[str, Any]) -> list[Document]:
    knowledge = data["knowledge_data"]
    relationships = knowledge["relationships"]
    documents = [
        Document(
            document_id=item["evidence_id"],
            version="V1",
            title="供应关系证据",
            text=(
                f"{item['supplier_id']} 提供 {item['capability']}，"
                f"适用 {item['item_category']}，有效期 {item['valid_from']} "
                f"至 {item['valid_to']}"
            ),
            source="CONTRACT",
        )
        for item in relationships
    ]
    documents.extend(
        Document(
            item["document_id"],
            item["version"],
            item["title"],
            item["text"],
            item["source"],
        )
        for item in knowledge["documents"]
    )
    return documents


def _base_answer(
    case_id: str, route: str, data: dict[str, Any]
) -> tuple[str, AnswerDraft, list[str]]:
    if route == "permission_stop":
        return (
            "permission_denied",
            AnswerDraft(
                facts=[],
                limitations=["当前角色无权查看受限合同价格或报价明细，且不披露数据是否存在。"],
            ),
            ["PERMISSION_BLOCKED"],
        )
    if route == "clarify":
        return (
            "clarification",
            AnswerDraft(
                facts=["请补充产品或工艺、区域、资质、数量和交期约束。"],
                limitations=["关键约束不足，系统未执行供应商推荐。"],
            ),
            ["CLARIFICATION_REQUIRED"],
        )
    if route == "refuse":
        return (
            "refusal",
            AnswerDraft(facts=[], limitations=["知识库中没有该企业私有产能的可靠证据，无法回答。"]),
            ["NO_EVIDENCE_REFUSAL"],
        )
    if route == "version_check":
        return (
            "clarification",
            AnswerDraft(
                facts=["检索到两个版本的工艺温度窗口；V1 已失效，V2 为当前版本。"],
                citations=[
                    Citation(
                        citation_id="CIT-DEMO-PROCESS-CURRENT",
                        source_type="knowledge",
                        title="当前工艺温度窗口",
                        version_or_freshness="V2",
                    )
                ],
                limitations=["仍需工艺工程师确认 V2 是否适用于当前产品。"],
            ),
            ["SOURCE_VERSION_CONFLICT"],
        )
    if case_id == "compound_query_001":
        knowledge = data["knowledge_data"]
        eligible = [
            item["supplier_id"]
            for item in knowledge["relationships"]
            if item["capability"] == "precision_cleaning"
        ]
        submitted = [
            item for item in data["realtime_data"]["quotations"] if item["status"] == "submitted"
        ]
        return (
            "table",
            AnswerDraft(
                facts=[
                    f"具备精密清洗有效供应证据的供应商有 {len(eligible)} 家。",
                    f"当前询价已有 {len(submitted)} 家提交报价。",
                ],
                table=[
                    {"supplier_id": supplier, "capability": "precision_cleaning"}
                    for supplier in eligible
                ],
                citations=[
                    *[
                        Citation(
                            citation_id=item["evidence_id"],
                            source_type="knowledge",
                            title="供应关系证据",
                            version_or_freshness="V1",
                        )
                        for item in knowledge["relationships"]
                        if item["supplier_id"] in eligible
                    ],
                    Citation(
                        citation_id="TOOL-QUOTATION-DEMO-001",
                        source_type="tool",
                        title="报价 Tool",
                        version_or_freshness=data["realtime_data"]["inquiry"]["updated_at"],
                    ),
                ],
                limitations=["供应能力来自知识证据；当前报价数来自实时 Tool，两者不可互相替代。"],
            ),
            [],
        )
    if route == "tool":
        order = next(
            item
            for item in data["realtime_data"]["orders"]
            if item["order_id"] == "ORD-DEMO-001"
        )
        return (
            "answer",
            AnswerDraft(
                facts=[f"订单 {order['order_id']} 当前状态为{order['status']}。"],
                citations=[
                    Citation(
                        citation_id="TOOL-ORDER-DEMO-001",
                        source_type="tool",
                        title="订单 Tool",
                        version_or_freshness=order["updated_at"],
                    )
                ],
                limitations=["实时状态只由授权 Tool 返回，不使用知识库猜测。"],
            ),
            [],
        )
    documents = _knowledge_documents(data)
    query = QUERY_CASES[case_id].query
    hits = lexical_search(query, documents, top_k=3)
    facts = [hit.document.text for hit in hits[:2]]
    citations = [
        Citation(
            citation_id=hit.document.document_id,
            source_type="knowledge",
            title=hit.document.title,
            version_or_freshness=hit.document.version,
        )
        for hit in hits[:2]
    ]
    return (
        "answer",
        AnswerDraft(
            facts=facts,
            citations=citations,
            limitations=["答案仅基于当前有效且有权限的公开模拟知识。"],
        ),
        [],
    )


def run_enterprise_query(
    case_id: str, gateway_config: GatewayConfig | None = None
) -> EnterpriseRunReport:
    if case_id not in QUERY_CASES:
        raise KeyError(case_id)
    case = QUERY_CASES[case_id]
    data = _fixture()
    trace = TraceRecorder(f"enterprise-{case_id}")
    trace.start("normalize_query", input_count=1)
    normalized = _normalize(case.query, data)
    trace.complete("normalize_query", output_count=1)
    trace.start("terminology_rewrite", input_count=1)
    protected = _protected_constraints(case.query)
    rewritten = normalized
    trace.complete("terminology_rewrite", output_count=1)
    trace.start("classify_intent", input_count=1)
    intent = classify_intent(case.query)
    trace.complete("classify_intent", output_count=1)
    route = _route(case, intent.level_2)
    trace.start("route_knowledge_or_realtime_data", input_count=1)
    trace.complete("route_knowledge_or_realtime_data", output_count=1)
    trace.start("retrieve_and_rerank_or_call_business_tool", input_count=1)
    result_type, mock_answer, warnings = _base_answer(case_id, route, data)
    trace.complete(
        "retrieve_and_rerank_or_call_business_tool",
        output_count=len(mock_answer.citations),
        warning_codes=warnings,
    )
    trace.start("generate_structured_answer", input_count=len(mock_answer.citations))
    # Permission, refusal, clarification and Tool facts are deterministic product
    # boundaries. A real model may organize knowledge answers, but it may not
    # override access control or mutate transactional facts.
    model_safe_routes = {
        "permission_stop",
        "clarify",
        "refuse",
        "version_check",
        "tool",
        "rag_and_tool",
    }
    effective_config = (
        GatewayConfig(provider="mock") if route in model_safe_routes else gateway_config
    )
    gateway = StructuredGateway(effective_config)
    generation = gateway.generate(
        system_prompt="基于已授权证据生成企业问答；不得修改 Tool 事实，不得补写无引用事实。",
        payload={"query": rewritten, "route": route, "draft": mock_answer.model_dump(mode="json")},
        output_model=AnswerDraft,
        mock_output=mock_answer,
    )
    trace.add_model_usage(generation.estimated_input_tokens, generation.estimated_output_tokens)
    trace.complete("generate_structured_answer", output_count=len(generation.output.facts))
    trace.start("citation_and_permission_check", input_count=len(generation.output.citations))
    allowed_citations = {item.document_id for item in _knowledge_documents(data)} | {
        "TOOL-QUOTATION-DEMO-001",
        "TOOL-ORDER-DEMO-001",
    }
    unresolved = [
        item.citation_id
        for item in generation.output.citations
        if item.citation_id not in allowed_citations
    ]
    if unresolved:
        trace.fail("citation_and_permission_check", "UNRESOLVED_CITATION")
        raise ValueError(f"unresolved citations: {unresolved}")
    trace.complete("citation_and_permission_check", output_count=len(generation.output.citations))
    trace.start("answer_or_refuse", input_count=1)
    trace.complete("answer_or_refuse", output_count=1)
    view = trace.view()
    return EnterpriseRunReport(
        case_id=case_id,
        original_query=case.query,
        normalized_query=normalized,
        rewritten_query=rewritten,
        protected_constraints=protected,
        intent=intent,
        route=route,
        result_type=result_type,  # type: ignore[arg-type]
        answer=generation.output,
        model_provider=generation.provider,
        trace=view.nodes,
        estimated_tokens=view.estimated_tokens,
        warnings=view.warnings,
    )


def normalize_enterprise_report(report: EnterpriseRunReport) -> dict[str, object]:
    """Return the stable cross-language parity surface."""

    return {
        "case_id": report.case_id,
        "normalized_query": report.normalized_query,
        "protected_constraints": report.protected_constraints,
        "intent": report.intent.model_dump(mode="json"),
        "route": report.route,
        "result_type": report.result_type,
        "facts": report.answer.facts,
        "citations": [
            {
                "citation_id": item.citation_id,
                "source_type": item.source_type,
            }
            for item in report.answer.citations
        ],
        "warnings": report.warnings,
        "trace_nodes": [item.node for item in report.trace],
    }
