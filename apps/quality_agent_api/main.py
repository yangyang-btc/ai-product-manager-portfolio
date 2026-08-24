"""Versioned HTTP API for the online quality Agent demo."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from typing import Annotated, Any

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from packages.agent_core import AuthenticationError, ConflictError, ExpiredError
from packages.contracts.models import (
    ActionRequest,
    ActionResponse,
    RunCreateRequest,
    RunCreateResponse,
    RunSnapshot,
    TraceView,
)
from projects.quality_anomaly_agent.service import (
    HandoffGoneError,
    QualityAgentService,
)


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HandoffRequest(ApiModel):
    run_id: str


class HandoffResponse(ApiModel):
    handoff_id: str
    redeem_token: str
    redeem_url: str
    expires_at: str


class RedeemRequest(ApiModel):
    consumer: str = Field(pattern=r"^evaluation-lab$")


def _error(
    *,
    code: str,
    message: str,
    retryable: bool,
    status_code: int,
    run_id: str | None = None,
    trace_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "retryable": retryable,
                "run_id": run_id,
                "trace_id": trace_id,
                "details": details or {},
            }
        },
    )


def _bearer(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise AuthenticationError("Empty bearer token")
    return token


def create_app(service: QualityAgentService | None = None) -> FastAPI:
    runtime = service or QualityAgentService()
    app = FastAPI(
        title="Quality Anomaly Agent API",
        version="1.0.0",
        docs_url="/api/docs" if os.getenv("APP_MODE", "offline") != "public" else None,
    )
    app.state.quality_service = runtime
    allowed_origins = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "Last-Event-ID"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = {"fields": [".".join(str(part) for part in item["loc"]) for item in exc.errors()]}
        return _error(
            code="INVALID_INPUT",
            message="Request fields failed validation",
            retryable=False,
            status_code=422,
            details=details,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        code = "NOT_FOUND" if exc.status_code == 404 else "REQUEST_REJECTED"
        return _error(
            code=code,
            message=str(exc.detail),
            retryable=False,
            status_code=exc.status_code,
        )

    @app.exception_handler(KeyError)
    async def missing_run_handler(_request: Request, _exc: KeyError) -> JSONResponse:
        return _error(
            code="RUN_NOT_FOUND",
            message="The requested run does not exist",
            retryable=False,
            status_code=404,
        )

    @app.exception_handler(AuthenticationError)
    async def authentication_handler(_request: Request, _exc: AuthenticationError) -> JSONResponse:
        return _error(
            code="UNAUTHORIZED",
            message="The run token is invalid",
            retryable=False,
            status_code=401,
        )

    @app.exception_handler(ExpiredError)
    async def expired_handler(_request: Request, _exc: ExpiredError) -> JSONResponse:
        return _error(
            code="CHECKPOINT_EXPIRED",
            message="The in-memory run has expired; rerun or import a saved bundle",
            retryable=False,
            status_code=410,
        )

    @app.exception_handler(ConflictError)
    async def conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
        return _error(
            code="INVALID_STATE_TRANSITION",
            message=str(exc),
            retryable=False,
            status_code=409,
            details={"allowed_actions": [item.value for item in exc.allowed_actions]},
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "mode": os.getenv("APP_MODE", "offline"),
            "model_provider": runtime.gateway.config.provider,
        }

    @app.post("/api/v1/runs", response_model=RunCreateResponse)
    def create_run(
        body: RunCreateRequest,
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> RunCreateResponse:
        if idempotency_key is not None and len(idempotency_key) > 100:
            raise HTTPException(status_code=422, detail="Idempotency-Key too long")
        try:
            return runtime.create_run(body, idempotency_key=idempotency_key)
        except KeyError:
            raise HTTPException(status_code=404, detail="Unknown case_id") from None
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    def authorized_record(run_id: str, authorization: str | None) -> Any:
        return runtime.authorize(run_id, _bearer(authorization))

    @app.get("/api/v1/runs/{run_id}", response_model=RunSnapshot)
    def get_run(
        run_id: str,
        authorization: Annotated[str | None, Header()] = None,
    ) -> RunSnapshot:
        return runtime.snapshot(authorized_record(run_id, authorization))

    @app.get("/api/v1/runs/{run_id}/trace", response_model=TraceView)
    def get_trace(
        run_id: str,
        authorization: Annotated[str | None, Header()] = None,
    ) -> TraceView:
        return runtime.trace(authorized_record(run_id, authorization))

    @app.get("/api/v1/runs/{run_id}/bundle")
    def get_bundle(
        run_id: str,
        authorization: Annotated[str | None, Header()] = None,
    ) -> dict[str, Any]:
        bundle = runtime.bundle(authorized_record(run_id, authorization))
        return {"run_bundle": bundle.model_dump(mode="json")}

    @app.post("/api/v1/runs/{run_id}/actions", response_model=ActionResponse)
    def post_action(
        run_id: str,
        body: ActionRequest,
        authorization: Annotated[str | None, Header()] = None,
    ) -> ActionResponse:
        record = authorized_record(run_id, authorization)
        return runtime.apply_action(
            record,
            action=body.action,
            payload=body.payload,
            client_action_id=body.client_action_id,
        )

    @app.get("/api/v1/runs/{run_id}/events")
    def events(
        run_id: str,
        authorization: Annotated[str | None, Header()] = None,
        last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
    ) -> StreamingResponse:
        token = _bearer(authorization)
        try:
            record = runtime.authorize(run_id, token)
        except AuthenticationError:
            record = runtime.authorize_stream(run_id, token)
        try:
            after = int(last_event_id or "0")
        except ValueError:
            after = 0

        def event_stream() -> Iterator[str]:
            for event in record.events:
                if event.event_id <= after:
                    continue
                payload = {
                    "node": event.node,
                    "status": event.status.value,
                    "timestamp": event.timestamp.isoformat(),
                    "warning_codes": list(event.warning_codes),
                }
                yield (
                    f"id: {event.event_id}\n"
                    f"event: {event.event_type}\n"
                    f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                )

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @app.post("/api/v1/evaluation-handoffs", response_model=HandoffResponse)
    def create_handoff(
        body: HandoffRequest,
        authorization: Annotated[str | None, Header()] = None,
    ) -> HandoffResponse:
        record = authorized_record(body.run_id, authorization)
        handoff_id, redeem_token, expires_at = runtime.create_handoff(record)
        lab_url = os.getenv("EVALUATION_LAB_URL", "http://localhost:8501")
        fragment = f"handoff_id={handoff_id}&redeem_token={redeem_token}"
        return HandoffResponse(
            handoff_id=handoff_id,
            redeem_token=redeem_token,
            redeem_url=f"{lab_url.rstrip('/')}#{fragment}",
            expires_at=expires_at.isoformat(),
        )

    @app.post("/api/v1/evaluation-handoffs/{handoff_id}/redeem", response_model=None)
    def redeem_handoff(
        handoff_id: str,
        _body: RedeemRequest,
        authorization: Annotated[str | None, Header()] = None,
    ) -> dict[str, Any] | JSONResponse:
        token = _bearer(authorization)
        try:
            bundle = runtime.redeem_handoff(handoff_id, token)
        except HandoffGoneError:
            return _error(
                code="HANDOFF_GONE",
                message="The evaluation handoff is invalid, expired, or already redeemed",
                retryable=False,
                status_code=status.HTTP_410_GONE,
            )
        return {"run_bundle": bundle.model_dump(mode="json")}

    return app


app = create_app()
