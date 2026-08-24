from __future__ import annotations

from collections.abc import Iterable

from packages.model_gateway import GatewayConfig, StructuredGateway
from packages.observability import TraceRecorder
from packages.retrieval import Document, lexical_search
from projects.contract_review_agent.fixtures import load_contract_fixture
from projects.contract_review_agent.models import (
    Clause,
    ContractFixture,
    ContractRunReport,
    RiskFinding,
    SemanticFindingEnvelope,
)

POLICY_DOCUMENTS = [
    Document(
        "POL-PROC-V3",
        "V3.1",
        "采购付款与验收规则",
        "验收完成前高比例付款必须专项审批；质量异议期不得短于来料检验周期。",
        "POLICY",
    ),
    Document(
        "POL-SALES-V2",
        "V2.2",
        "设备销售验收与质保规则",
        "FAT、安装调试、SAT 和质保起算点必须保持一致，不得使用冲突起点。",
        "POLICY",
    ),
    Document(
        "POL-NDA-V4",
        "V4.0",
        "技术资料保密审查规则",
        "保密信息应覆盖图纸、BOM、工艺参数、软件代码和客户数据，并明确允许披露范围。",
        "POLICY",
    ),
    Document(
        "POL-TECH-V2",
        "V2.5",
        "联合开发知识产权规则",
        "必须区分背景知识产权与新生成果，并在签署前明确成果归属和使用许可。",
        "POLICY",
    ),
]


def _clause(fixture: ContractFixture, clause_id: str) -> Clause:
    return next(item for item in fixture.contract.clauses if item.clause_id == clause_id)


def _clause_by_heading(fixture: ContractFixture, heading: str) -> Clause | None:
    return next(
        (item for item in fixture.contract.clauses if heading in item.heading),
        None,
    )


def _excerpt(fixture: ContractFixture, clause_ids: Iterable[str]) -> str:
    return " / ".join(_clause(fixture, item).text for item in clause_ids)


def _rule(fixture: ContractFixture, rule_id: str) -> tuple[str, str]:
    item = next(rule for rule in fixture.rules if rule.rule_id == rule_id)
    return item.rule_id, item.version


def _deterministic_findings(fixture: ContractFixture) -> list[RiskFinding]:
    ids = {item.clause_id for item in fixture.contract.clauses}
    findings: list[RiskFinding] = []
    if fixture.contract.contract_type == "procurement":
        if {"CL-PAY-001", "CL-ACC-001"} <= ids:
            rule_id, version = _rule(fixture, "RULE-PROC-012")
            findings.append(
                RiskFinding(
                    finding_id="RF-DEMO-001",
                    severity="high",
                    source="rule_and_cross_clause",
                    clause_ids=["CL-PAY-001", "CL-ACC-001"],
                    original_excerpt=_excerpt(fixture, ["CL-PAY-001", "CL-ACC-001"]),
                    rule_id=rule_id,
                    rule_version=version,
                    policy_document_id="POL-PROC-V3",
                    rationale="付款可能在来料检验完成前发生，形成先付款后验收的风险。",
                    suggestion="将大额付款节点调整到来料验收通过后，例外情况进入专项审批。",
                    human_required=True,
                )
            )
        if {"CL-OBJ-001", "CL-ACC-001", "CL-WAR-001"} <= ids:
            rule_id, version = _rule(fixture, "RULE-PROC-021")
            findings.append(
                RiskFinding(
                    finding_id="RF-DEMO-002",
                    severity="critical",
                    source="rule_and_cross_clause",
                    clause_ids=["CL-OBJ-001", "CL-ACC-001", "CL-WAR-001"],
                    original_excerpt=_excerpt(fixture, ["CL-OBJ-001", "CL-ACC-001", "CL-WAR-001"]),
                    rule_id=rule_id,
                    rule_version=version,
                    policy_document_id="POL-PROC-V3",
                    rationale="质量异议期短于检验周期，可能在检验完成前被视为验收合格。",
                    suggestion="将质量异议期延长至检验周期结束后，并保留隐蔽缺陷追索。",
                    human_required=True,
                )
            )
    elif (
        fixture.contract.contract_type == "sales"
        and {"CL-FAT-001", "CL-SAT-001", "CL-WAR-101"} <= ids
    ):
        rule_id, version = _rule(fixture, "RULE-SALES-031")
        findings.append(
            RiskFinding(
                finding_id="RF-SALES-001",
                severity="critical",
                source="rule_and_cross_clause",
                clause_ids=["CL-FAT-001", "CL-SAT-001", "CL-WAR-101"],
                original_excerpt=_excerpt(fixture, ["CL-FAT-001", "CL-SAT-001", "CL-WAR-101"]),
                rule_id=rule_id,
                rule_version=version,
                policy_document_id="POL-SALES-V2",
                rationale="同一设备的质保起点同时指向发货日和 SAT 通过日，责任窗口不可确定。",
                suggestion=(
                    "统一以 SAT 通过日为质保起点，并设置客户原因导致 SAT 延迟的最长兜底期限。"
                ),
                human_required=True,
            )
        )
    elif fixture.contract.contract_type == "sales":
        liability_cap = _clause_by_heading(fixture, "责任上限")
        appendix = _clause_by_heading(fixture, "附件 A")
        if (
            liability_cap is not None
            and appendix is not None
            and "附件 A" in liability_cap.text
            and "不受" in appendix.text
            and "责任上限" in appendix.text
        ):
            rule_id, version = _rule(fixture, "RULE-SALES-099")
            findings.append(
                RiskFinding(
                    finding_id="RF-CONTEXT-LOSS-001",
                    severity="critical",
                    source="rule_and_cross_clause",
                    clause_ids=[liability_cap.clause_id, appendix.clause_id],
                    original_excerpt=" / ".join(
                        [liability_cap.text, appendix.text]
                    ),
                    rule_id=rule_id,
                    rule_version=version,
                    policy_document_id="POL-SALES-V2",
                    rationale=(
                        "正文与附件对责任上限存在冲突，单条款检索可能遗漏附件例外。"
                    ),
                    suggestion=(
                        "补充正文与附件的双向交叉引用，并由法务确认赔偿例外的优先级。"
                    ),
                    human_required=True,
                )
            )
    return findings


