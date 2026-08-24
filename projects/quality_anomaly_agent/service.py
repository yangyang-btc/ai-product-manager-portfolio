"""Application service coordinating workflow, state, evaluation, and safe export."""

from __future__ import annotations

import hashlib
import secrets
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from packages.agent_core import (
    InMemoryRunRepository,
    RunRecord,
    assert_bundle_safe,
)
from packages.contracts.models import (
    ActionName,
    ActionResponse,
    BundleIdentity,
    RunBundle,
    RunCreateRequest,
    RunCreateResponse,
    RunSnapshot,
    RunStatus,
    TraceView,
)
from packages.evaluation import evaluate_quality_run
from packages.model_gateway import GatewayConfig, ModelGateway
from projects.quality_anomaly_agent.fixtures import load_fixture
from projects.quality_anomaly_agent.workflow import QualityState, QualityWorkflow

CASE_SCENARIOS = {
    "incoming_material_001": "incoming",
    "no_evidence": "incoming",
    "tool_timeout": "delivery",
}


@dataclass
class _Handoff:
    handoff_id: str
    token_hash: str
    bundle: RunBundle
    expires_at: datetime
    redeemed: bool = False


class HandoffGoneError(RuntimeError):
    pass


class QualityAgentService:
    dataset_version = "quality-fixtures-v1"
    prompt_version = "quality-hypothesis-v1"
    config_version = "runtime-config-v1"

    def __init__(self, gateway_config: GatewayConfig | None = None) -> None:
        self.gateway = ModelGateway(gateway_config or GatewayConfig.from_env())
        self.workflow = QualityWorkflow(self.gateway)
        self.repository: InMemoryRunRepository[QualityState] = InMemoryRunRepository(
            ttl_minutes=30
        )
        self._handoffs: dict[str, _Handoff] = {}
        self._handoff_lock = threading.RLock()

    def create_run(
        self,
        request: RunCreateRequest,
        idempotency_key: str | None = None,
    ) -> RunCreateResponse:
        expected_scenario = CASE_SCENARIOS.get(request.case_id)
        if expected_scenario is None:
            raise KeyError(request.case_id)
        if request.scenario != expected_scenario:
            raise ValueError(
                f"case_id {request.case_id} belongs to scenario {expected_scenario}"
            )
        fixture = load_fixture(request.case_id)
        seed_state: QualityState = {"case_id": request.case_id, "scenario": request.scenario}
        record, session_token, stream_token, created = self.repository.create(
            case_id=request.case_id,
            scenario=request.scenario,
            state=seed_state,
            idempotency_key=idempotency_key,
            idempotency_fingerprint=hashlib.sha256(
                request.model_dump_json().encode("utf-8")
            ).hexdigest(),
        )
        if created:
            self._execute_initial(record, fixture)
        return RunCreateResponse(
            run_id=record.run_id,
            case_id=record.case_id,
            trace_id=record.trace_id,
            session_token=session_token,
            stream_token=stream_token,
            status=record.status,
            expires_at=record.expires_at,
        )

    def _execute_initial(self, record: RunRecord[QualityState], fixture: object) -> None:
        from projects.quality_anomaly_agent.fixtures import QualityFixture

        if not isinstance(fixture, QualityFixture):
            raise TypeError("fixture must be QualityFixture")
        record.status = RunStatus.RUNNING
        try:
            state = self.workflow.run_initial(
                fixture=fixture,
                scenario=record.scenario,
                trace=record.trace,
            )
            record.state = state
            record.result = state["result"]
            for node in record.trace.view().nodes:
                if node.node == "await_human":
                    record.status = RunStatus.AWAITING_HUMAN
                    event_type = "awaiting_human"
                else:
                    event_type = "node_completed"
                self.repository.add_event(
                    record,
                    event_type,
                    node.node,
                    warning_codes=node.warning_codes,
                )
            record.status = RunStatus.AWAITING_HUMAN
            record.current_node = "await_human"
        except Exception:
            record.status = RunStatus.FAILED
            record.current_node = "failed"
            self.repository.add_event(record, "failed", "failed", ["WORKFLOW_FAILED"])
            raise

    def authorize(self, run_id: str, session_token: str) -> RunRecord[QualityState]:
        return self.repository.get(run_id, session_token)

    def authorize_stream(self, run_id: str, stream_token: str) -> RunRecord[QualityState]:
        return self.repository.consume_stream_token(run_id, stream_token)

    @staticmethod
    def snapshot(record: RunRecord[QualityState]) -> RunSnapshot:
        return RunSnapshot(
            run_id=record.run_id,
            case_id=record.case_id,
            status=record.status,
            current_node=record.current_node,
            result_summary=record.result,
            allowed_actions=record.allowed_actions(),
            updated_at=record.updated_at,
            expires_at=record.expires_at,
        )

    def apply_action(
        self,
        record: RunRecord[QualityState],
        *,
        action: ActionName,
        payload: dict[str, str],
        client_action_id: str,
    ) -> ActionResponse:
        previous = self.repository.check_action(record, action, client_action_id)
        if previous is not None:
            return ActionResponse(
                run_id=record.run_id,
                status=previous[1],
                accepted_action=previous[0],
                next_node=previous[2],
            )
        record.status = RunStatus.RUNNING
        self.repository.add_event(record, "node_started", "supplement_or_finalize")
        record.state = self.workflow.resume(
            state=record.state,
            action=action,
            supplement_present=bool(payload),
        )
        record.result = record.state["result"]
        record.status = RunStatus.COMPLETED
        record.current_node = "completed"
        self.repository.add_event(record, "completed", "supplement_or_finalize")
        self.repository.remember_action(
            record, client_action_id, action, "completed"
        )
        return ActionResponse(
            run_id=record.run_id,
            status=record.status,
            accepted_action=action,
            next_node="completed",
        )

    @staticmethod
    def trace(record: RunRecord[QualityState]) -> TraceView:
        return record.trace.view()

    def bundle(self, record: RunRecord[QualityState]) -> RunBundle:
        result = record.result
        if result is None:
            raise ValueError("Run has no result to export")
        evaluation = evaluate_quality_run(
            evidence=result.evidence,
            hypotheses=result.hypotheses,
            status=record.status,
            human_required=True,
        )
        trace = record.trace.view()
        bundle = RunBundle(
            run_id=record.run_id,
            case_id=record.case_id,
            scenario=record.scenario,
            status=record.status,
            identity=BundleIdentity(
                workflow_version=self.workflow.version,
                dataset_version=self.dataset_version,
                prompt_version=self.prompt_version,
                config_version=self.config_version,
                model_provider=self.gateway.config.provider,
                seed=self.gateway.config.seed,
            ),
            nodes=trace.nodes,
            evidence=result.evidence,
            hypotheses=result.hypotheses,
            metrics=evaluation.metrics,
            estimated_tokens=trace.estimated_tokens,
            estimated_cost_usd=trace.estimated_cost_usd,
            warnings=trace.warnings,
            generated_at=datetime.now(UTC),
        )
        assert_bundle_safe(bundle)
        return bundle

    @staticmethod
    def _hash(value: str) -> str:
        import hashlib

        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def create_handoff(
        self, record: RunRecord[QualityState]
    ) -> tuple[str, str, datetime]:
        bundle = self.bundle(record)
        handoff_id = f"handoff_{secrets.token_hex(12)}"
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(minutes=15)
        with self._handoff_lock:
            self._handoffs[handoff_id] = _Handoff(
                handoff_id=handoff_id,
                token_hash=self._hash(token),
                bundle=bundle,
                expires_at=expires_at,
            )
        return handoff_id, token, expires_at

    def redeem_handoff(self, handoff_id: str, token: str) -> RunBundle:
        with self._handoff_lock:
            handoff = self._handoffs.get(handoff_id)
            if (
                handoff is None
                or handoff.redeemed
                or datetime.now(UTC) >= handoff.expires_at
                or not secrets.compare_digest(handoff.token_hash, self._hash(token))
            ):
                raise HandoffGoneError(handoff_id)
            handoff.redeemed = True
            return handoff.bundle
