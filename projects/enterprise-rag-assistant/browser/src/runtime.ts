import { ENTERPRISE_ASSETS, getQueryCase } from './fixtures'
import type { AnswerDraft, EnterpriseData, EnterpriseRunReport, IntentMatch, PermissionScope, QueryCase, ResultType, Route, SourceType, TraceNode, UserRole } from './types'

const NODE_NAMES = ['normalize_query', 'terminology_rewrite', 'classify_intent', 'route_knowledge_or_realtime_data', 'retrieve_and_rerank_or_call_business_tool', 'generate_structured_answer', 'citation_and_permission_check', 'answer_or_refuse'] as const
const NODE_DURATIONS = [4, 5, 8, 3, 18, 12, 5, 2]
const CONSTRAINTS = ['华东', '两周内', 'ISO', '交期', '当前']

export function normalizeQuery(query: string, data = ENTERPRISE_ASSETS.data) {
  let normalized = query.normalize('NFKC').trim().replaceAll('，', '、').replaceAll(',', '、').replaceAll('。', '').replace(/\s+/g, ' ')
  for (const entry of data.knowledge_data.terminology) for (const alias of entry.aliases) if (normalized.includes(alias) && !normalized.includes(entry.canonical)) normalized = normalized.replaceAll(alias, `${alias}（${entry.canonical}）`)
  return normalized
}

export function classifyIntent(query: string): IntentMatch {
  const comparableQuery = query.trim().toLocaleLowerCase()
  const reorderedComposite = !query.includes('并告诉我当前') && ['能做', '供应商能力', '精密清洗'].some(item => query.includes(item)) && ['当前询价', '已报价', '报价'].some(item => query.includes(item))
  if (reorderedComposite) return { level_1: 'composite_analysis', level_2: 'knowledge_and_realtime', confidence: 0.99, alternatives: ['supplier_capability', 'quotation_status'] }
  const scores = ENTERPRISE_ASSETS.taxonomy.definitions.map((definition, index) => {
    let score = definition.keywords.reduce((total, keyword) => total + (comparableQuery.includes(keyword.toLocaleLowerCase()) ? 3 : 0), 0)
    if (definition.level_2 === 'knowledge_and_realtime' && score) score += 10
    if (definition.example.toLocaleLowerCase() === comparableQuery) score += 20
    return { score, index, definition }
  }).sort((a, b) => b.score - a.score || a.index - b.index)
  const best = scores[0]
  if (best.score === 0) return { level_1: 'composite_analysis', level_2: 'supplier_comparison', confidence: 0.35, alternatives: ['clarify'] }
  return { level_1: best.definition.level_1, level_2: best.definition.level_2, confidence: Math.min(0.55 + best.score * 0.04, 0.99), alternatives: scores.slice(1, 3).filter(item => item.score > 0).map(item => item.definition.level_2) }
}

function routeQuery(query: string, scope: PermissionScope, intent: IntentMatch): Route {
  if (scope === 'public' && ['受限', '合同价格', '报价明细'].some(item => query.includes(item))) return 'permission_stop'
  if (intent.level_2 === 'supplier_comparison' && !['产品', '工艺', '区域', '资质', '数量', '交期'].some(item => query.includes(item))) return 'clarify'
  if (query.includes('未收录') || query.includes('无可靠证据')) return 'refuse'
  if (intent.level_2 === 'process_parameter' && query.includes('有效')) return 'version_check'
  if (['inquiry_status', 'quotation_status', 'order_status', 'logistics_status'].includes(intent.level_2)) return 'tool'
  if (intent.level_2 === 'knowledge_and_realtime') return 'rag_and_tool'
  return 'rag'
}