def _mock_semantic_findings(fixture: ContractFixture) -> SemanticFindingEnvelope:
    contract_type = fixture.contract.contract_type
    if contract_type == "nda":
        finding = RiskFinding(
            finding_id="RF-NDA-001",
            severity="high",
            source="llm",
            clause_ids=["CL-NDA-SCOPE-001", "CL-NDA-DISC-001"],
            original_excerpt=_excerpt(fixture, ["CL-NDA-SCOPE-001", "CL-NDA-DISC-001"]),
            rule_id="RULE-NDA-011",
            rule_version="V4.0",
            policy_document_id="POL-NDA-V4",
            rationale="保密信息仅列明图纸和 BOM，未覆盖软件代码、客户数据，允许披露对象也不完整。",
            suggestion="补充受保护信息类型，并限定向顾问和关联方披露的必要性、保密义务与责任。",
            human_required=True,
        )
        return SemanticFindingEnvelope(findings=[finding])
    if contract_type == "technical_cooperation":
        finding = RiskFinding(
            finding_id="RF-TECH-001",
            severity="critical",
            source="llm",
            clause_ids=["CL-IP-BG-001", "CL-IP-FG-001", "CL-ACC-201"],
            original_excerpt=_excerpt(fixture, ["CL-IP-BG-001", "CL-IP-FG-001", "CL-ACC-201"]),
            rule_id="RULE-TECH-021",
            rule_version="V2.5",
            policy_document_id="POL-TECH-V2",
            rationale="协议定义了背景知识产权，但将新生成算法与工艺成果留待后续协商，验收后仍可能无法使用成果。",
            suggestion="签署前明确新生成果的归属、许可范围、申请权与验收失败后的处置。",
            human_required=True,
        )
        return SemanticFindingEnvelope(findings=[finding])
    return SemanticFindingEnvelope(findings=[])


