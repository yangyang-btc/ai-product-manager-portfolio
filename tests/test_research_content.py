from __future__ import annotations

from pathlib import Path

import pytest

from tools.validate_research import ResearchValidationError, validate_research


def test_four_research_articles_are_complete_and_sourced() -> None:
    articles = validate_research()
    assert {article.slug for article in articles} == {
        "codex",
        "workbuddy",
        "claude-code",
        "cursor",
    }
    assert all(article.source_count >= 5 for article in articles)
    assert all(article.marker_counts["fact"] >= 8 for article in articles)
    assert all(2000 <= article.chinese_characters <= 3500 for article in articles)


def test_unofficial_source_domain_is_rejected(tmp_path: Path) -> None:
    research = tmp_path / "research"
    source_root = Path(__file__).resolve().parents[1] / "research"
    for path in source_root.rglob("*"):
        if path.is_file():
            target = research / path.relative_to(source_root)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
    sources = research / "codex" / "sources.yml"
    sources.write_text(
        sources.read_text(encoding="utf-8").replace(
            "https://openai.com/index/introducing-the-codex-app/",
            "https://example.com/unverified",
        ),
        encoding="utf-8",
    )
    with pytest.raises(ResearchValidationError, match="outside official domains"):
        validate_research(research)
