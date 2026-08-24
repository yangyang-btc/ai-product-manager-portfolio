from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dist-pages"
BASE_URL = "/ai-product-manager-portfolio/"


@pytest.fixture(scope="module", autouse=True)
def pages_artifact() -> None:
    env = {
        **{
            key: os.environ[key]
            for key in ("PATH", "HOME", "SHELL", "TMPDIR")
            if key in os.environ
        },
        "CI": "true",
        "BASE_URL": BASE_URL,
        "GITHUB_REPO_URL": "https://github.com/example/ai-product-manager-portfolio",
        "EVALUATION_LAB_URL": "https://evaluation.example.test",
        "QUALITY_API_URL": "https://quality-api.example.test",
    }
    subprocess.run(
        ["node", "tools/build_pages_artifact.mjs"],
        cwd=ROOT,
        env=env,
        check=True,
    )


def _bundled_text(relative: str) -> str:
    root = OUTPUT / relative
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file() and path.suffix in {".html", ".js", ".css"}
    )


def test_pages_artifact_has_fixed_application_entries() -> None:
    expected = {
        "index.html",
        "quality-agent/index.html",
        "contract-console/index.html",
        "rag-console/index.html",
    }
    assert all((OUTPUT / path).is_file() for path in expected)


@pytest.mark.parametrize(
    ("relative", "asset_prefix"),
    [
        ("index.html", f"{BASE_URL}assets/"),
        ("quality-agent/index.html", f"{BASE_URL}quality-agent/assets/"),
        ("contract-console/index.html", f"{BASE_URL}contract-console/assets/"),
        ("rag-console/index.html", f"{BASE_URL}rag-console/assets/"),
    ],
)
def test_each_entry_uses_repository_base(relative: str, asset_prefix: str) -> None:
    html = (OUTPUT / relative).read_text(encoding="utf-8")
    paths = re.findall(r'(?:src|href)="([^"]+assets/[^"]+)"', html)
    assert paths
    assert all(path.startswith(asset_prefix) for path in paths)


def test_portfolio_contains_four_research_routes_and_console_links() -> None:
    bundle = _bundled_text("")
    assert "#/research/" in bundle
    for slug in ("codex", "workbuddy", "claude-code", "cursor"):
        assert slug in bundle
    for path in ("quality-agent/", "contract-console/", "rag-console/"):
        assert f"{BASE_URL}{path}" in bundle
    assert "查看公开重建源码" in bundle
    assert "https://github.com/example/ai-product-manager-portfolio" in bundle
    assert "research/codex/article.md" in bundle


def test_cross_application_return_links_and_public_boundaries_are_bundled() -> None:
    quality = _bundled_text("quality-agent")
    contract = _bundled_text("contract-console")
    rag = _bundled_text("rag-console")
    assert f"{BASE_URL}#/project/quality" in quality
    assert f"{BASE_URL}#/project/contract" in contract
    assert f"{BASE_URL}#/project/rag" in rag
    assert "角色与权限只演示产品行为" in rag
    assert "http://localhost" not in "\n".join((quality, contract, rag))
