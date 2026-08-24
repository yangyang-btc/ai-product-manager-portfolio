import type { EnterpriseRunReport, RunBundleV2, SourceType } from './types'

export function createRunBundle(report: EnterpriseRunReport): RunBundleV2 {
  const citations = report.answer.citations.map(item => ({
    citation_id: item.citation_id,
    public_summary: `${item.title} · ${item.version_or_freshness}`,
    source_type: (item.source_type === 'tool' ? 'simulated_extension' : 'public_reconstruction') as SourceType,
    fact_id: null,
    claim_id: null,
  }))
  const citationIds = citations.map(item => item.citation_id)
  const resultKind = report.result_type === 'refusal' || report.result_type === 'permission_denied' ? 'refusal' : report.result_type === 'clarification' ? 'clarification' : 'answer'
  const summaries = report.answer.facts.length ? report.answer.facts : report.answer.limitations
  return {
    schema_version: 2, project_id: 'enterprise-rag-assistant', case_id: report.case_id,
    run_id: `rag-${report.case_id}-offline-v1`, trace_id: `trace-rag-${report.case_id}-v1`, status: 'completed',
    identity: { workflow_version: 'enterprise-rag-workflow-v1', dataset_version: 'enterprise-query-cases-v1', rules_version: 'enterprise-routing-v1', prompt_or_policy_version: 'enterprise-answer-policy-v1', runtime_version: 'rag-browser-v1', model_provider: 'mock', seed: 23 },
    nodes: report.trace.map(({ source_type, ...node }) => ({ ...node, source_type, fact_id: null, claim_id: null })),
    citations,
    results: summaries.map((summary, index) => ({ result_id: `RESULT-${String(index + 1).padStart(3, '0')}`, result_type: resultKind, summary, citation_ids: citationIds, source_type: report.route === 'tool' ? 'simulated_extension' : 'simulated_run_result', fact_id: null, claim_id: null })),
    claims: [{ statement: '知识检索链路为公开重建；询价、报价与订单 Tool 为公开模拟扩展。', source_type: 'public_reconstruction', fact_id: null, claim_id: null }],
    estimated_tokens: report.estimated_tokens, estimated_cost_usd: 0, warnings: report.warnings,
    generated_at: '2026-08-20T00:00:00.000Z',
  }
}

export function serializeRunBundle(bundle: RunBundleV2) { return `${JSON.stringify(bundle, null, 2)}\n` }
