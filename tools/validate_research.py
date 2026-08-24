from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = ROOT / "research"
REQUIRED_SECTIONS = (
    "一句话判断",
    "目标用户与核心任务",
    "产品定位与价值主张",
    "关键用户旅程",
    "Agent、Context 与 Tool 工作机制",
    "交互与信任设计",
    "商业化与增长逻辑",
    "评测指标设计",
    "局限与风险",
    "对 AI 产品经理的可迁移启发",
    "官方参考资料与调研日期",
)
MARKER_PATTERN = re.compile(
    r"\[(fact|marketing_claim|judgment|inference)(?::([A-Z0-9,-]+))?\]"
)
CHINESE_PATTERN = re.compile(r"[\u3400-\u9fff]")
URL_PATTERN = re.compile(r"https://[^\s)]+")
REQUIRED_SOURCE_FIELDS = (
    "id",
    "title",
    "url",
    "accessed_at",
    "applicable_version",
    "source_kind",
    "claim_scope",
    "license_note",
)


class ResearchValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ResearchArticle:
    slug: str
    article_path: Path
    sources_path: Path
    chinese_characters: int
    source_count: int
    marker_counts: dict[str, int]


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ResearchValidationError(f"{path}: cannot load YAML") from exc
    if not isinstance(payload, dict):
        raise ResearchValidationError(f"{path}: root must be a mapping")
    return payload


def _require(mapping: dict[str, Any], fields: tuple[str, ...], path: Path) -> None:
    missing = [field for field in fields if not mapping.get(field)]
    if missing:
        raise ResearchValidationError(f"{path}: missing {', '.join(missing)}")


def _domain_allowed(host: str, allowed: set[str]) -> bool:
    return any(host == domain or host.endswith(f".{domain}") for domain in allowed)


def _content_lines(article: str) -> list[str]:
    lines: list[str] = []
    in_fence = False
    for raw_line in article.splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def _validate_sources(path: Path) -> tuple[dict[str, dict[str, Any]], set[str]]:
    payload = _load_yaml(path)
    _require(
        payload,
        (
            "product",
            "vendor",
            "official_domains",
            "researched_at",
            "applicable_version",
            "sources",
        ),
        path,
    )
    if payload.get("schema_version") != 1:
        raise ResearchValidationError(f"{path}: schema_version must be 1")
    try:
        researched_at = date.fromisoformat(str(payload["researched_at"]))
    except ValueError as exc:
        raise ResearchValidationError(f"{path}: invalid researched_at") from exc
    if researched_at > date.today():
        raise ResearchValidationError(f"{path}: researched_at cannot be in the future")

    domains = payload["official_domains"]
    sources = payload["sources"]
    if not isinstance(domains, list) or not domains:
        raise ResearchValidationError(f"{path}: official_domains must be a list")
    if not isinstance(sources, list) or len(sources) < 5:
        raise ResearchValidationError(f"{path}: at least five sources are required")

    allowed = {str(domain).lower() for domain in domains}
    by_id: dict[str, dict[str, Any]] = {}
    for source in sources:
        if not isinstance(source, dict):
            raise ResearchValidationError(f"{path}: each source must be a mapping")
        _require(source, REQUIRED_SOURCE_FIELDS, path)
        source_id = str(source["id"])
        if source_id in by_id:
            raise ResearchValidationError(f"{path}: duplicate source id {source_id}")
        parsed = urlparse(str(source["url"]))
        if parsed.scheme != "https" or not parsed.hostname:
            raise ResearchValidationError(f"{path}: source {source_id} needs HTTPS")
        if not _domain_allowed(parsed.hostname.lower(), allowed):
            raise ResearchValidationError(
                f"{path}: source {source_id} is outside official domains"
            )
        try:
            date.fromisoformat(str(source["accessed_at"]))
        except ValueError as exc:
            raise ResearchValidationError(
                f"{path}: source {source_id} has invalid accessed_at"
            ) from exc
        by_id[source_id] = source
    return by_id, allowed


