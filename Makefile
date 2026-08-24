.PHONY: bootstrap lint test build-pages test-browser-consoles verify-runtime-parity verify-research demo-quality demo-contract demo-rag demo-evaluation serve-portfolio serve-quality-api serve-quality-web serve-contract-console serve-rag-console serve-evaluation-lab

bootstrap:
	uv sync --dev
	pnpm install

lint:
	uv run ruff check apps packages projects tools tests
	uv run mypy
	pnpm lint

test:
	uv run pytest
	pnpm test

build-pages:
	CI=true pnpm build:pages

test-browser-consoles:
	CI=true pnpm test:browser-consoles

verify-runtime-parity:
	uv run pytest tests/test_contract_review_agent.py -q
	pnpm --filter @portfolio/contract-browser-runtime test
	uv run pytest tests/test_enterprise_rag_assistant.py -q
	pnpm --filter @portfolio/rag-browser-runtime test

verify-research:
	uv run pytest tests/test_research_content.py -q
	uv run python -m tools.validate_research

demo-quality:
	uv run python -m apps.quality_agent_api.demo --case incoming_material_001

demo-contract:
	uv run python -m projects.contract_review_agent.demo --case procurement_contract_001

demo-rag:
	uv run python -m projects.enterprise_rag_assistant.demo --case compound_query_001

demo-evaluation:
	uv run python -m apps.evaluation_lab.demo

serve-portfolio:
	pnpm --filter @portfolio/portfolio-web dev

serve-quality-api:
	uv run uvicorn apps.quality_agent_api.main:app --reload --port 8000

serve-quality-web:
	pnpm --filter @portfolio/quality-agent-web dev

serve-contract-console:
	pnpm --filter @portfolio/contract-console dev

serve-rag-console:
	pnpm --filter @portfolio/rag-console dev

serve-evaluation-lab:
	EVALUATION_LAB_MODE=local uv run python -m streamlit run apps/evaluation_lab/app.py
