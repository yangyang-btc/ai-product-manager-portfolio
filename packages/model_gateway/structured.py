"""Schema-bound generation for project-specific local workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from packages.model_gateway.gateway import GatewayConfig, ModelGatewayError


@dataclass(frozen=True)
class StructuredGeneration[OutputT: BaseModel]:
    output: OutputT
    estimated_input_tokens: int
    estimated_output_tokens: int
    provider: str
    repaired: bool = False


class StructuredGateway:
    """Use deterministic output offline and validated JSON for local real models."""

    def __init__(self, config: GatewayConfig | None = None) -> None:
        self.config = config or GatewayConfig.from_env()
        self.config.validate_for_runtime()

    def generate[OutputT: BaseModel](
        self,
        *,
        system_prompt: str,
        payload: dict[str, Any],
        output_model: type[OutputT],
        mock_output: OutputT,
    ) -> StructuredGeneration[OutputT]:
        serialized = json.dumps(payload, ensure_ascii=False)
        if self.config.provider == "mock":
            return StructuredGeneration(
                output=mock_output,
                estimated_input_tokens=max(len(serialized) // 4, 1),
                estimated_output_tokens=max(len(mock_output.model_dump_json()) // 4, 1),
                provider="mock",
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {"input": payload, "output_schema": output_model.model_json_schema()},
                    ensure_ascii=False,
                ),
            },
        ]
        repaired = False
        for attempt in range(2):
            data = self._request(messages)
            try:
                content = data["choices"][0]["message"]["content"]
                if not isinstance(content, str):
                    raise TypeError("message content is not text")
                output = output_model.model_validate_json(content)
                usage = data.get("usage", {})
                input_tokens = max(int(usage.get("prompt_tokens", len(serialized) // 4)), 0)
                output_tokens = max(int(usage.get("completion_tokens", len(content) // 4)), 0)
                self._validate_budget(input_tokens, output_tokens)
                return StructuredGeneration(
                    output=output,
                    estimated_input_tokens=input_tokens,
                    estimated_output_tokens=output_tokens,
                    provider="openai-compatible",
                    repaired=repaired,
                )
            except (KeyError, IndexError, TypeError, ValueError, ValidationError) as exc:
                if attempt == 1:
                    raise ModelGatewayError("Provider output failed schema validation") from exc
                repaired = True
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Repair the previous output and return only schema-compliant JSON."
                        ),
                    }
                )
        raise ModelGatewayError("Unreachable provider state")

    def _request(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        try:
            response = httpx.post(
                f"{self.config.base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "max_tokens": self.config.max_tokens,
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                },
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ModelGatewayError("OpenAI-compatible provider request failed") from exc
        if not isinstance(data, dict):
            raise ModelGatewayError("Provider returned a non-object response")
        return data

    def _validate_budget(self, input_tokens: int, output_tokens: int) -> None:
        if output_tokens > self.config.max_tokens:
            raise ModelGatewayError("Provider response exceeded the configured token budget")
        if (input_tokens + output_tokens) * 0.000002 > self.config.max_estimated_cost_usd:
            raise ModelGatewayError("Provider response exceeded the estimated cost budget")
