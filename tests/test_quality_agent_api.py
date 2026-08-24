from __future__ import annotations

from typing import cast

from fastapi.testclient import TestClient

from apps.quality_agent_api.main import create_app
from projects.quality_anomaly_agent.service import QualityAgentService


def _create(client: TestClient, case_id: str, scenario: str) -> dict[str, object]:
    response = client.post(
        "/api/v1/runs",
        json={
            "case_id": case_id,
            "scenario": scenario,
            "mode": "offline",
            "client_version": "test-v1",
        },
    )
    assert response.status_code == 200, response.text
    return cast(dict[str, object], response.json())


def _auth(created: dict[str, object]) -> dict[str, str]:
    return {"Authorization": f"Bearer {created['session_token']}"}


def test_incoming_material_end_to_end_human_loop_and_bundle() -> None:
    client = TestClient(create_app(QualityAgentService()))
    created = _create(client, "incoming_material_001", "incoming")
    run_id = str(created["run_id"])
    headers = _auth(created)

    snapshot = client.get(f"/api/v1/runs/{run_id}", headers=headers)
    assert snapshot.status_code == 200
    body = snapshot.json()
    assert body["status"] == "awaiting_human"
    assert len(body["result_summary"]["hypotheses"]) == 3
    assert len(body["result_summary"]["evidence"]) >= 3

    trace = client.get(f"/api/v1/runs/{run_id}/trace", headers=headers).json()
    assert [node["node"] for node in trace["nodes"]] == [
        "intake",
        "validate_case",
        "classify_scenario",
        "plan_queries",
        "fetch_qms_mes_erp_plm",
        "retrieve_sop_fmea_8d_cases",
        "build_evidence_graph",
        "generate_hypothesis_matrix",
        "validate_schema_and_evidence",
        "await_human",
    ]

    action = {
        "action": "confirm",
        "payload": {},
        "client_action_id": "confirm-001",
    }
    completed = client.post(
        f"/api/v1/runs/{run_id}/actions", headers=headers, json=action
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"

    replay = client.post(f"/api/v1/runs/{run_id}/actions", headers=headers, json=action)
    assert replay.status_code == 200
    assert replay.json() == completed.json()

    invalid = client.post(
        f"/api/v1/runs/{run_id}/actions",
        headers=headers,
        json={"action": "reject", "payload": {}, "client_action_id": "reject-002"},
    )
    assert invalid.status_code == 409

    bundle_response = client.get(f"/api/v1/runs/{run_id}/bundle", headers=headers)
    assert bundle_response.status_code == 200
    bundle = bundle_response.json()["run_bundle"]
    assert bundle["status"] == "completed"
    assert len(bundle["hypotheses"]) == 3
    assert bundle["metrics"]["schema_compliance"] == 1
    assert bundle["metrics"]["evidence_resolvability"] == 1
    assert bundle["metrics"]["unsupported_conclusion_rate"] == 0
    assert "raw_prompt" not in bundle


def test_no_evidence_never_generates_a_root_cause() -> None:
    client = TestClient(create_app(QualityAgentService()))
    created = _create(client, "no_evidence", "incoming")
    snapshot = client.get(
        f"/api/v1/runs/{created['run_id']}", headers=_auth(created)
    ).json()
    result = snapshot["result_summary"]
    assert snapshot["status"] == "awaiting_human"
    assert result["result_type"] == "clarification"
    assert result["hypotheses"] == []
    assert result["required_clarifications"] == [
        "material_id",
        "lot_id",
        "inspection_record",
    ]


def test_tool_timeout_keeps_partial_evidence_and_marks_degraded() -> None:
    client = TestClient(create_app(QualityAgentService()))
    created = _create(client, "tool_timeout", "delivery")
    headers = _auth(created)
    snapshot = client.get(f"/api/v1/runs/{created['run_id']}", headers=headers).json()
    trace = client.get(f"/api/v1/runs/{created['run_id']}/trace", headers=headers).json()
    assert snapshot["result_summary"]["result_type"] == "degraded"
    assert snapshot["result_summary"]["evidence"]
    assert snapshot["result_summary"]["hypotheses"] == []
    assert "TOOL_ERP_TIMEOUT" in trace["warnings"]


def test_sse_can_resume_after_last_event_id() -> None:
    client = TestClient(create_app(QualityAgentService()))
    created = _create(client, "incoming_material_001", "incoming")
    response = client.get(
        f"/api/v1/runs/{created['run_id']}/events",
        headers={
            "Authorization": f"Bearer {created['stream_token']}",
            "Last-Event-ID": "8",
        },
    )
    assert response.status_code == 200
    assert "id: 9" in response.text
    assert "id: 1\n" not in response.text


def test_evaluation_handoff_is_atomic_and_one_time() -> None:
    client = TestClient(create_app(QualityAgentService()))
    created = _create(client, "incoming_material_001", "incoming")
    headers = _auth(created)
    handoff_response = client.post(
        "/api/v1/evaluation-handoffs",
        headers=headers,
        json={"run_id": created["run_id"]},
    )
    assert handoff_response.status_code == 200
    handoff = handoff_response.json()
    assert "#handoff_id=" in handoff["redeem_url"]

    redeem_headers = {"Authorization": f"Bearer {handoff['redeem_token']}"}
    first = client.post(
        f"/api/v1/evaluation-handoffs/{handoff['handoff_id']}/redeem",
        headers=redeem_headers,
        json={"consumer": "evaluation-lab"},
    )
    second = client.post(
        f"/api/v1/evaluation-handoffs/{handoff['handoff_id']}/redeem",
        headers=redeem_headers,
        json={"consumer": "evaluation-lab"},
    )
    assert first.status_code == 200
    assert second.status_code == 410


def test_idempotency_key_does_not_execute_the_workflow_twice() -> None:
    service = QualityAgentService()
    client = TestClient(create_app(service))
    payload = {
        "case_id": "incoming_material_001",
        "scenario": "incoming",
        "mode": "offline",
        "client_version": "test-v1",
    }
    first = client.post(
        "/api/v1/runs", json=payload, headers={"Idempotency-Key": "same-request"}
    )
    second = client.post(
        "/api/v1/runs", json=payload, headers={"Idempotency-Key": "same-request"}
    )
    assert first.status_code == second.status_code == 200
    assert first.json()["run_id"] == second.json()["run_id"]
    assert first.json()["session_token"] == second.json()["session_token"]
    record = service.authorize(first.json()["run_id"], first.json()["session_token"])
    assert len(record.trace.view().nodes) == 10

    conflict = client.post(
        "/api/v1/runs",
        json={**payload, "case_id": "no_evidence"},
        headers={"Idempotency-Key": "same-request"},
    )
    assert conflict.status_code == 409


def test_local_react_origins_can_call_the_api() -> None:
    client = TestClient(create_app(QualityAgentService()))
    for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
        response = client.options(
            "/api/v1/runs",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,idempotency-key",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin
