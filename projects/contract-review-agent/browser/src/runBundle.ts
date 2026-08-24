import type { ContractFixture, ContractRunReport, RunBundleV2 } from './types'

const FIXED_GENERATED_AT = '2026-08-20T00:00:00.000Z'

export function createRunBundle(fixture: ContractFixture, report: ContractRunReport): RunBundleV2 {
  const citedClauseIds = new Set(report.findings.flatMap(item => item.clause_ids))
  const citedRuleIds = new Set(report.findings.map(item => item.rule_id))
  const citations: RunBundleV2['citations'] = []
  for (const clause of fixture.contract.clauses.filter(item => citedClauseIds.has(item.clause_id))) {
    citations.push({ citation_id: clause.clause_id, public_summary: `第 ${clause.page} 页 · ${clause.heading} · 公开模拟条款`, source_type: 'public_reconstruction', fact_id: null, claim_id: null })
  }
  for (const reviewRule of fixture.rules.filter(item => citedRuleIds.has(item.rule_id))) {
    citations.push({ citation_id: reviewRule.rule_id, public_summary: `${reviewRule.rule_id} / ${reviewRule.version} · 公开重建规则`, source_type: 'public_reconstruction', fact_id: null, claim_id: null })
  }
  const results: RunBundleV2['results'] = report.findings.map(item => ({
    result_id: item.finding_id, result_type: 'finding', summary: item.rationale,
    citation_ids: [...item.clause_ids, item.rule_id], source_type: 'simulated_run_result', fact_id: null, claim_id: null,
  }))
  results.push({ result_id: 'HUMAN-GATE-001', result_type: 'human_gate', summary: '风险项需由法务和业务人员复核；自动审查不构成法律意见。', citation_ids: [], source_type: 'simulated_run_result', fact_id: null, claim_id: null })
  return {
    schema_version: 2, project_id: 'contract-review-agent', case_id: report.case_id,
    run_id: `contract-${report.case_id}-offline-v1`, trace_id: `trace-contract-${report.case_id}-v1`, status: 'awaiting_human',
    identity: { workflow_version: 'contract-workflow-v1', dataset_version: 'contract-fixtures-v1', rules_version: 'contract-rules-v1', prompt_or_policy_version: 'contract-policy-v1', runtime_version: 'contract-browser-v1', model_provider: 'mock', seed: 17 },
    nodes: report.trace.map(item => ({ ...item, source_type: 'simulated_run_result', fact_id: null, claim_id: null })), citations, results,
    claims: [{ statement: '本 Bundle 来自公开模拟合同与确定性离线运行，不代表历史生产结果。', source_type: 'public_reconstruction', fact_id: null, claim_id: null }],
    estimated_tokens: report.estimated_tokens, estimated_cost_usd: 0, warnings: report.warnings, generated_at: FIXED_GENERATED_AT,
  }
}

export function serializeRunBundle(bundle: RunBundleV2) {
  return `${JSON.stringify(bundle, null, 2)}\n`
}
