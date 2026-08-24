"""Project-specific conversion from FMEA/case records into retrieval documents."""

from __future__ import annotations

from packages.contracts.models import Evidence
from packages.retrieval import Document, lexical_search
from projects.quality_anomaly_agent.fixtures import QualityFixture

_TERM_LABELS = {
    "seal_surface_or_contamination": "密封面缺陷、表面污染与氦质谱检漏异常",
    "measurement_fixture_contamination": "检漏夹具污染与测量系统本底异常",
    "seal_surface_defect": "阀组件密封面微观缺陷与泄漏率异常",
    "site_utility_or_interface_leak": "客户现场公用工程或接口泄漏",
}


def build_documents(fixture: QualityFixture) -> list[Document]:
    documents: list[Document] = []
    for fmea in fixture.knowledge.fmea:
        label = _TERM_LABELS.get(fmea.failure_mode, fmea.failure_mode.replace("_", " "))
        documents.append(
            Document(
                document_id=fmea.document_id,
                version=fmea.version,
                title=f"FMEA：{label}",
                text=f"{label}。建议检查：{'、'.join(fmea.recommended_checks)}。",
                source="FMEA",
            )
        )
    for historical_case in fixture.knowledge.historical_cases:
        label = _TERM_LABELS.get(
            historical_case.confirmed_cause,
            historical_case.confirmed_cause.replace("_", " "),
        )
        documents.append(
            Document(
                document_id=historical_case.case_id,
                version="case-v1",
                title=f"历史案例：{label}",
                text=(
                    f"{label}。确认依据：{historical_case.support}。"
                    f"相似度仅用于召回：{historical_case.similarity}。"
                ),
                source="CASE",
            )
        )
    return documents


def retrieve_knowledge(fixture: QualityFixture, top_k: int = 5) -> list[Evidence]:
    documents = build_documents(fixture)
    query = fixture.qms.anomaly.symptom + " 密封面 污染 检漏夹具 测量系统"
    hits = lexical_search(query, documents, top_k=top_k)
    source_counts = {"FMEA": 0, "CASE": 0}
    evidence: list[Evidence] = []
    for hit in hits:
        source = hit.document.source
        if source not in source_counts:
            continue
        source_counts[source] += 1
        evidence.append(
            Evidence(
                evidence_id=f"EV-{source}-{source_counts[source]:03d}",
                source=source,  # type: ignore[arg-type]
                source_record_id=hit.document.document_id,
                title=hit.document.title,
                public_summary=(
                    f"检索排名 {hit.rank}，词法分数 {hit.score:.3f}；"
                    f"文档版本 {hit.document.version}。"
                ),
            )
        )
    return evidence
