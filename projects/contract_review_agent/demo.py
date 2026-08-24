from __future__ import annotations

import argparse
import json

from projects.contract_review_agent.evaluation import evaluate_contract_cases
from projects.contract_review_agent.fixtures import CASE_IDS
from projects.contract_review_agent.runtime import run_contract_review


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the contract-review Agent locally")
    parser.add_argument("--case", choices=CASE_IDS, default="procurement_contract_001")
    parser.add_argument("--evaluate", action="store_true")
    args = parser.parse_args()
    result = evaluate_contract_cases() if args.evaluate else run_contract_review(args.case)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