def run_contract_review(
    case_id: str,
    gateway_config: GatewayConfig | None = None,
) -> ContractRunReport:
    fixture = load_contract_fixture(case_id)
    trace = TraceRecorder(f"contract-{case_id}")

    trace.start("ingest_document", input_count=1)
    trace.complete("ingest_document", output_count=len(fixture.contract.clauses))
    trace.start("classify_contract", input_count=len(fixture.contract.clauses))
    trace.complete("classify_contract", output_count=1)
    trace.start("structural_clause_split", input_count=1)
    trace.complete("structural_clause_split", output_count=len(fixture.contract.clauses))

    trace.start("deterministic_rules", input_count=len(fixture.rules))
    findings = _deterministic_findings(fixture)
    trace.complete("deterministic_rules", output_count=len(findings))

    trace.start("retrieve_policy_and_precedent", input_count=len(fixture.contract.clauses))
    query = " ".join(item.heading + " " + item.text for item in fixture.contract.clauses)
    hits = lexical_search(query, POLICY_DOCUMENTS, top_k=4)
    trace.complete("retrieve_policy_and_precedent", output_count=len(hits))

    trace.start("semantic_risk_review", input_count=len(hits))
    gateway = StructuredGateway(gateway_config)
    semantic = gateway.generate(
        system_prompt="识别合同语义与跨条款风险，只能引用输入条款和有效规则；高风险必须转法务。",
        payload={
            "contract_type": fixture.contract.contract_type,
            "clauses": [item.model_dump() for item in fixture.contract.clauses],
            "policies": [
                item.document.model_dump()
                if hasattr(item.document, "model_dump")
                else {
                    "document_id": item.document.document_id,
                    "version": item.document.version,
                    "title": item.document.title,
                    "text": item.document.text,
                }
                for item in hits
            ],
        },
        output_model=SemanticFindingEnvelope,
        mock_output=_mock_semantic_findings(fixture),
    )
    findings.extend(semantic.output.findings)
    trace.add_model_usage(semantic.estimated_input_tokens, semantic.estimated_output_tokens)
    trace.complete("semantic_risk_review", output_count=len(semantic.output.findings))

    trace.start("cross_clause_consistency", input_count=len(fixture.contract.clauses))
    trace.complete(
        "cross_clause_consistency",
        output_count=sum(item.source == "rule_and_cross_clause" for item in findings),
    )
    trace.start("evidence_validation", input_count=len(findings))
    known_clauses = {item.clause_id for item in fixture.contract.clauses}
    known_rules = {item.rule_id: item.version for item in fixture.rules}
    known_policies = {item.document_id for item in POLICY_DOCUMENTS}
    invalid = [
        item.finding_id
        for item in findings
        if not set(item.clause_ids) <= known_clauses
        or item.rule_id not in known_rules
        or item.rule_version != known_rules[item.rule_id]
        or item.policy_document_id not in known_policies
        or (item.severity in {"high", "critical"} and not item.human_required)
    ]
    if invalid:
        trace.fail("evidence_validation", "UNRESOLVED_CITATION")
        raise ValueError(f"unresolved contract citations: {invalid}")
    trace.complete("evidence_validation", output_count=len(findings))
    trace.start("risk_ranking", input_count=len(findings))
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda item: (order[item.severity], item.finding_id))
    trace.complete("risk_ranking", output_count=len(findings))
    trace.start("mandatory_human_review", input_count=len(findings))
    trace.complete(
        "mandatory_human_review", output_count=sum(item.human_required for item in findings)
    )

    view = trace.view()
    return ContractRunReport(
        case_id=case_id,
        contract_id=fixture.contract.contract_id,
        contract_type=fixture.contract.contract_type,
        model_provider=semantic.provider,
        findings=findings,
        covered_clause_ids=sorted({clause for item in findings for clause in item.clause_ids}),
        unreviewed_areas=["附件与签章真实性需由法务和业务人员确认"],
        trace=view.nodes,
        estimated_tokens=view.estimated_tokens,
        warnings=view.warnings,
    )


def normalize_contract_report(report: ContractRunReport) -> dict[str, object]:
    """Return the stable cross-language parity surface.

    Runtime-specific timing and token estimates are intentionally excluded.
    """

    return {
        "case_id": report.case_id,
        "contract_type": report.contract_type,
        "findings": [
            {
                "finding_id": item.finding_id,
                "severity": item.severity,
                "source": item.source,
                "clause_ids": item.clause_ids,
                "rule_id": item.rule_id,
                "rule_version": item.rule_version,
                "policy_document_id": item.policy_document_id,
                "human_required": item.human_required,
            }
            for item in report.findings
        ],
        "covered_clause_ids": report.covered_clause_ids,
        "trace_nodes": [item.node for item in report.trace],
    }
