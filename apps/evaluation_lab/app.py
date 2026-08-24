"""AI Agent Evaluation Lab: datasets, traces, experiments, gates, and bad cases."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, cast

import httpx
import streamlit as st
import streamlit.components.v1 as components

from apps.evaluation_lab.lab_core import (
    BAD_CASES,
    ExperimentConfig,
    compare_versions,
    load_retrieval_dataset,
    load_versioned_project_report,
    local_bundle_import_enabled,
    parse_local_run_bundle,
    run_retrieval_experiment,
)
from packages.contracts.models import RunCreateRequest
from packages.model_gateway import GatewayConfig
from projects.quality_anomaly_agent.service import CASE_SCENARIOS, QualityAgentService

st.set_page_config(
    page_title="AI Agent Evaluation Lab",
    page_icon="◫",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      :root { --lab-ink:#13232b; --lab-blue:#2457e6; --lab-aqua:#0a8e91; --lab-amber:#c86a10; }
      .stApp { background: #eef3f5; color: var(--lab-ink); }
      [data-testid="stSidebar"] { background: #172a33; }
      [data-testid="stSidebar"] * { color: #eaf1f3 !important; }
      [data-testid="stHeader"] { background: transparent; }
      .block-container { max-width: 1500px; padding-top: 2.4rem; padding-bottom: 5rem; }
      h1, h2, h3 { letter-spacing: -.035em !important; }
      h1 { font-size: clamp(2.8rem, 6vw, 5.8rem) !important; line-height: .92 !important; }
      .lab-kicker { color: var(--lab-blue); font: 700 10px/1.2 monospace; letter-spacing:.14em; text-transform:uppercase; }
      .lab-intro { max-width: 760px; color:#5d6f77; font-size:15px; line-height:1.8; }
      .identity-strip { display:grid; grid-template-columns:repeat(4,1fr); border:1px solid #afbec4; margin:1.8rem 0; }
      .identity-strip div { padding:14px 16px; border-right:1px solid #cbd6da; background:#f9fbfb; }
      .identity-strip div:last-child { border-right:0; }
      .identity-strip small { display:block; color:#71828a; font:9px monospace; margin-bottom:5px; }
      .identity-strip strong { font-size:12px; }
      .source-badge { display:inline-block; padding:4px 7px; color:#174f52; background:#d9eeee; font:9px monospace; }
      .gate-pass, .gate-block { padding:18px 20px; border-left:5px solid var(--lab-aqua); background:#e5f3f1; }
      .gate-block { border-color:var(--lab-amber); background:#fff0dc; }
      .metric-note { color:#708189; font-size:10px; }
      div[data-testid="stMetric"] { padding:16px; border:1px solid #cbd6da; background:#f9fbfb; }
      div[data-baseweb="tab-list"] { gap:7px; }
      button[data-baseweb="tab"] { border:1px solid #cbd6da; background:#f9fbfb; padding:10px 16px; }
      button[data-baseweb="tab"][aria-selected="true"] { color:white !important; background:var(--lab-ink); }
      @media(max-width:800px){ .identity-strip{grid-template-columns:1fr 1fr;} }
    </style>
    """,
    unsafe_allow_html=True,
)


COMPONENT_PATH = Path(__file__).parent / "handoff_component"
handoff_fragment = components.declare_component("handoff_fragment", path=str(COMPONENT_PATH))


def redeem_handoff(fragment: dict[str, str]) -> dict[str, Any]:
    api_url = os.getenv("QUALITY_API_URL", "http://127.0.0.1:8000").rstrip("/")
    # This is a loopback handoff. Inheriting HTTP_PROXY can route localhost
    # traffic away from the local API and make a healthy service look offline.
    with httpx.Client(timeout=15, trust_env=False) as client:
        response = client.post(
            f"{api_url}/api/v1/evaluation-handoffs/{fragment['handoff_id']}/redeem",
            headers={"Authorization": f"Bearer {fragment['redeem_token']}"},
            json={"consumer": "evaluation-lab"},
        )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Handoff response is not an object")
    run_bundle = payload.get("run_bundle")
    if not isinstance(run_bundle, dict):
        raise ValueError("Handoff response is missing run_bundle")
    return cast(dict[str, Any], run_bundle)


def run_local_case(case_id: str) -> dict[str, Any]:
    service = QualityAgentService(GatewayConfig(provider="mock"))
    created = service.create_run(
        RunCreateRequest(
            case_id=case_id,
            scenario=CASE_SCENARIOS[case_id],  # type: ignore[arg-type]
            mode="offline",
            client_version="evaluation-lab-v1",
        )
    )
    record = service.authorize(created.run_id, created.session_token)
    return service.bundle(record).model_dump(mode="json")