function citation(id: string, source_type: 'knowledge' | 'tool', title: string, version: string) { return { citation_id: id, source_type, title, version_or_freshness: version } }
function knowledgeAnswer(intent: IntentMatch, data: EnterpriseData): AnswerDraft {
  const docs = new Map(data.knowledge_data.documents.map(item => [item.document_id, item]))
  if (intent.level_2 === 'alias_resolution') { const item = docs.get('CIT-DEMO-TERM-01')!; return { facts: [item.text], table: [], citations: [citation(item.document_id, 'knowledge', item.title, item.version)], limitations: ['答案仅基于当前有效且有权限的公开模拟知识。'] } }
  if (intent.level_2 === 'process_flow') { const ids = ['CIT-DEMO-PROCESS-01', 'CIT-DEMO-PROCESS-CURRENT']; const selected = ids.map(id => docs.get(id)!); return { facts: selected.map(item => item.text), table: [], citations: selected.map(item => citation(item.document_id, 'knowledge', item.title, item.version)), limitations: ['答案仅基于当前有效且有权限的公开模拟知识。'] } }
  if (['supply_relationship', 'supplier_qualification'].includes(intent.level_2)) {
    const profile = docs.get('CIT-DEMO-SUPPLIER-QUAL-01')!; const relation = data.knowledge_data.relationships[0]
    return { facts: [profile.text, `${relation.supplier_id} 提供 ${relation.capability}，适用 ${relation.item_category}，有效期 ${relation.valid_from} 至 ${relation.valid_to}`], table: [], citations: [citation(profile.document_id, 'knowledge', profile.title, profile.version), citation(relation.evidence_id, 'knowledge', '供应关系证据', 'V1')], limitations: ['答案仅基于当前有效且有权限的公开模拟知识。'] }
  }
  const capable = data.knowledge_data.suppliers.filter(item => item.capabilities.includes('precision_cleaning'))
  if (intent.level_2 === 'supplier_capability' && capable.length) return { facts: [`公开证据中有 ${capable.length} 家供应商具备精密清洗能力。`], table: capable.map(item => ({ supplier_id: item.supplier_id, region: item.region })), citations: data.knowledge_data.relationships.map(item => citation(item.evidence_id, 'knowledge', '供应关系证据', 'V1')), limitations: ['能力记录不等于当前产能承诺，交期需另行确认。'] }
  return { facts: [], table: [], citations: [], limitations: ['当前公开语料没有足够证据，需要补充问题或转人工查询。'] }
}

function answerFor(route: Route, intent: IntentMatch, data: EnterpriseData): { resultType: ResultType; answer: AnswerDraft; warnings: string[] } {
  if (route === 'permission_stop') return { resultType: 'permission_denied', answer: { facts: [], table: [], citations: [], limitations: ['当前角色无权查看受限合同价格或报价明细，且不披露数据是否存在。'] }, warnings: ['PERMISSION_BLOCKED'] }
  if (route === 'clarify') return { resultType: 'clarification', answer: { facts: ['请补充产品或工艺、区域、资质、数量和交期约束。'], table: [], citations: [], limitations: ['关键约束不足，系统未执行供应商推荐。'] }, warnings: ['CLARIFICATION_REQUIRED'] }
  if (route === 'refuse') return { resultType: 'refusal', answer: { facts: [], table: [], citations: [], limitations: ['知识库中没有该企业私有产能的可靠证据，无法回答。'] }, warnings: ['NO_EVIDENCE_REFUSAL'] }
  if (route === 'version_check') return { resultType: 'clarification', answer: { facts: ['检索到两个版本的工艺温度窗口；V1 已失效，V2 为当前版本。'], table: [], citations: [citation('CIT-DEMO-PROCESS-CURRENT', 'knowledge', '当前工艺温度窗口', 'V2')], limitations: ['仍需工艺工程师确认 V2 是否适用于当前产品。'] }, warnings: ['SOURCE_VERSION_CONFLICT'] }
  if (route === 'rag_and_tool') {
    const eligible = data.knowledge_data.relationships.filter(item => item.capability === 'precision_cleaning'); const submitted = data.realtime_data.quotations.filter(item => item.status === 'submitted')
    return { resultType: 'table', answer: { facts: [`具备精密清洗有效供应证据的供应商有 ${eligible.length} 家。`, `当前询价已有 ${submitted.length} 家提交报价。`], table: eligible.map(item => ({ supplier_id: item.supplier_id, capability: item.capability })), citations: [...eligible.map(item => citation(item.evidence_id, 'knowledge', '供应关系证据', 'V1')), citation('TOOL-QUOTATION-DEMO-001', 'tool', '报价 Tool', data.realtime_data.inquiry.updated_at)], limitations: ['供应能力来自知识证据；当前报价数来自实时 Tool，两者不可互相替代。'] }, warnings: [] }
  }
  if (route === 'tool') {
    if (intent.level_2 === 'order_status') { const order = data.realtime_data.orders[0]; return { resultType: 'answer', answer: { facts: [`订单 ${order.order_id} 当前状态为${order.status}。`], table: [], citations: [citation('TOOL-ORDER-DEMO-001', 'tool', '订单 Tool', order.updated_at)], limitations: ['实时状态只由授权 Tool 返回，不使用知识库猜测。'] }, warnings: [] } }
    const submitted = data.realtime_data.quotations.filter(item => item.status === 'submitted')
    return { resultType: 'answer', answer: { facts: [`当前询价已有 ${submitted.length} 家提交报价。`], table: [], citations: [citation('TOOL-QUOTATION-DEMO-001', 'tool', '报价 Tool', data.realtime_data.inquiry.updated_at)], limitations: ['这是公开模拟 Tool 结果，不代表生产交易状态。'] }, warnings: [] }
  }
  const answer = knowledgeAnswer(intent, data)
  if (!answer.facts.length) return { resultType: 'refusal', answer, warnings: ['NO_EVIDENCE_REFUSAL'] }
  return { resultType: answer.table.length ? 'table' : 'answer', answer, warnings: [] }
}

