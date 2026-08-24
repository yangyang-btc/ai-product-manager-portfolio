from __future__ import annotations

import argparse
import json

from projects.enterprise_rag_assistant.cases import QUERY_CASES
from projects.enterprise_rag_assistant.evaluation import evaluate_enterprise_cases
from projects.enterprise_rag_assistant.runtime import run_enterprise_query


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the enterprise RAG assistant locally")
    parser.add_argument("--case", choices=tuple(QUERY_CASES), default="compound_query_001")
    parser.add_argument("--evaluate", action="store_true")
    args = parser.parse_args()
    result = evaluate_enterprise_cases() if args.evaluate else run_enterprise_query(args.case)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