fragment_value = handoff_fragment(key="handoff-fragment", default=None)
if fragment_value:
    fragment = cast(dict[str, str], fragment_value)
    handoff_id = fragment.get("handoff_id")
    if handoff_id and st.session_state.get("handoff_id") != handoff_id:
        # Claim the component event before the network call. Streamlit can rerun while a
        # component settles; pre-claiming prevents a one-time credential from being redeemed twice.
        st.session_state.handoff_id = handoff_id
        st.session_state.handoff_consumed = True
        try:
            st.session_state.run_bundle = redeem_handoff(fragment)
            st.session_state.handoff_status = "success"
        except httpx.HTTPStatusError as error:
            st.session_state.handoff_status = (
                "expired" if error.response.status_code in {401, 404, 410} else "unavailable"
            )
        except httpx.RequestError:
            st.session_state.handoff_status = "unavailable"
        except (KeyError, TypeError, ValueError):
            st.session_state.handoff_status = "invalid"

if st.session_state.get("handoff_status") == "success":
    st.success("已安全接收一次性 Run Bundle，地址栏凭证已清除。")
elif st.session_state.get("handoff_status") == "expired":
    st.warning("评测交接已过期或已兑换。请从质量 Agent 重新发起，或上传 Run Bundle。")
elif st.session_state.get("handoff_status") == "unavailable":
    st.warning("质量 Agent API 暂时不可达。请稍后重试，或从质量 Agent 导出 Run Bundle 后上传。")
elif st.session_state.get("handoff_status") == "invalid":
    st.warning("评测交接响应不完整。请重新发起，或上传 Run Bundle。")


with st.sidebar:
    st.markdown("### EVALUATION / LAB")
    st.caption("评测对象")
    project_options = ["质量异常分析 Agent", "合同审查 Agent", "企业智能问答助手"]
    query_project = st.query_params.get("project", "")
    query_project_labels = {
        "contract-review-agent": "合同审查 Agent",
        "enterprise-rag-assistant": "企业智能问答助手",
    }
    selected_label = query_project_labels.get(query_project, project_options[0])
    project = st.selectbox(
        "项目",
        project_options,
        index=project_options.index(selected_label),
        label_visibility="collapsed",
    )
    st.markdown("---")
    lab_mode = os.getenv("EVALUATION_LAB_MODE", "public")
    st.caption("评测模式")
    st.markdown("**LOCAL / OFFLINE / MOCK**" if lab_mode == "local" else "**PUBLIC / READ ONLY**")
    st.caption("公开环境不接收访客 Bundle；本地模式也不会持久化导入内容。")
    st.markdown("---")
    if local_bundle_import_enabled(lab_mode):
        uploaded = st.file_uploader("导入 Run Bundle", type=["json"])
        if uploaded is not None:
            try:
                st.session_state.run_bundle = parse_local_run_bundle(json.load(uploaded))
                st.success("Bundle 已校验并载入当前会话")
            except (json.JSONDecodeError, UnicodeDecodeError):
                st.error("文件不是有效 JSON")
            except ValueError as error:
                st.error(f"Bundle 校验失败：{error}")
    else:
        st.caption("Run Bundle 导入仅在 EVALUATION_LAB_MODE=local 时启用。")


st.markdown('<p class="lab-kicker">Dataset → Trace → Experiment → Gate</p>', unsafe_allow_html=True)
st.title("AI Agent\nEvaluation Lab")
st.markdown(
    '<p class="lab-intro">这里不展示一个孤立分数。每次评测都绑定数据集、配置、工作流和指标版本，并把失败归因转成下一轮回归案例。</p>',
    unsafe_allow_html=True,
)
project_ids = {
    "合同审查 Agent": "contract-review-agent",
    "企业智能问答助手": "enterprise-rag-assistant",
}
versioned_report = (
    load_versioned_project_report(project_ids[project]) if project in project_ids else None
)
identity = (
    {
        "dataset": versioned_report["dataset_version"],
        "workflow": versioned_report["workflow_version"],
        "metrics": versioned_report["metric_definition_version"],
        "source": versioned_report["source_label"],
    }
    if versioned_report
    else {
        "dataset": "quality-retrieval-v1",
        "workflow": "quality-workflow-v1",
        "metrics": "quality-v1",
        "source": "模拟数据运行结果",
    }
)
st.markdown(
    f"""
    <div class="identity-strip">
      <div><small>DATASET</small><strong>{identity['dataset']}</strong></div>
      <div><small>WORKFLOW</small><strong>{identity['workflow']}</strong></div>
      <div><small>METRICS</small><strong>{identity['metrics']}</strong></div>
      <div><small>SOURCE</small><strong>{identity['source']}</strong></div>
    </div>
    """,
    unsafe_allow_html=True,
)