function traceFor(route: Route, answer: AnswerDraft, warnings: string[]): TraceNode[] {
  const outputs = [1, 1, 1, 1, answer.citations.length, answer.facts.length, answer.citations.length, 1]
  return NODE_NAMES.map((node, index) => ({ sequence: index + 1, node, status: 'completed', duration_ms: NODE_DURATIONS[index], input_count: index === 5 || index === 6 ? answer.citations.length : 1, output_count: outputs[index], warning_codes: index === 4 ? warnings : [], source_type: index === 4 && (route === 'tool' || route === 'rag_and_tool') ? 'simulated_extension' : 'public_reconstruction' as SourceType }))
}

export function runEnterpriseQuery(input: { caseId?: string; query?: string; userRole?: UserRole; permissionScope?: PermissionScope }): EnterpriseRunReport {
  const known = input.caseId ? getQueryCase(input.caseId) : undefined
  const query = known?.query ?? input.query ?? ''
  if ([...query].length > 500) throw new Error('invalid_custom_query:length')
  if (!query.trim()) throw new Error('invalid_custom_query:empty')
  const normalized = normalizeQuery(query); const intent = classifyIntent(query); const scope = known?.permission_scope ?? input.permissionScope ?? 'internal'; const route = routeQuery(query, scope, intent); const { resultType, answer, warnings } = answerFor(route, intent, ENTERPRISE_ASSETS.data)
  const constraints = CONSTRAINTS.filter(item => query.includes(item)); const subqueries = route === 'rag_and_tool' ? ['查找具备精密清洗有效证据的供应商', '查询当前询价已报价数量'] : [normalized]
  return { schema_version: 1, project_id: 'enterprise-rag-assistant', case_id: known?.case_id ?? 'custom_query', is_custom_query: !known, original_query: query, normalized_query: normalized, rewritten_query: normalized, protected_constraints: constraints, subqueries, intent, route, result_type: resultType, answer, model_provider: 'mock', trace: traceFor(route, answer, warnings), estimated_tokens: answer.facts.join('').length + answer.citations.length * 32, warnings, source_label: '模拟数据运行结果' }
}

export function normalizeForParity(report: EnterpriseRunReport) { return { case_id: report.case_id, normalized_query: report.normalized_query, protected_constraints: report.protected_constraints, intent: report.intent, route: report.route, result_type: report.result_type, facts: report.answer.facts, citations: report.answer.citations.map(item => ({ citation_id: item.citation_id, source_type: item.source_type })), warnings: report.warnings, trace_nodes: report.trace.map(item => item.node) } }
