"""LangGraph workflow for evidence-bound quality anomaly analysis."""

from __future__ import annotations

from typing import Literal, TypedDict, cast

from langgraph.graph import END, START, StateGraph

from packages.contracts.models import ActionName, Evidence, Hypothesis, RunResult
from packages.model_gateway import ModelGateway
from packages.observability import TraceRecorder
from projects.quality_anomaly_agent.fixtures import QualityFixture
from projects.quality_anomaly_agent.knowledge import retrieve_knowledge
from projects.quality_anomaly_agent.tools import fetch_business_evidence


class QualityState(TypedDict, total=False):
    case_id: str
    scenario: str
    fixture: QualityFixture
    trace: TraceRecorder
    evidence: list[Evidence]
    hypotheses: list[Hypothesis]
    facts: list[str]
    warnings: list[str]
    query_plan: list[str]
    stop_reason: str
    result: RunResult
    estimated_input_tokens: int
    estimated_output_tokens: int
    action: ActionName
    supplement_present: bool


class QualityWorkflow:
    version = "quality-workflow-v1"

    def __init__(self, gateway: ModelGateway | None = None) -> None:
        self.gateway = gateway or ModelGateway()
        builder = StateGraph(QualityState)
        builder.add_node("intake", self.intake)
        builder.add_node("validate_case", self.validate_case)
        builder.add_node("classify_scenario", self.classify_scenario)
        builder.add_node("plan_queries", self.plan_queries)
        builder.add_node("fetch_qms_mes_erp_plm", self.fetch_qms_mes_erp_plm)
        builder.add_node("retrieve_sop_fmea_8d_cases", self.retrieve_sop_fmea_8d_cases)
        builder.add_node("build_evidence_graph", self.build_evidence_graph)
        builder.add_node("generate_hypothesis_matrix", self.generate_hypothesis_matrix)
        builder.add_node("validate_schema_and_evidence", self.validate_schema_and_evidence)
        builder.add_node("await_human", self.await_human)
        builder.add_edge(START, "intake")
        builder.add_edge("intake", "validate_case")
        builder.add_conditional_edges(
            "validate_case",
            self.route_after_validation,
            {"continue": "classify_scenario", "clarify": "await_human"},
        )
        builder.add_edge("classify_scenario", "plan_queries")
        builder.add_edge("plan_queries", "fetch_qms_mes_erp_plm")
        builder.add_edge("fetch_qms_mes_erp_plm", "retrieve_sop_fmea_8d_cases")
        builder.add_edge("retrieve_sop_fmea_8d_cases", "build_evidence_graph")
        builder.add_edge("build_evidence_graph", "generate_hypothesis_matrix")
        builder.add_edge("generate_hypothesis_matrix", "validate_schema_and_evidence")
        builder.add_edge("validate_schema_and_evidence", "await_human")
        builder.add_edge("await_human", END)
        self.graph = builder.compile()

        resume_builder = StateGraph(QualityState)
        resume_builder.add_node("supplement_or_finalize", self.supplement_or_finalize)
        resume_builder.add_edge(START, "supplement_or_finalize")
        resume_builder.add_edge("supplement_or_finalize", END)
        self.resume_graph = resume_builder.compile()

    @staticmethod
    def _start(state: QualityState, node: str, input_count: int = 0) -> TraceRecorder:
        trace = state["trace"]
        trace.start(node, input_count=input_count)
        return trace

    def intake(self, state: QualityState) -> QualityState:
        trace = self._start(state, "intake", 1)
        fixture = state["fixture"]
        trace.complete("intake", output_count=1)
        return {"facts": list(fixture.expected.facts), "warnings": []}

    def validate_case(self, state: QualityState) -> QualityState:
        trace = self._start(state, "validate_case", 1)
        fixture = state["fixture"]
        missing_core = (
            not fixture.qms.inspection_records
            or fixture.plm.specification is None
            or (
                fixture.erp.material_lot is None
                and not (
                    fixture.failure_injection is not None
                    and fixture.failure_injection.system == "ERP"
                )
            )
        )
        if missing_core:
            result = RunResult(
                result_type="clarification",
                summary="证据不足，未生成原因假设；请先补充关键业务标识与记录。",
                facts=fixture.expected.facts,
                required_clarifications=fixture.expected.required_clarifications,
            )
            trace.complete("validate_case", output_count=0, warning_codes=["EVIDENCE_INSUFFICIENT"])
            trace.add_warning("EVIDENCE_INSUFFICIENT")
            return {"stop_reason": "missing_core_evidence", "result": result}
        trace.complete("validate_case", output_count=1)
        return {"stop_reason": ""}

    @staticmethod
    def route_after_validation(state: QualityState) -> Literal["continue", "clarify"]:
        return "clarify" if state.get("stop_reason") else "continue"

    def classify_scenario(self, state: QualityState) -> QualityState:
        trace = self._start(state, "classify_scenario", 1)
        scenario = state["scenario"]
        trace.complete("classify_scenario", output_count=1)
        return {"scenario": scenario}

    def plan_queries(self, state: QualityState) -> QualityState:
        trace = self._start(state, "plan_queries", 1)
        plan = ["QMS:异常与检验", "MES:使用与隔离", "ERP:批次履历", "PLM:生效规范"]
        trace.complete("plan_queries", output_count=len(plan))
        return {"query_plan": plan}

    def fetch_qms_mes_erp_plm(self, state: QualityState) -> QualityState:
        trace = self._start(state, "fetch_qms_mes_erp_plm", len(state["query_plan"]))
        batch = fetch_business_evidence(state["fixture"])
        for warning in batch.warnings:
            trace.add_warning(warning)
        trace.complete(
            "fetch_qms_mes_erp_plm",
            output_count=len(batch.evidence),
            warning_codes=batch.warnings,
        )
        return {"evidence": batch.evidence, "warnings": batch.warnings}

    def retrieve_sop_fmea_8d_cases(self, state: QualityState) -> QualityState:
        trace = self._start(state, "retrieve_sop_fmea_8d_cases", 1)
        retrieved = retrieve_knowledge(state["fixture"], top_k=5)
        warnings = list(state.get("warnings", []))
        if not retrieved:
            warnings.append("RAG_NO_RELIABLE_RESULT")
            trace.add_warning("RAG_NO_RELIABLE_RESULT")
        trace.complete(
            "retrieve_sop_fmea_8d_cases",
            output_count=len(retrieved),
            warning_codes=["RAG_NO_RELIABLE_RESULT"] if not retrieved else [],
        )
        return {"evidence": state.get("evidence", []) + retrieved, "warnings": warnings}

    def build_evidence_graph(self, state: QualityState) -> QualityState:
        evidence = state.get("evidence", [])
        trace = self._start(state, "build_evidence_graph", len(evidence))
        seen: set[str] = set()
        duplicates: list[str] = []
        for item in evidence:
            if item.evidence_id in seen:
                duplicates.append(item.evidence_id)
            seen.add(item.evidence_id)
        if duplicates:
            trace.fail("build_evidence_graph", "DUPLICATE_EVIDENCE_ID")
            raise ValueError(f"Duplicate evidence IDs: {duplicates}")
        trace.complete("build_evidence_graph", output_count=len(seen))
        return {"evidence": evidence}

    def generate_hypothesis_matrix(self, state: QualityState) -> QualityState:
        evidence = state.get("evidence", [])
        trace = self._start(state, "generate_hypothesis_matrix", len(evidence))
        response = self.gateway.generate_hypotheses(case_id=state["case_id"], evidence=evidence)
        trace.add_model_usage(response.estimated_input_tokens, response.estimated_output_tokens)
        warning_codes = ["SCHEMA_REPAIRED"] if response.repaired else []
        trace.complete(
            "generate_hypothesis_matrix",
            output_count=len(response.hypotheses),
            warning_codes=warning_codes,
        )
        return {
            "hypotheses": response.hypotheses,
            "estimated_input_tokens": response.estimated_input_tokens,
            "estimated_output_tokens": response.estimated_output_tokens,
        }

    def validate_schema_and_evidence(self, state: QualityState) -> QualityState:
        hypotheses = state.get("hypotheses", [])
        evidence = state.get("evidence", [])
        trace = self._start(state, "validate_schema_and_evidence", len(hypotheses))
        known_ids = {item.evidence_id for item in evidence}
        unresolved = {
            evidence_id
            for hypothesis in hypotheses
            for evidence_id in hypothesis.supporting_evidence_ids + hypothesis.counter_evidence_ids
            if evidence_id not in known_ids
        }
        deterministic = [item.hypothesis_id for item in hypotheses if item.deterministic_conclusion]
        if unresolved or deterministic:
            trace.fail("validate_schema_and_evidence", "EVIDENCE_SCHEMA_VIOLATION")
            raise ValueError("Hypothesis output failed evidence validation")
        result_type: Literal["hypothesis_matrix", "clarification", "degraded"]
        if not hypotheses or state.get("warnings"):
            result_type = "degraded"
        else:
            result_type = "hypothesis_matrix"
        result = RunResult(
            result_type=result_type,
            summary=(
                "已形成三个待验证原因方向，最终根因与处置需由质量工程师确认。"
                if hypotheses
                else "可用证据不足，未生成原因假设。"
            ),
            facts=state.get("facts", []),
            evidence=evidence,
            hypotheses=hypotheses,
            required_clarifications=state["fixture"].expected.required_clarifications,
        )
        trace.complete("validate_schema_and_evidence", output_count=len(hypotheses))
        return {"result": result}

    def await_human(self, state: QualityState) -> QualityState:
        trace = self._start(state, "await_human", len(state.get("hypotheses", [])))
        trace.complete("await_human", output_count=1)
        return {}

    def supplement_or_finalize(self, state: QualityState) -> QualityState:
        trace = self._start(state, "supplement_or_finalize", 1)
        action = state["action"]
        result = state["result"].model_copy(deep=True)
        decision_map = {
            ActionName.CONFIRM: "人工确认分析方向，进入验证行动。",
            ActionName.REJECT: "人工退回分析方向，保留证据并结束本次运行。",
            ActionName.SUPPLEMENT: "已记录本次会话补充信息，需在后续验证行动中复核。",
            ActionName.RESUME: "从有效检查点恢复并完成本次离线运行。",
        }
        result.human_decision = decision_map[action]
        trace.complete("supplement_or_finalize", output_count=1)
        return {"result": result}

    def run_initial(
        self,
        *,
        fixture: QualityFixture,
        scenario: str,
        trace: TraceRecorder,
    ) -> QualityState:
        initial: QualityState = {
            "case_id": fixture.scenario_id,
            "scenario": scenario,
            "fixture": fixture,
            "trace": trace,
        }
        return cast(QualityState, self.graph.invoke(initial))

    def resume(
        self,
        *,
        state: QualityState,
        action: ActionName,
        supplement_present: bool,
    ) -> QualityState:
        resumed = dict(state)
        resumed["action"] = action
        resumed["supplement_present"] = supplement_present
        return cast(QualityState, self.resume_graph.invoke(cast(QualityState, resumed)))
