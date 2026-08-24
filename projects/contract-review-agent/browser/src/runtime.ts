import type { Clause, ContractFixture, ContractRunReport, RiskFinding, ReviewRule, Severity, TraceNode } from './types'

const SEVERITY_ORDER: Record<Severity, number> = { critical: 0, high: 1, medium: 2, low: 3 }
const POLICY_BY_RULE: Record<string, string> = {
  'RULE-PROC-012': 'POL-PROC-V3', 'RULE-PROC-021': 'POL-PROC-V3',
  'RULE-SALES-031': 'POL-SALES-V2', 'RULE-SALES-099': 'POL-SALES-V2',
  'RULE-NDA-011': 'POL-NDA-V4', 'RULE-TECH-021': 'POL-TECH-V2',
}

const NODE_DURATIONS = [18, 7, 12, 15, 14, 32, 13, 9, 4, 3]
const NODE_NAMES = ['ingest_document', 'classify_contract', 'structural_clause_split', 'deterministic_rules', 'retrieve_policy_and_precedent', 'semantic_risk_review', 'cross_clause_consistency', 'evidence_validation', 'risk_ranking', 'mandatory_human_review'] as const

function has(text: string, terms: string[]) { return terms.every(term => text.includes(term)) }
function findClause(fixture: ContractFixture, heading: string) { return fixture.contract.clauses.find(item => item.heading.includes(heading)) }
function rule(fixture: ContractFixture, id: string): ReviewRule | undefined { return fixture.rules.find(item => item.rule_id === id) }
function excerpt(clauses: Clause[]) { return clauses.map(item => item.text).join(' / ') }

function finding(fixture: ContractFixture, id: string, ruleId: string, source: RiskFinding['source'], clauses: Array<Clause | undefined>, rationale: string, suggestion: string, missing: string[]): RiskFinding | null {
  const reviewRule = rule(fixture, ruleId)
  const completeClauses = clauses.filter((item): item is Clause => Boolean(item))
  if (!reviewRule || completeClauses.length !== clauses.length) return null
  return {
    finding_id: id, severity: reviewRule.severity, source, clause_ids: completeClauses.map(item => item.clause_id),
    original_excerpt: excerpt(completeClauses), rule_id: ruleId, rule_version: reviewRule.version,
    policy_document_id: POLICY_BY_RULE[ruleId], rationale, suggestion, missing_information: missing,
    human_required: true, human_status: 'pending_legal_review',
  }
}

function evaluateRules(fixture: ContractFixture): RiskFinding[] {
  const findings: Array<RiskFinding | null> = []
  if (fixture.contract.contract_type === 'procurement') {
    const payment = findClause(fixture, '付款')
    const acceptance = findClause(fixture, '验收')
    const objection = findClause(fixture, '质量异议')
    const warranty = findClause(fixture, '质量保证')
    const earlyPayment = Boolean(payment && acceptance && /(签收|到货).*(百分之九十|90%)/.test(payment.text) && /(检验周期|十个工作日)/.test(acceptance.text))
    if (earlyPayment) findings.push(finding(fixture, 'RF-DEMO-001', 'RULE-PROC-012', 'rule_and_cross_clause', [payment, acceptance], '付款可能在来料检验完成前发生，形成先付款后验收的风险。', '将大额付款节点调整到来料验收通过后，例外情况进入专项审批。', ['专项审批阈值与授权人']))
    const shortObjection = Boolean(objection && acceptance && /(七个自然日|7个自然日)/.test(objection.text) && /(十个工作日|10个工作日)/.test(acceptance.text))
    if (shortObjection) findings.push(finding(fixture, 'RF-DEMO-002', 'RULE-PROC-021', 'rule_and_cross_clause', [objection, acceptance, warranty], '质量异议期短于检验周期，可能在检验完成前被视为验收合格。', '将质量异议期延长至检验周期结束后，并保留隐蔽缺陷追索。', ['自然日与工作日的统一换算口径']))
  }
  if (fixture.contract.contract_type === 'sales') {
    const fat = findClause(fixture, '出厂验收')
    const sat = findClause(fixture, '现场验收')
    const warranty = findClause(fixture, '质量保证')
    if (fat && sat && warranty && has(warranty.text, ['发货日', 'SAT'])) findings.push(finding(fixture, 'RF-SALES-001', 'RULE-SALES-031', 'rule_and_cross_clause', [fat, sat, warranty], '同一设备的质保起点同时指向发货日和 SAT 通过日，责任窗口不可确定。', '统一以 SAT 通过日为质保起点，并设置客户原因导致 SAT 延迟的最长兜底期限。', ['客户原因导致 SAT 延迟时的兜底日期']))
    const cap = findClause(fixture, '责任上限')
    const appendix = findClause(fixture, '附件 A')
    if (cap && appendix && has(cap.text, ['责任', '附件 A']) && has(appendix.text, ['不受', '责任上限'])) findings.push(finding(fixture, 'RF-CONTEXT-LOSS-001', 'RULE-SALES-099', 'rule_and_cross_clause', [cap, appendix], '正文与附件对责任上限存在冲突，单条款检索可能遗漏附件例外。', '补充正文与附件的双向交叉引用，并由法务确认赔偿例外的优先级。', ['正文与附件的适用顺序']))
  }
  if (fixture.contract.contract_type === 'nda') {
    const scope = findClause(fixture, '保密信息')
    const disclosure = findClause(fixture, '允许披露')
    if (scope && disclosure && (has(scope.text, ['未列明', '软件代码']) || has(disclosure.text, ['未约定', '保密义务']))) findings.push(finding(fixture, 'RF-NDA-001', 'RULE-NDA-011', 'llm', [scope, disclosure], '保密信息仅列明图纸和 BOM，未覆盖软件代码、客户数据，允许披露对象也不完整。', '补充受保护信息类型，并限定向顾问和关联方披露的必要性、保密义务与责任。', ['允许披露对象的完整清单']))
  }
  if (fixture.contract.contract_type === 'technical_cooperation') {
    const background = findClause(fixture, '背景知识产权')
    const foreground = findClause(fixture, '新生成果')
    const acceptance = findClause(fixture, '项目验收')
    if (foreground && /(验收后|后续).*(协商|另行)/.test(foreground.text)) findings.push(finding(fixture, 'RF-TECH-001', 'RULE-TECH-021', 'llm', [background, foreground, acceptance], '协议定义了背景知识产权，但将新生成果留待后续协商，验收后仍可能无法使用成果。', '签署前明确新生成果的归属、许可范围、申请权与验收失败后的处置。', ['新成果权属与部署许可范围']))
  }
  return findings.filter((item): item is RiskFinding => Boolean(item)).sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity] || a.finding_id.localeCompare(b.finding_id))
}

