"""Versioned fixture schemas and loader for the quality project."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class FixtureModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Anomaly(FixtureModel):
    anomaly_id: str
    symptom: str
    severity: Literal["low", "medium", "high"]
    discovered_at: datetime


class InspectionRecord(FixtureModel):
    record_id: str
    lot_id: str | None = None
    item: str
    value: float | str
    unit: str | None = None
    limit: float | None = None
    result: Literal["pass", "fail"]
    measured_at: datetime
    instrument_id: str | None = None


class QmsData(FixtureModel):
    anomaly: Anomaly
    inspection_records: list[InspectionRecord]


class MaterialLot(FixtureModel):
    material_id: str
    lot_id: str
    supplier_alias: str
    quantity: int = Field(gt=0)
    received_at: datetime
    supplier_certificate_status: str


class PriorLot(FixtureModel):
    lot_id: str
    supplier_alias: str
    result: Literal["pass", "fail"]


class ErpData(FixtureModel):
    material_lot: MaterialLot | None
    prior_lots: list[PriorLot]


class Specification(FixtureModel):
    document_id: str
    version: str
    effective_at: datetime | None = None
    helium_leak_rate_max: float | None = None
    vacuum_build_time_max: float | None = None
    unit: str


class PlmData(FixtureModel):
    specification: Specification | None


class Usage(FixtureModel):
    used_in_work_orders: list[str]
    quarantine_status: str


class MesData(FixtureModel):
    usage: Usage


class FmeaRecord(FixtureModel):
    document_id: str
    version: str
    failure_mode: str
    recommended_checks: list[str]


class HistoricalCase(FixtureModel):
    case_id: str
    similarity: float = Field(ge=0, le=1)
    confirmed_cause: str
    support: str


class KnowledgeData(FixtureModel):
    fmea: list[FmeaRecord]
    historical_cases: list[HistoricalCase]


class ExpectedData(FixtureModel):
    facts: list[str]
    hypotheses: list[dict[str, Any]]
    required_clarifications: list[str] = Field(default_factory=list)
    forbidden_conclusions: list[str]


class FailureInjection(FixtureModel):
    system: str
    behavior: str


class QualityFixture(FixtureModel):
    schema_version: Literal[1]
    project_id: Literal["quality-anomaly-agent"]
    scenario_id: str
    synthetic: Literal[True]
    source_label: Literal["公开模拟数据"]
    clock: datetime
    failure_injection: FailureInjection | None = None
    qms: QmsData
    erp: ErpData
    plm: PlmData
    mes: MesData
    knowledge: KnowledgeData
    expected: ExpectedData


FIXTURE_DIR = Path(__file__).parents[1] / "quality-anomaly-agent" / "fixtures"


def load_fixture(case_id: str) -> QualityFixture:
    if not case_id.replace("_", "").isalnum():
        raise ValueError("Invalid case_id")
    path = FIXTURE_DIR / f"{case_id}.yml"
    if not path.is_file():
        raise KeyError(case_id)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return QualityFixture.model_validate(raw)
