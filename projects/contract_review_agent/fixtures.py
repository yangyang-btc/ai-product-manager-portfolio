from __future__ import annotations

import json
from pathlib import Path

from projects.contract_review_agent.models import ContractFixture

FIXTURE_DIR = Path(__file__).parents[1] / "contract-review-agent" / "fixtures"
CASE_IDS = (
    "procurement_contract_001",
    "sales_contract_001",
    "nda_001",
    "technical_cooperation_001",
)
PUBLIC_FIXTURE_IDS = (
    *CASE_IDS,
    "procurement_safe_001",
    "cross_clause_context_loss",
)


def load_contract_fixture(case_id: str) -> ContractFixture:
    if case_id not in PUBLIC_FIXTURE_IDS:
        raise KeyError(case_id)
    raw = json.loads((FIXTURE_DIR / f"{case_id}.json").read_text(encoding="utf-8"))
    return ContractFixture.model_validate(raw)