def _validate_article(
    slug: str,
    article_path: Path,
    source_path: Path,
) -> ResearchArticle:
    sources, allowed_domains = _validate_sources(source_path)
    try:
        article = article_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ResearchValidationError(f"{article_path}: cannot read article") from exc

    headings = re.findall(r"^## (.+)$", article, re.MULTILINE)
    positions: list[int] = []
    for section in REQUIRED_SECTIONS:
        if section not in headings:
            raise ResearchValidationError(f"{article_path}: missing section {section}")
        positions.append(headings.index(section))
    if positions != sorted(positions):
        raise ResearchValidationError(f"{article_path}: sections are out of order")

    chinese_characters = len(CHINESE_PATTERN.findall(article))
    if not 2000 <= chinese_characters <= 3500:
        raise ResearchValidationError(
            f"{article_path}: expected 2000-3500 Chinese characters, "
            f"got {chinese_characters}"
        )
    lowered = article.lower()
    if any(token in lowered for token in ("todo", "coming soon", "待补充", "占位")):
        raise ResearchValidationError(f"{article_path}: placeholder content detected")

    marker_counts = {
        "fact": 0,
        "marketing_claim": 0,
        "judgment": 0,
        "inference": 0,
    }
    referenced: set[str] = set()
    for line in _content_lines(article):
        markers = MARKER_PATTERN.findall(line)
        if not markers:
            raise ResearchValidationError(
                f"{article_path}: unclassified content line: {line[:48]}"
            )
        for kind, raw_ids in markers:
            marker_counts[kind] += 1
            source_ids = {item for item in raw_ids.split(",") if item}
            if kind in {"fact", "marketing_claim", "inference"} and not source_ids:
                raise ResearchValidationError(
                    f"{article_path}: {kind} marker requires source ids"
                )
            unknown = source_ids - sources.keys()
            if unknown:
                raise ResearchValidationError(
                    f"{article_path}: unknown sources {sorted(unknown)}"
                )
            referenced.update(source_ids)

    if marker_counts["fact"] < 8 or marker_counts["judgment"] < 6:
        raise ResearchValidationError(
            f"{article_path}: needs at least eight facts and six judgments"
        )
    if marker_counts["inference"] < 2:
        raise ResearchValidationError(f"{article_path}: needs at least two inferences")
    missing_references = sources.keys() - referenced
    if missing_references:
        raise ResearchValidationError(
            f"{article_path}: unreferenced sources {sorted(missing_references)}"
        )
    for url in URL_PATTERN.findall(article):
        host = urlparse(url.rstrip(".>")).hostname
        if not host or not _domain_allowed(host.lower(), allowed_domains):
            raise ResearchValidationError(f"{article_path}: non-official URL {url}")

    return ResearchArticle(
        slug=slug,
        article_path=article_path,
        sources_path=source_path,
        chinese_characters=chinese_characters,
        source_count=len(sources),
        marker_counts=marker_counts,
    )


def validate_research(root: Path = RESEARCH_ROOT) -> list[ResearchArticle]:
    index_path = root / "index.yml"
    index = _load_yaml(index_path)
    if index.get("schema_version") != 1:
        raise ResearchValidationError(f"{index_path}: schema_version must be 1")
    articles = index.get("articles")
    if not isinstance(articles, list) or len(articles) != 4:
        raise ResearchValidationError(f"{index_path}: exactly four articles required")
    slugs = [item.get("slug") for item in articles if isinstance(item, dict)]
    if len(slugs) != 4 or len(set(slugs)) != 4:
        raise ResearchValidationError(f"{index_path}: article slugs must be unique")

    validated = []
    for item in articles:
        if not isinstance(item, dict):
            raise ResearchValidationError(f"{index_path}: invalid article entry")
        _require(
            item,
            (
                "slug",
                "product",
                "vendor",
                "title",
                "summary",
                "tags",
                "reading_minutes",
                "updated_at",
            ),
            index_path,
        )
        slug = str(item["slug"])
        article_dir = root / slug
        validated.append(
            _validate_article(
                slug,
                article_dir / "article.md",
                article_dir / "sources.yml",
            )
        )
    return validated


def main() -> None:
    articles = validate_research()
    total_sources = sum(article.source_count for article in articles)
    print(f"Validated {len(articles)} research articles and {total_sources} sources.")


if __name__ == "__main__":
    main()
