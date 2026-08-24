"""Terminal entry point proving the offline workflow without static shortcuts."""

from __future__ import annotations

import argparse
import json

from packages.contracts.models import ActionName, RunCreateRequest
from projects.quality_anomaly_agent.service import CASE_SCENARIOS, QualityAgentService


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the quality anomaly Agent offline")
    parser.add_argument("--case", default="incoming_material_001", choices=CASE_SCENARIOS)
    args = parser.parse_args()
    service = QualityAgentService()
    created = service.create_run(
        RunCreateRequest(
            case_id=args.case,
            scenario=CASE_SCENARIOS[args.case],  # type: ignore[arg-type]
            mode="offline",
            client_version="cli-v1",
        )
    )
    record = service.authorize(created.run_id, created.session_token)
    service.apply_action(
        record,
        action=ActionName.CONFIRM,
        payload={},
        client_action_id="cli-confirm-1",
    )
    bundle = service.bundle(record)
    print(json.dumps(bundle.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
