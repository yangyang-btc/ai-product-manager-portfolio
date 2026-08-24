from __future__ import annotations

import json
from pathlib import Path

from projects.enterprise_rag_assistant.models import IntentMatch, IntentTaxonomyFixture

TAXONOMY_PATH = (
    Path(__file__).parents[1]
    / "enterprise-rag-assistant"
    / "fixtures"
    / "intent_taxonomy_v1.json"
)


def load_intent_taxonomy() -> IntentTaxonomyFixture:
    raw = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    return IntentTaxonomyFixture.model_validate(raw)


INTENT_TAXONOMY = load_intent_taxonomy()
INTENT_DEFINITIONS = tuple(INTENT_TAXONOMY.definitions)


def classify_intent(query: str) -> IntentMatch:
    scores = []
    for index, definition in enumerate(INTENT_DEFINITIONS):
        score = sum(3 if keyword in query else 0 for keyword in definition.keywords)
        if definition.level_2 == "knowledge_and_realtime" and score:
            score += 10
        if definition.example == query:
            score += 20
        scores.append((score, -index, definition))
    scores.sort(key=lambda item: (item[0], item[1]), reverse=True)
    best = scores[0]
    if best[0] == 0:
        return IntentMatch(
            level_1="composite_analysis",
            level_2="supplier_comparison",
            confidence=0.35,
            alternatives=["clarify"],
        )
    alternatives = [item[2].level_2 for item in scores[1:3] if item[0] > 0]
    return IntentMatch(
        level_1=best[2].level_1,
        level_2=best[2].level_2,
        confidence=min(0.55 + best[0] * 0.04, 0.99),
        alternatives=alternatives,
    )
