from __future__ import annotations

import json
from pathlib import Path

from projects.enterprise_rag_assistant.models import QueryCaseCollection

FIXTURE_DIR = Path(__file__).parents[1] / "enterprise-rag-assistant" / "fixtures"
QUERY_CASES_PATH = FIXTURE_DIR / "query_cases_v1.json"


def load_query_case_collection() -> QueryCaseCollection:
    raw = json.loads(QUERY_CASES_PATH.read_text(encoding="utf-8"))
    return QueryCaseCollection.model_validate(raw)


QUERY_CASE_COLLECTION = load_query_case_collection()
QUERY_CASES = {item.case_id: item for item in QUERY_CASE_COLLECTION.cases}