function makeTrace(fixture: ContractFixture, findings: RiskFinding[]): TraceNode[] {
  const ruleFindings = findings.filter(item => item.source === 'rule' || item.source === 'rule_and_cross_clause').length
  const semanticFindings = findings.filter(item => item.source === 'llm' || item.source === 'rag').length
  const outputs = [fixture.contract.clauses.length, 1, fixture.contract.clauses.length, ruleFindings, Math.min(4, fixture.rules.length + 1), semanticFindings, findings.filter(item => item.source === 'rule_and_cross_clause').length, findings.length, findings.length, findings.filter(item => item.human_required).length]
  const inputs = [1, fixture.contract.clauses.length, 1, fixture.rules.length, fixture.contract.clauses.length, Math.min(4, fixture.rules.length + 1), fixture.contract.clauses.length, findings.length, findings.length, findings.length]
  return NODE_NAMES.map((node, index) => ({ sequence: index + 1, node, status: 'completed', duration_ms: NODE_DURATIONS[index], input_count: inputs[index], output_count: outputs[index], warning_codes: [] }))
}

export function runContractReview(fixture: ContractFixture): ContractRunReport {
  const findings = evaluateRules(fixture)
  return {
    schema_version: 1, project_id: 'contract-review-agent', case_id: fixture.scenario_id,
    contract_id: fixture.contract.contract_id, contract_type: fixture.contract.contract_type,
    status: 'awaiting_human', model_provider: 'mock', findings,
    covered_clause_ids: [...new Set(findings.flatMap(item => item.clause_ids))].sort(),
    unreviewed_areas: ['附件与签章真实性需由法务和业务人员确认'], trace: makeTrace(fixture, findings),
    estimated_tokens: findings.length * 180, warnings: findings.length === 0 ? ['NO_AUTOMATED_RISK_IS_NOT_LEGAL_APPROVAL'] : [],
    source_label: '模拟数据运行结果',
  }
}

export function normalizeForParity(report: ContractRunReport) {
  return {
    case_id: report.case_id, contract_type: report.contract_type,
    findings: report.findings.map(item => ({ finding_id: item.finding_id, severity: item.severity, source: item.source, clause_ids: item.clause_ids, rule_id: item.rule_id, rule_version: item.rule_version, policy_document_id: item.policy_document_id, human_required: item.human_required })),
    covered_clause_ids: report.covered_clause_ids,
    trace_nodes: report.trace.map(item => item.node),
  }
}
