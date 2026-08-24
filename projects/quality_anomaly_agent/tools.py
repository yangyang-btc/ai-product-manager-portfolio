"""QMS/MES/ERP/PLM offline adapters using realistic project fields."""

from __future__ import annotations

from dataclasses import dataclass, field

from packages.contracts.models import Evidence
from projects.quality_anomaly_agent.fixtures import QualityFixture


@dataclass(frozen=True)
class ToolBatch:
    evidence: list[Evidence]
    warnings: list[str] = field(default_factory=list)
    attempts: dict[str, int] = field(default_factory=dict)


def _inspection_summary(item: str, value: float | str, unit: str | None, result: str) -> str:
    unit_text = f" {unit}" if unit else ""
    return f"检验项 {item} 的模拟实测值为 {value}{unit_text}，判定 {result}。"


def fetch_business_evidence(fixture: QualityFixture) -> ToolBatch:
    evidence: list[Evidence] = []
    warnings: list[str] = []
    attempts = {"QMS": 1, "MES": 1, "ERP": 1, "PLM": 1}

    anomaly = fixture.qms.anomaly
    evidence.append(
        Evidence(
            evidence_id="EV-QMS-001",
            source="QMS",
            source_record_id=anomaly.anomaly_id,
            title="质量异常单",
            public_summary=f"{anomaly.severity} 级异常：{anomaly.symptom}",
            observed_at=anomaly.discovered_at,
        )
    )
    for index, record in enumerate(fixture.qms.inspection_records, start=2):
        evidence.append(
            Evidence(
                evidence_id=f"EV-QMS-{index:03d}",
                source="QMS",
                source_record_id=record.record_id,
                title="检验记录",
                public_summary=_inspection_summary(
                    record.item, record.value, record.unit, record.result
                ),
                observed_at=record.measured_at,
            )
        )

    failure = fixture.failure_injection
    erp_timed_out = failure is not None and failure.system == "ERP"
    if erp_timed_out:
        attempts["ERP"] = 2
        warnings.append("TOOL_ERP_TIMEOUT")
    elif fixture.erp.material_lot is not None:
        lot = fixture.erp.material_lot
        prior_results = ", ".join(f"{item.lot_id}:{item.result}" for item in fixture.erp.prior_lots)
        evidence.append(
            Evidence(
                evidence_id="EV-ERP-001",
                source="ERP",
                source_record_id=lot.lot_id,
                title="来料批次与供应商履历",
                public_summary=(
                    f"模拟批次 {lot.lot_id} 来自 {lot.supplier_alias}；"
                    f"历史批次结果：{prior_results or '无'}。"
                ),
                observed_at=lot.received_at,
            )
        )

    specification = fixture.plm.specification
    if specification is not None:
        limit = specification.helium_leak_rate_max or specification.vacuum_build_time_max
        evidence.append(
            Evidence(
                evidence_id="EV-PLM-001",
                source="PLM",
                source_record_id=specification.document_id,
                title="生效技术规范",
                public_summary=(
                    f"规范 {specification.version} 的模拟上限为 {limit} {specification.unit}。"
                ),
                observed_at=specification.effective_at,
            )
        )

    usage = fixture.mes.usage
    evidence.append(
        Evidence(
            evidence_id="EV-MES-001",
            source="MES",
            source_record_id=usage.used_in_work_orders[0] if usage.used_in_work_orders else "NO-WO",
            title="制造使用与隔离状态",
            public_summary=(
                f"关联工单 {usage.used_in_work_orders or '无'}；"
                f"隔离状态 {usage.quarantine_status}。"
            ),
        )
    )
    return ToolBatch(evidence=evidence, warnings=warnings, attempts=attempts)
