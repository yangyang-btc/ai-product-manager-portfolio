export type PermissionScope = 'public' | 'internal' | 'restricted'
export type UserRole = 'bd' | 'operations' | 'new_employee'
export type Route = 'rag' | 'tool' | 'rag_and_tool' | 'clarify' | 'refuse' | 'permission_stop' | 'version_check'
export type ResultType = 'answer' | 'table' | 'clarification' | 'refusal' | 'permission_denied'
export type SourceType = 'public_reconstruction' | 'simulated_run_result' | 'simulated_extension'

export interface QueryCase {
  case_id: string; query: string; user_role: UserRole; permission_scope: PermissionScope
  expected_l1: string; expected_l2: string; expected_route: Route
}
export interface QueryCaseCollection { schema_version: 1; project_id: 'enterprise-rag-assistant'; dataset_version: 'enterprise-query-cases-v1'; synthetic: true; source_label: '公开模拟数据'; cases: QueryCase[] }
export interface IntentDefinition { level_1: string; level_2: string; keywords: string[]; example: string }
export interface IntentTaxonomy { schema_version: 1; project_id: 'enterprise-rag-assistant'; taxonomy_version: 'enterprise-intent-taxonomy-v1'; synthetic: true; source_label: '公开模拟数据'; definitions: IntentDefinition[] }
export interface TerminologyEntry { canonical: string; aliases: string[]; confused_with: string[] }
export interface Supplier { supplier_id: string; region: string; capabilities: string[]; certifications: string[] }
export interface Relationship { relationship_id: string; supplier_id: string; item_category: string; capability: string; valid_from: string; valid_to: string; evidence_id: string }
export interface KnowledgeDocument { document_id: string; version: string; source: string; title: string; text: string }
export interface EnterpriseData {
  schema_version: 1; project_id: 'enterprise-rag-assistant'; dataset_version: 'enterprise-business-data-v1'; synthetic: true; source_label: '公开模拟数据'; clock: string
  knowledge_data: { source_type: 'public_reconstruction'; terminology: TerminologyEntry[]; suppliers: Supplier[]; relationships: Relationship[]; documents: KnowledgeDocument[] }
  realtime_data: { source_type: 'simulated_extension'; inquiry: { inquiry_id: string; item_category: string; status: string; updated_at: string }; quotations: Array<{ quotation_id: string; inquiry_id: string; supplier_id: string; status: string; updated_at: string }>; orders: Array<{ order_id: string; status: string; updated_at: string }> }
}
export interface IntentMatch { level_1: string; level_2: string; confidence: number; alternatives: string[] }
export interface Citation { citation_id: string; source_type: 'knowledge' | 'tool'; title: string; version_or_freshness: string }
export interface AnswerDraft { facts: string[]; table: Array<Record<string, string | number>>; citations: Citation[]; limitations: string[] }
export interface TraceNode { sequence: number; node: string; status: 'completed' | 'failed' | 'skipped'; duration_ms: number; input_count: number; output_count: number; warning_codes: string[]; source_type: SourceType }
export interface EnterpriseRunReport {
  schema_version: 1; project_id: 'enterprise-rag-assistant'; case_id: string; is_custom_query: boolean
  original_query: string; normalized_query: string; rewritten_query: string; protected_constraints: string[]; subqueries: string[]
  intent: IntentMatch; route: Route; result_type: ResultType; answer: AnswerDraft; model_provider: 'mock'; trace: TraceNode[]; estimated_tokens: number; warnings: string[]; source_label: '模拟数据运行结果'
}
export interface EnterpriseAssets { cases: QueryCaseCollection; data: EnterpriseData; taxonomy: IntentTaxonomy }
export interface RunBundleV2 {
  schema_version: 2; project_id: 'enterprise-rag-assistant'; case_id: string; run_id: string; trace_id: string; status: 'completed'
  identity: { workflow_version: 'enterprise-rag-workflow-v1'; dataset_version: 'enterprise-query-cases-v1'; rules_version: 'enterprise-routing-v1'; prompt_or_policy_version: 'enterprise-answer-policy-v1'; runtime_version: 'rag-browser-v1'; model_provider: 'mock'; seed: 23 }
  nodes: Array<Omit<TraceNode, 'source_type'> & { source_type: SourceType; fact_id: null; claim_id: null }>
  citations: Array<{ citation_id: string; public_summary: string; source_type: SourceType; fact_id: null; claim_id: null }>
  results: Array<{ result_id: string; result_type: 'answer' | 'clarification' | 'refusal'; summary: string; citation_ids: string[]; source_type: SourceType; fact_id: null; claim_id: null }>
  claims: Array<{ statement: string; source_type: 'public_reconstruction'; fact_id: null; claim_id: null }>
  estimated_tokens: number; estimated_cost_usd: 0; warnings: string[]; generated_at: string
}

function record(value: unknown): value is Record<string, unknown> { return typeof value === 'object' && value !== null && !Array.isArray(value) }
function publicHeader(value: Record<string, unknown>, versionKey: string, version: string) {
  if (value.schema_version !== 1) throw new Error('runtime_schema_mismatch')
  if (value.project_id !== 'enterprise-rag-assistant' || value.synthetic !== true || value.source_label !== '公开模拟数据' || value[versionKey] !== version) throw new Error('fixture_public_boundary_mismatch')
}
export function parseEnterpriseAssets(casesRaw: unknown, dataRaw: unknown, taxonomyRaw: unknown): EnterpriseAssets {
  if (!record(casesRaw) || !record(dataRaw) || !record(taxonomyRaw)) throw new Error('fixture_shape_mismatch')
  publicHeader(casesRaw, 'dataset_version', 'enterprise-query-cases-v1'); publicHeader(dataRaw, 'dataset_version', 'enterprise-business-data-v1'); publicHeader(taxonomyRaw, 'taxonomy_version', 'enterprise-intent-taxonomy-v1')
  if (!Array.isArray(casesRaw.cases) || casesRaw.cases.length !== 10 || !record(dataRaw.knowledge_data) || !record(dataRaw.realtime_data) || !Array.isArray(taxonomyRaw.definitions) || taxonomyRaw.definitions.length !== 24) throw new Error('fixture_shape_mismatch')
  return { cases: casesRaw as unknown as QueryCaseCollection, data: dataRaw as unknown as EnterpriseData, taxonomy: taxonomyRaw as unknown as IntentTaxonomy }
}
