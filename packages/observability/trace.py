"""Trace collection that stores counts and codes, not raw business payloads."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from packages.contracts.models import TraceNode, TraceView


@dataclass
class _ActiveNode:
    sequence: int
    started: float
    input_count: int


class TraceRecorder:
    def __init__(self, trace_id: str) -> None:
        self.trace_id = trace_id
        self._nodes: list[TraceNode] = []
        self._active: dict[str, _ActiveNode] = {}
        self._estimated_tokens = 0
        self._estimated_cost_usd = 0.0
        self._warnings: list[str] = []

    def start(self, node: str, input_count: int = 0) -> None:
        self._active[node] = _ActiveNode(
            sequence=len(self._nodes) + 1,
            started=perf_counter(),
            input_count=input_count,
        )

    def complete(
        self,
        node: str,
        *,
        output_count: int = 0,
        warning_codes: list[str] | None = None,
    ) -> TraceNode:
        active = self._active.pop(node)
        event = TraceNode(
            sequence=active.sequence,
            node=node,
            status="completed",
            duration_ms=max(int((perf_counter() - active.started) * 1000), 0),
            input_count=active.input_count,
            output_count=output_count,
            warning_codes=warning_codes or [],
        )
        self._nodes.append(event)
        for warning_code in warning_codes or []:
            self.add_warning(warning_code)
        return event

    def fail(self, node: str, warning_code: str) -> TraceNode:
        active = self._active.pop(node)
        event = TraceNode(
            sequence=active.sequence,
            node=node,
            status="failed",
            duration_ms=max(int((perf_counter() - active.started) * 1000), 0),
            input_count=active.input_count,
            output_count=0,
            warning_codes=[warning_code],
        )
        self._nodes.append(event)
        self.add_warning(warning_code)
        return event

    def add_model_usage(self, input_tokens: int, output_tokens: int) -> None:
        tokens = max(input_tokens, 0) + max(output_tokens, 0)
        self._estimated_tokens += tokens
        self._estimated_cost_usd += tokens * 0.000002

    def add_warning(self, code: str) -> None:
        if code not in self._warnings:
            self._warnings.append(code)

    def view(self) -> TraceView:
        return TraceView(
            trace_id=self.trace_id,
            nodes=self._nodes,
            total_duration_ms=sum(node.duration_ms for node in self._nodes),
            estimated_tokens=self._estimated_tokens,
            estimated_cost_usd=round(self._estimated_cost_usd, 6),
            warnings=self._warnings,
        )
