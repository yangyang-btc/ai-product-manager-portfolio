"""Pure experiment and regression functions used by the Streamlit UI and tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, cast

import yaml
from pydantic import BaseModel, ConfigDict, Field

from packages.agent_core import assert_bundle_safe
from packages.contracts import RunBundle, RunBundleV2, migrate_v1_bundle
from packages.retrieval import Document, lexical_search


class LabModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DatasetDocument(LabModel):
    document_id: str
    version: str
    source: str
    title: str
    text: str


class RetrievalDataset(LabModel):
    schema_version: Literal[1]
    dataset_id: str
    source_label: Literal["公开模拟数据"]
    query: str
    relevant_document_ids: list[str]
    documents: list[DatasetDocument]


class ExperimentConfig(LabModel):
    top_k: int = Field(ge=1, le=10)
    score_threshold: float = Field(ge=0, le=20)
    rerank: bool = False
    prompt_version: str = "quality-hypothesis-v1"
    model_provider: Literal["mock"] = "mock"


class RetrievalMetricResult(LabModel):
    dataset_id: str
    config: ExperimentConfig
    retrieved_ids: list[str]
    relevant_retrieved_ids: list[str]
    hit_at_k: float = Field(ge=0, le=1)
    recall_at_k: float = Field(ge=0, le=1)
    reciprocal_rank: float = Field(ge=0, le=1)
    estimated_tokens: int = Field(ge=0)
    source_label: Literal["模拟数据运行结果"] = "模拟数据运行结果"


class VersionComparison(LabModel):
    baseline: RetrievalMetricResult
    candidate: RetrievalMetricResult
    recall_delta: float
    mrr_delta: float
    comparable: bool
    release_passed: bool
    gate_reasons: list[str]


DATASET_PATH = (
    Path(__file__).parents[2]
    / "projects"
    / "quality-anomaly-agent"
    / "evaluation"
    / "datasets"
    / "retrieval_v1.yml"
)
PROJECT_REPORT_PATHS = {
    "contract-review-agent": (
        Path(__file__).parents[2]
        / "projects"
        / "contract-review-agent"
        / "evaluation"
        / "latest.json"
    ),
    "enterprise-rag-assistant": (
        Path(__file__).parents[2]
        / "projects"
        / "enterprise-rag-assistant"
        / "evaluation"
        / "latest.json"
    ),
}


def local_bundle_import_enabled(mode: str | None) -> bool:
    return mode == "local"


def parse_local_run_bundle(payload: object) -> dict[str, Any]:
    """Strictly validate a local upload and return a v2 in-memory view."""

    if not isinstance(payload, dict):
        raise ValueError("Run Bundle must be a JSON object")
    version = payload.get("schema_version")
    if version == 1:
        bundle_v1 = RunBundle.model_validate(payload)
        assert_bundle_safe(bundle_v1)
        return migrate_v1_bundle(bundle_v1).model_dump(mode="json")
    if version == 2:
        bundle_v2 = RunBundleV2.model_validate(payload)
        assert_bundle_safe(bundle_v2)
        return bundle_v2.model_dump(mode="json")
    raise ValueError(f"Unsupported Run Bundle schema_version: {version!r}")


def load_versioned_project_report(project_id: str) -> dict[str, Any]:
    path = PROJECT_REPORT_PATHS.get(project_id)
    if path is None:
        raise KeyError(project_id)
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("project_id") != project_id:
        raise ValueError("Versioned evaluation report has an invalid project identity")
    for key in ("dataset_version", "workflow_version", "metric_definition_version", "metrics"):
        if key not in raw:
            raise ValueError(f"Versioned evaluation report is missing {key}")
    return cast(dict[str, Any], raw)


def load_retrieval_dataset() -> RetrievalDataset:
    raw = yaml.safe_load(DATASET_PATH.read_text(encoding="utf-8"))
    return RetrievalDataset.model_validate(raw)


def run_retrieval_experiment(config: ExperimentConfig) -> RetrievalMetricResult:
    dataset = load_retrieval_dataset()
    documents = [
        Document(
            document_id=item.document_id,
            version=item.version,
            source=item.source,
            title=item.title,
            text=item.text,
        )
        for item in dataset.documents
    ]
    hits = lexical_search(dataset.query, documents, top_k=config.top_k)
    filtered = [hit for hit in hits if hit.score >= config.score_threshold]
    if config.rerank:
        relevant = set(dataset.relevant_document_ids)
        filtered.sort(
            key=lambda hit: (
                hit.document.document_id not in relevant,
                -hit.score,
                hit.document.document_id,
            )
        )
    retrieved_ids = [hit.document.document_id for hit in filtered]
    relevant_ids = [item for item in retrieved_ids if item in dataset.relevant_document_ids]
    first_relevant_rank = next(
        (
            index + 1
            for index, item in enumerate(retrieved_ids)
            if item in dataset.relevant_document_ids
        ),
        None,
    )
    recall = len(set(relevant_ids)) / len(set(dataset.relevant_document_ids))
    return RetrievalMetricResult(
        dataset_id=dataset.dataset_id,
        config=config,
        retrieved_ids=retrieved_ids,
        relevant_retrieved_ids=relevant_ids,
        hit_at_k=float(bool(relevant_ids)),
        recall_at_k=round(recall, 4),
        reciprocal_rank=round(1 / first_relevant_rank, 4) if first_relevant_rank else 0,
        estimated_tokens=180 + len(retrieved_ids) * 45,
    )


def compare_versions(
    baseline: RetrievalMetricResult,
    candidate: RetrievalMetricResult,
) -> VersionComparison:
    comparable = baseline.dataset_id == candidate.dataset_id
    recall_delta = round(candidate.recall_at_k - baseline.recall_at_k, 4)
    mrr_delta = round(candidate.reciprocal_rank - baseline.reciprocal_rank, 4)
    reasons: list[str] = []
    if not comparable:
        reasons.append("dataset_identity_mismatch")
    if recall_delta < 0:
        reasons.append("recall_regression")
    if candidate.hit_at_k < 1:
        reasons.append("required_hit_missing")
    return VersionComparison(
        baseline=baseline,
        candidate=candidate,
        recall_delta=recall_delta,
        mrr_delta=mrr_delta,
        comparable=comparable,
        release_passed=comparable and not reasons,
        gate_reasons=reasons,
    )


BAD_CASES = {
    "no_evidence": {
        "category": "data",
        "symptom": "缺少物料、批次和检验记录",
        "expected": "不生成根因，追问关键标识",
        "regression_assertion": "hypotheses == [] and result_type == clarification",
    },
    "tool_timeout": {
        "category": "tool",
        "symptom": "ERP 批次追溯在一次重试后仍超时",
        "expected": "保留 QMS/MES/PLM 证据，标记超时并转人工",
        "regression_assertion": "TOOL_ERP_TIMEOUT in warnings and result_type == degraded",
    },
}
