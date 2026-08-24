"""Small deterministic BM25 implementation for offline fixtures."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field

TERM_ALIASES = {
    "漏率": "泄漏率",
    "氦检": "氦质谱检漏",
    "阀件": "阀组件",
    "治具": "夹具",
}


def normalize_terms(text: str) -> str:
    normalized = text.lower().strip()
    for alias, canonical in TERM_ALIASES.items():
        normalized = normalized.replace(alias, canonical)
    return normalized


def _tokens(text: str) -> list[str]:
    normalized = normalize_terms(text)
    ascii_words = re.findall(r"[a-z0-9_.-]+", normalized)
    han_runs = re.findall(r"[\u4e00-\u9fff]+", normalized)
    han_tokens: list[str] = []
    for run in han_runs:
        han_tokens.extend(run[index : index + 2] for index in range(max(len(run) - 1, 1)))
    return ascii_words + han_tokens


@dataclass(frozen=True)
class Document:
    document_id: str
    version: str
    title: str
    text: str
    source: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievalHit:
    document: Document
    score: float
    rank: int


def lexical_search(query: str, documents: list[Document], top_k: int = 5) -> list[RetrievalHit]:
    if top_k < 1:
        raise ValueError("top_k must be positive")
    if not documents:
        return []

    query_tokens = _tokens(query)
    if not query_tokens:
        return []
    tokenized = [_tokens(document.text + " " + document.title) for document in documents]
    average_length = sum(len(tokens) for tokens in tokenized) / len(tokenized)
    document_frequency: Counter[str] = Counter()
    for tokens in tokenized:
        document_frequency.update(set(tokens))

    scores: list[tuple[float, str, Document]] = []
    k1 = 1.5
    b = 0.75
    for document, tokens in zip(documents, tokenized, strict=True):
        frequencies = Counter(tokens)
        score = 0.0
        for term in query_tokens:
            frequency = frequencies[term]
            if frequency == 0:
                continue
            df = document_frequency[term]
            inverse_frequency = math.log(1 + (len(documents) - df + 0.5) / (df + 0.5))
            denominator = frequency + k1 * (
                1 - b + b * len(tokens) / max(average_length, 1)
            )
            score += inverse_frequency * frequency * (k1 + 1) / denominator
        if score > 0:
            scores.append((score, document.document_id, document))

    scores.sort(key=lambda item: (-item[0], item[1]))
    return [
        RetrievalHit(document=document, score=round(score, 6), rank=index + 1)
        for index, (score, _, document) in enumerate(scores[:top_k])
    ]