if versioned_report:
    st.info("在线 Lab 展示仓库中的版本化评测产物；使用 README 命令可在本地重新运行全部案例。")
    metric_items = list(versioned_report["metrics"].items())
    metric_columns = st.columns(min(len(metric_items), 4))
    for index, (name, value) in enumerate(metric_items):
        display = f"{value:.0%}" if isinstance(value, float) else value
        metric_columns[index % len(metric_columns)].metric(name, display)
    st.markdown("#### 评测案例")
    st.dataframe(versioned_report["cases"], width="stretch", hide_index=True)
    if versioned_report["release_passed"]:
        st.markdown(
            '<div class="gate-pass"><strong>PASS · 版本化评测门禁通过</strong></div>',
            unsafe_allow_html=True,
        )
    st.download_button(
        "下载版本化评测报告",
        json.dumps(versioned_report, ensure_ascii=False, indent=2),
        file_name=f"{versioned_report['project_id']}-evaluation.json",
        mime="application/json",
    )
    st.stop()

dataset = load_retrieval_dataset()
tabs = st.tabs(["评测集", "单次运行", "参数实验", "指标", "版本门禁", "Bad Case"])

with tabs[0]:
    st.subheader("评测集管理")
    left, right = st.columns([1.2, 0.8])
    with left:
        st.markdown('<span class="source-badge">公开模拟数据</span>', unsafe_allow_html=True)
        st.write(dataset.query)
        st.dataframe(
            [
                {
                    "document_id": item.document_id,
                    "source": item.source,
                    "version": item.version,
                    "relevant": item.document_id in dataset.relevant_document_ids,
                    "title": item.title,
                }
                for item in dataset.documents
            ],
            width="stretch",
            hide_index=True,
        )
    with right:
        st.metric("语料条目", len(dataset.documents))
        st.metric("数据集版本", "V1")
        st.caption("相关性标签只用于公开模拟评测，不代表历史生产标注。")

with tabs[1]:
    st.subheader("单次 Run / Trace 检查")
    case_labels = {
        "incoming_material_001": "来料检漏超限 · 标准路径",
        "no_evidence": "信息不足 · 拒答路径",
        "tool_timeout": "ERP 超时 · 降级路径",
    }
    case_id = st.selectbox(
        "选择运行案例",
        list(case_labels),
        format_func=lambda item: case_labels[item],
    )
    if st.button("运行离线评测", type="primary"):
        with st.spinner("执行 Tool、检索、Schema 与 Trace…"):
            st.session_state.run_bundle = run_local_case(case_id)
    bundle = st.session_state.get("run_bundle")
    if bundle:
        is_v2_bundle = bundle.get("schema_version") == 2
        evidence_items = bundle.get("citations", []) if is_v2_bundle else bundle["evidence"]
        result_items = bundle.get("results", []) if is_v2_bundle else bundle["hypotheses"]
        summary_cols = st.columns(4)
        summary_cols[0].metric("状态", bundle["status"])
        summary_cols[1].metric("证据", len(evidence_items))
        summary_cols[2].metric("结果", len(result_items))
        summary_cols[3].metric("估算 Token", bundle["estimated_tokens"])
        st.markdown("#### 节点 Trace")
        st.dataframe(bundle["nodes"], width="stretch", hide_index=True)
        with st.expander("查看引用与结果结构"):
            st.json({"evidence": evidence_items, "results": result_items})
    else:
        st.info("从质量 Agent 进入、导入 Bundle，或运行一个离线案例。")

with tabs[2]:
    st.subheader("检索参数实验")
    controls, output = st.columns([0.36, 0.64])
    with controls:
        top_k = st.slider("Top-K", 1, 6, 5)
        score_threshold = st.slider("最低词法分数", 0.0, 10.0, 0.0, 0.1)
        rerank = st.toggle("相关性重排", value=False)
        st.selectbox("Prompt 版本", ["quality-hypothesis-v1"])
        st.selectbox("模型配置", ["mock / fixed-seed-42"])
    current_result = run_retrieval_experiment(
        ExperimentConfig(top_k=top_k, score_threshold=score_threshold, rerank=rerank)
    )
    st.session_state.current_experiment = current_result.model_dump(mode="json")
    with output:
        metric_cols = st.columns(4)
        metric_cols[0].metric(f"Hit@{top_k}", f"{current_result.hit_at_k:.0%}")
        metric_cols[1].metric(f"Recall@{top_k}", f"{current_result.recall_at_k:.0%}")
        metric_cols[2].metric("MRR", f"{current_result.reciprocal_rank:.3f}")
        metric_cols[3].metric("估算 Token", current_result.estimated_tokens)
        st.markdown("#### 返回顺序")
        for rank, document_id in enumerate(current_result.retrieved_ids, start=1):
            relevant = document_id in current_result.relevant_retrieved_ids
            st.write(f"`{rank:02d}`  {document_id}  {'✓ 相关' if relevant else '· 非相关'}")
        st.caption("指标来源：模拟数据运行结果；相似度只用于检索排序，不等于根因概率。")

