"""In-memory, TTL-bound runtime repository with opaque bearer tokens."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from packages.contracts.models import ActionName, RunResult, RunStatus
from packages.observability import TraceRecorder


class AuthenticationError(RuntimeError):
    pass


class ExpiredError(RuntimeError):
    pass


class ConflictError(RuntimeError):
    def __init__(self, message: str, allowed_actions: list[ActionName]) -> None:
        super().__init__(message)
        self.allowed_actions = allowed_actions


@dataclass(frozen=True)
class WorkflowEvent:
    event_id: int
    event_type: str
    node: str
    status: RunStatus
    timestamp: datetime
    warning_codes: tuple[str, ...] = ()


@dataclass
class RunRecord[StateT]:
    run_id: str
    trace_id: str
    case_id: str
    scenario: str
    status: RunStatus
    current_node: str
    state: StateT
    trace: TraceRecorder
    session_token_hash: str
    stream_token_hash: str
    stream_token_consumed: bool
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    result: RunResult | None = None
    events: list[WorkflowEvent] = field(default_factory=list)
    action_results: dict[str, tuple[ActionName, RunStatus, str]] = field(default_factory=dict)

    def allowed_actions(self) -> list[ActionName]:
        if self.status == RunStatus.AWAITING_HUMAN:
            return [
                ActionName.CONFIRM,
                ActionName.REJECT,
                ActionName.SUPPLEMENT,
                ActionName.RESUME,
            ]
        if self.status == RunStatus.FAILED:
            return [ActionName.RESUME]
        return []


class InMemoryRunRepository[StateT]:
    def __init__(self, ttl_minutes: int = 30) -> None:
        self.ttl = timedelta(minutes=ttl_minutes)
        self._runs: dict[str, RunRecord[StateT]] = {}
        self._idempotency: dict[str, tuple[str, str]] = {}
        self._token_secret = secrets.token_bytes(32)
        self._lock = threading.RLock()

    @staticmethod
    def _hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _token(self, run_id: str, purpose: str) -> str:
        digest = hmac.new(
            self._token_secret,
            f"{run_id}:{purpose}".encode(),
            hashlib.sha256,
        ).hexdigest()
        return digest

    def create(
        self,
        *,
        case_id: str,
        scenario: str,
        state: StateT,
        idempotency_key: str | None,
        idempotency_fingerprint: str = "",
    ) -> tuple[RunRecord[StateT], str, str, bool]:
        with self._lock:
            if idempotency_key and idempotency_key in self._idempotency:
                existing_run_id, existing_fingerprint = self._idempotency[idempotency_key]
                if not secrets.compare_digest(existing_fingerprint, idempotency_fingerprint):
                    raise ConflictError("Idempotency-Key was reused for another request", [])
                existing = self._runs[existing_run_id]
                return (
                    existing,
                    self._token(existing.run_id, "session"),
                    self._token(existing.run_id, "stream"),
                    False,
                )

            now = datetime.now(UTC)
            run_id = f"run_{secrets.token_hex(12)}"
            trace_id = f"trace_{secrets.token_hex(12)}"
            session_token = self._token(run_id, "session")
            stream_token = self._token(run_id, "stream")
            record = RunRecord(
                run_id=run_id,
                trace_id=trace_id,
                case_id=case_id,
                scenario=scenario,
                status=RunStatus.CREATED,
                current_node="created",
                state=state,
                trace=TraceRecorder(trace_id),
                session_token_hash=self._hash(session_token),
                stream_token_hash=self._hash(stream_token),
                stream_token_consumed=False,
                created_at=now,
                updated_at=now,
                expires_at=now + self.ttl,
            )
            self._runs[run_id] = record
            if idempotency_key:
                self._idempotency[idempotency_key] = (run_id, idempotency_fingerprint)
            return record, session_token, stream_token, True

    def _active(self, run_id: str) -> RunRecord[StateT]:
        record = self._runs.get(run_id)
        if record is None:
            raise KeyError(run_id)
        if datetime.now(UTC) >= record.expires_at:
            record.status = RunStatus.EXPIRED
            raise ExpiredError(run_id)
        return record

    def get(self, run_id: str, session_token: str) -> RunRecord[StateT]:
        with self._lock:
            record = self._active(run_id)
            if not secrets.compare_digest(record.session_token_hash, self._hash(session_token)):
                raise AuthenticationError(run_id)
            return record

    def consume_stream_token(self, run_id: str, stream_token: str) -> RunRecord[StateT]:
        with self._lock:
            record = self._active(run_id)
            valid = secrets.compare_digest(record.stream_token_hash, self._hash(stream_token))
            if not valid or record.stream_token_consumed:
                raise AuthenticationError(run_id)
            record.stream_token_consumed = True
            return record

    def add_event(
        self,
        record: RunRecord[StateT],
        event_type: str,
        node: str,
        warning_codes: list[str] | None = None,
    ) -> None:
        with self._lock:
            now = datetime.now(UTC)
            record.updated_at = now
            record.current_node = node
            record.events.append(
                WorkflowEvent(
                    event_id=len(record.events) + 1,
                    event_type=event_type,
                    node=node,
                    status=record.status,
                    timestamp=now,
                    warning_codes=tuple(warning_codes or []),
                )
            )

    def check_action(
        self,
        record: RunRecord[StateT],
        action: ActionName,
        client_action_id: str,
    ) -> tuple[ActionName, RunStatus, str] | None:
        with self._lock:
            previous = record.action_results.get(client_action_id)
            if previous is not None:
                if previous[0] != action:
                    raise ConflictError("client_action_id was used for another action", [])
                return previous
            if action not in record.allowed_actions():
                raise ConflictError(
                    "Action is not valid for the current state", record.allowed_actions()
                )
            return None

    def remember_action(
        self,
        record: RunRecord[StateT],
        client_action_id: str,
        action: ActionName,
        next_node: str,
    ) -> None:
        with self._lock:
            record.action_results[client_action_id] = (action, record.status, next_node)
