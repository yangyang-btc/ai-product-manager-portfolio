"""Bounded model gateway used by project workflows."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Literal, Protocol, cast

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from packages.contracts.models import Evidence, Hypothesis, ValidationAction


class ModelGatewayError(RuntimeError):
    """A safe, observable model-provider failure."""


@dataclass(frozen=True)
class GatewayConfig:
    provider: Literal["mock", "openai-compatible"] = "mock"
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    timeout_seconds: float = 20.0
    max_tokens: int = 1200
    max_estimated_cost_usd: float = 0.05
    seed: int = 42

    @classmethod
    def from_env(cls) -> GatewayConfig:
        app_mode = os.getenv("APP_MODE", "offline")
        configured_provider = os.getenv("MODEL_PROVIDER", "mock")
        kill_switch = os.getenv("MODEL_KILL_SWITCH", "0") == "1"
        if app_mode == "public" or kill_switch:
            provider: Literal["mock", "openai-compatible"] = "mock"
        elif configured_provider in {"mock", "openai-compatible"}:
            provider = cast(Literal["mock", "openai-compatible"], configured_provider)
        else:
            raise ModelGatewayError("MODEL_PROVIDER must be mock or openai-compatible")
        return cls(
            provider=provider,
            base_url=os.getenv("OPENAI_COMPATIBLE_BASE_URL", ""),
            api_key=os.getenv("OPENAI_COMPATIBLE_API_KEY", ""),
            model=os.getenv("OPENAI_COMPATIBLE_MODEL", ""),
            timeout_seconds=float(os.getenv("MODEL_TIMEOUT_SECONDS", "20")),
            max_tokens=int(os.getenv("MODEL_MAX_TOKENS", "1200")),
            max_estimated_cost_usd=float(os.getenv("MODEL_MAX_ESTIMATED_COST_USD", "0.05")),
        )

    def validate_for_runtime(self) -> None:
        if self.max_tokens < 1 or self.max_tokens > 4000:
            raise ModelGatewayError("MODEL_MAX_TOKENS must be between 1 and 4000")
        if self.timeout_seconds <= 0 or self.timeout_seconds > 60:
            raise ModelGatewayError("MODEL_TIMEOUT_SECONDS must be between 0 and 60")
        if self.provider == "openai-compatible" and not all(
            [self.base_url, self.api_key, self.model]
        ):
            raise ModelGatewayError(
                "Real-model mode requires OPENAI_COMPATIBLE_BASE_URL, "
                "OPENAI_COMPATIBLE_API_KEY, and OPENAI_COMPATIBLE_MODEL"
            )


class ModelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hypotheses: list[Hypothesis]
    estimated_input_tokens: int = Field(ge=0)
    estimated_output_tokens: int = Field(ge=0)
    provider: Literal["mock", "openai-compatible"]
    repaired: bool = False


class Provider(Protocol):
    def generate(self, *, case_id: str, evidence: list[Evidence]) -> ModelResponse: ...


def _find_id(evidence: list[Evidence], source: str, fallback: str) -> str:
    return next((item.evidence_id for item in evidence if item.source == source), fallback)


def _find_record(evidence: list[Evidence], record_id: str, fallback: str) -> str:
    return next(
        (item.evidence_id for item in evidence if item.source_record_id == record_id), fallback
    )


class MockProvider:
    """Seeded, evidence-bound response generator for offline public demos."""

    def __init__(self, config: GatewayConfig) -> None:
        self.config = config

    def generate(self, *, case_id: str, evidence: list[Evidence]) -> ModelResponse:
        if case_id != "incoming_material_001":
            return ModelResponse(
                hypotheses=[],
                estimated_input_tokens=80 + len(evidence) * 25,
                estimated_output_tokens=20,
                provider="mock",
            )

        qms_id = _find_id(evidence, "QMS", "")
        plm_id = _find_id(evidence, "PLM", "")
        fmea_id = _find_id(evidence, "FMEA", "")
        case_ids = [item.evidence_id for item in evidence if item.source == "CASE"]
        erp_id = _find_id(evidence, "ERP", "")
        visual_id = _find_record(evidence, "IR-DEMO-002", qms_id)
        if not qms_id or not plm_id:
            raise ModelGatewayError("Required measurement and specification evidence is missing")

        fixture_case = case_ids[0] if case_ids else qms_id
        defect_case = case_ids[1] if len(case_ids) > 1 else fmea_id
        hypotheses = [
            Hypothesis(
                hypothesis_id="H1",
                direction="测量系统或检漏夹具污染",
                confidence="medium",
                reasoning_summary="当前超限由有效检验与规范确认，历史相似案例支持先排查测量链路。",
                supporting_evidence_ids=[qms_id, plm_id, fixture_case],
                counter_evidence_ids=[visual_id],
                missing_information=["夹具本底测试结果", "独立设备复测结果"],
                validation_actions=[
                    ValidationAction(
                        action_id="VA-H1-01",
                        action="执行夹具空白检漏并使用独立设备复测",
                        owner_role="质量工程师",
                        target="当前来料批次与检漏夹具",
                        expected_result="区分产品泄漏与测量系统偏差",
                    )
                ],
            ),
            Hypothesis(
                hypothesis_id="H2",
                direction="密封面缺陷或表面污染",
                confidence="medium",
                reasoning_summary="FMEA 与历史案例支持密封界面方向，但外观合格不能排除微观缺陷。",
                supporting_evidence_ids=[qms_id, fmea_id, defect_case],
                counter_evidence_ids=[visual_id],
                missing_information=["密封面显微检查结果"],
                validation_actions=[
                    ValidationAction(
                        action_id="VA-H2-01",
                        action="清洁密封面后复测并进行显微检查",
                        owner_role="质量工程师",
                        target="抽样阀组件密封面",
                        expected_result="确认污染可逆性或微观缺陷证据",
                    )
                ],
            ),
            Hypothesis(
                hypothesis_id="H3",
                direction="供应商当前批次过程波动",
                confidence="low",
                reasoning_summary="异常集中于当前批次，但同供应商历史批次合格，不能直接认定供应商根因。",
                supporting_evidence_ids=[qms_id, erp_id],
                counter_evidence_ids=[erp_id],
                missing_information=["扩大抽样结果", "供应商本批过程记录"],
                validation_actions=[
                    ValidationAction(
                        action_id="VA-H3-01",
                        action="扩大批内抽样并请求供应商过程记录",
                        owner_role="供应商质量工程师",
                        target="当前来料批次",
                        expected_result="判断异常是否具有批次聚集性",
                    )
                ],
            ),
        ]
        return ModelResponse(
            hypotheses=hypotheses,
            estimated_input_tokens=220 + len(evidence) * 35,
            estimated_output_tokens=410,
            provider="mock",
        )


class OpenAICompatibleProvider:
    """Local-only OpenAI-compatible provider with one schema-repair attempt."""

    def __init__(self, config: GatewayConfig) -> None:
        self.config = config

    def _request(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        try:
            response = httpx.post(
                f"{self.config.base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ModelGatewayError("OpenAI-compatible provider request failed") from exc
        if not isinstance(data, dict):
            raise ModelGatewayError("Provider returned a non-object response")
        return data

    @staticmethod
    def _content(data: dict[str, Any]) -> str:
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelGatewayError("Provider response is missing message content") from exc
        if not isinstance(content, str):
            raise ModelGatewayError("Provider message content is not text")
        return content

    def generate(self, *, case_id: str, evidence: list[Evidence]) -> ModelResponse:
        safe_context = [
            {
                "evidence_id": item.evidence_id,
                "source": item.source,
                "summary": item.public_summary,
            }
            for item in evidence
        ]
        system = (
            "Return JSON with a hypotheses array that conforms to the supplied schema. "
            "Every supporting or counter evidence ID must exist in the context. "
            "Never claim a deterministic root cause."
        )
        user = json.dumps(
            {
                "case_id": case_id,
                "evidence": safe_context,
                "hypothesis_schema": Hypothesis.model_json_schema(),
            },
            ensure_ascii=False,
        )
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        repaired = False
        for attempt in range(2):
            data = self._request(messages)
            try:
                parsed = json.loads(self._content(data))
                hypotheses = _HypothesisEnvelope.model_validate(parsed).hypotheses
                usage = data.get("usage", {})
                input_tokens = int(usage.get("prompt_tokens", len(user) // 4))
                output_tokens = int(usage.get("completion_tokens", 0))
                return ModelResponse(
                    hypotheses=hypotheses,
                    estimated_input_tokens=max(input_tokens, 0),
                    estimated_output_tokens=max(output_tokens, 0),
                    provider="openai-compatible",
                    repaired=repaired,
                )
            except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
                if attempt == 1:
                    raise ModelGatewayError("Provider output failed schema validation") from exc
                repaired = True
                messages.append(
                    {
                        "role": "user",
                        "content": "Repair the previous output. Return only schema-compliant JSON.",
                    }
                )
        raise ModelGatewayError("Unreachable provider state")


class _HypothesisEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hypotheses: list[Hypothesis]


class ModelGateway:
    def __init__(self, config: GatewayConfig | None = None) -> None:
        self.config = config or GatewayConfig()
        self.config.validate_for_runtime()
        self.provider: Provider
        if self.config.provider == "mock":
            self.provider = MockProvider(self.config)
        else:
            self.provider = OpenAICompatibleProvider(self.config)

    def generate_hypotheses(self, *, case_id: str, evidence: list[Evidence]) -> ModelResponse:
        response = self.provider.generate(case_id=case_id, evidence=evidence)
        if response.estimated_output_tokens > self.config.max_tokens:
            raise ModelGatewayError("Provider response exceeded the configured token budget")
        token_total = response.estimated_input_tokens + response.estimated_output_tokens
        estimated_cost = token_total * 0.000002
        if estimated_cost > self.config.max_estimated_cost_usd:
            raise ModelGatewayError("Provider response exceeded the estimated cost budget")
        return response