with tabs[3]:
    st.subheader("项目特定指标")
    metric_bundle = st.session_state.get("run_bundle")
    if metric_bundle and metric_bundle.get("schema_version") == 1:
        metrics = metric_bundle["metrics"]
        cols = st.columns(5)
        cols[0].metric("Schema 合规", f"{metrics['schema_compliance']:.0%}")
        cols[1].metric("引用可解析", f"{metrics['evidence_resolvability']:.0%}")
        cols[2].metric("无依据结论", f"{metrics['unsupported_conclusion_rate']:.0%}")
        cols[3].metric("反证覆盖", f"{metrics['counter_evidence_coverage']:.0%}")
        cols[4].metric("人工边界", f"{metrics['human_boundary_accuracy']:.0%}")
        st.caption(f"指标版本：{metrics['metric_definition_version']} · 分母：当前 Run 中可评价对象")
    elif metric_bundle:
        st.info("Run Bundle v2 不携带通用质量指标；请查看对应项目的版本化评测报告。")
    else:
        st.info("先在“单次运行”中执行案例，或导入 Run Bundle。")
    st.markdown("#### 门槛解释")
    st.table(
        [
            {"指标": "Schema 合规率", "门槛": "100%", "业务含义": "每个输出都可被下游消费"},
            {"指标": "引用可解析率", "门槛": "100%", "业务含义": "每个假设引用都能回到证据"},
            {"指标": "无依据确定性结论率", "门槛": "0%", "业务含义": "Agent 不越权认定根因"},
            {"指标": "人工边界准确率", "门槛": "100%", "业务含义": "处置决策必须交给质量角色"},
        ]
    )

with tabs[4]:
    st.subheader("版本对比与发布门禁")
    baseline = run_retrieval_experiment(ExperimentConfig(top_k=3, score_threshold=0, rerank=False))
    candidate_data = st.session_state.get("current_experiment")
    candidate = (
        run_retrieval_experiment(ExperimentConfig.model_validate(candidate_data["config"]))
        if candidate_data
        else run_retrieval_experiment(ExperimentConfig(top_k=5, score_threshold=0, rerank=False))
    )
    comparison = compare_versions(baseline, candidate)
    compare_cols = st.columns(4)
    compare_cols[0].metric("Baseline Recall", f"{baseline.recall_at_k:.0%}")
    compare_cols[1].metric("Candidate Recall", f"{candidate.recall_at_k:.0%}", f"{comparison.recall_delta:+.0%}")
    compare_cols[2].metric("Baseline MRR", f"{baseline.reciprocal_rank:.3f}")
    compare_cols[3].metric("Candidate MRR", f"{candidate.reciprocal_rank:.3f}", f"{comparison.mrr_delta:+.3f}")
    if comparison.release_passed:
        st.markdown('<div class="gate-pass"><strong>PASS · 可以进入下一发布阶段</strong><br><small>数据集身份一致，核心检索指标未低于基线。</small></div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="gate-block"><strong>BLOCK · 发布已阻止</strong><br><small>{", ".join(comparison.gate_reasons)}</small></div>',
            unsafe_allow_html=True,
        )
    st.download_button(
        "导出版本对比 JSON",
        comparison.model_dump_json(indent=2),
        file_name="quality-version-comparison.json",
        mime="application/json",
    )

with tabs[5]:
    st.subheader("Bad Case 归因工作台")
    bad_case_id = st.selectbox("回归案例", list(BAD_CASES))
    bad_case = BAD_CASES[bad_case_id]
    bad_cols = st.columns([0.25, 0.75])
    with bad_cols[0]:
        st.metric("归因层", bad_case["category"].upper())
        st.caption("data → tool → retrieval → rule → prompt → model → workflow → human_feedback")
    with bad_cols[1]:
        st.markdown(f"**失败表现**  \n{bad_case['symptom']}")
        st.markdown(f"**期望行为**  \n{bad_case['expected']}")
        st.code(bad_case["regression_assertion"], language="python")
    regression_payload = {
        "schema_version": 1,
        "case_id": bad_case_id,
        "root_category": bad_case["category"],
        "expected_behavior": bad_case["expected"],
        "assertion": bad_case["regression_assertion"],
        "source_label": "公开模拟数据",
    }
    st.download_button(
        "生成回归案例 JSON",
        json.dumps(regression_payload, ensure_ascii=False, indent=2),
        file_name=f"{bad_case_id}-regression.json",
        mime="application/json",
    )

st.markdown("---")
st.caption("AI Agent Evaluation Lab · 当前会话内编辑 · 不持久化 · 模拟数据运行结果")
