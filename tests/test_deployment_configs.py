from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_render_blueprint_is_public_mock_only() -> None:
    blueprint = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
    service = blueprint["services"][0]
    env = {item["key"]: item for item in service["envVars"]}

    assert service["runtime"] == "python"
    assert service["healthCheckPath"] == "/health"
    assert "apps.quality_agent_api.main:app" in service["startCommand"]
    assert env["APP_MODE"]["value"] == "public"
    assert env["MODEL_PROVIDER"]["value"] == "mock"
    assert env["MODEL_KILL_SWITCH"]["value"] == "1"
    assert env["ALLOWED_ORIGINS"]["value"] == "https://yangyang-btc.github.io"
    assert env["EVALUATION_LAB_URL"]["sync"] is False


def test_cloud_requirements_cover_runtime_dependencies() -> None:
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    for package in ("fastapi", "httpx", "langgraph", "pydantic", "PyYAML", "streamlit", "uvicorn"):
        assert package in requirements


def test_streamlit_cloud_keeps_security_defaults_enabled() -> None:
    config = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert "headless = true" in config
    assert "enableCORS = true" in config
    assert "enableXsrfProtection = true" in config
