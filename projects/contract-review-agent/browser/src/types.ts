export type ContractType = 'procurement' | 'sales' | 'nda' | 'technical_cooperation'
export type Severity = 'low' | 'medium' | 'high' | 'critical'
export type ReviewStatus = 'pending_legal_review' | 'confirmed' | 'supplement_requested'

export interface Clause {
  clause_id: string
  heading: string
  page: number
  text: string
}

export interface ContractData {
  contract_id: string
  contract_type: ContractType
  version: string
  party_aliases: string[]
  business_context: Record<string, unknown>
  clauses: Clause[]
}

export interface ReviewRule {
  rule_id: string
  version: string
  severity: Severity
  requirement: string
}

export interface ContractFixture {
  schema_version: 1
  project_id: 'contract-review-agent'
  scenario_id: string
  synthetic: true
  source_label: '公开模拟数据'
  contract: ContractData
  rules: ReviewRule[]
  expected: {
    findings: unknown[]
    non_findings: unknown[]
    forbidden_behavior: string[]
  }
}

export interface TraceNode {
  sequence: number
  node: string
  status: 'completed' | 'failed' | 'skipped'
  duration_ms: number
  input_count: number
  output_count: number
  warning_codes: string[]
}

export interface RiskFinding {
  finding_id: string
  severity: Severity
  source: 'rule' | 'rag' | 'llm' | 'rule_and_cross_clause'
  clause_ids: string[]
  original_excerpt: string
  rule_id: string
  rule_version: string
  policy_document_id: string
  rationale: string
  suggestion: string
  missing_information: string[]
  human_required: true
  human_status: ReviewStatus
}

export interface ContractRunReport {
  schema_version: 1
  project_id: 'contract-review-agent'
  case_id: string
  contract_id: string
  contract_type: ContractType
  status: 'awaiting_human'
  model_provider: 'mock'
  findings: RiskFinding[]
  covered_clause_ids: string[]
  unreviewed_areas: string[]
  trace: TraceNode[]
  estimated_tokens: number
  warnings: string[]
  source_label: '模拟数据运行结果'
}

export type SourceType = 'public_reconstruction' | 'simulated_run_result'

export interface RunBundleV2 {
  schema_version: 2
  project_id: 'contract-review-agent'
  case_id: string
  run_id: string
  trace_id: string
  status: 'awaiting_human'
  identity: {
    workflow_version: 'contract-workflow-v1'
    dataset_version: 'contract-fixtures-v1'
    rules_version: 'contract-rules-v1'
    prompt_or_policy_version: 'contract-policy-v1'
    runtime_version: 'contract-browser-v1'
    model_provider: 'mock'
    seed: 17
  }
  nodes: Array<TraceNode & { source_type: 'simulated_run_result'; fact_id: null; claim_id: null }>
  citations: Array<{
    citation_id: string
    public_summary: string
    source_type: SourceType
    fact_id: null
    claim_id: null
  }>
  results: Array<{
    result_id: string
    result_type: 'finding' | 'human_gate'
    summary: string
    citation_ids: string[]
    source_type: 'simulated_run_result'
    fact_id: null
    claim_id: null
  }>
  claims: Array<{
    statement: string
    source_type: 'public_reconstruction'
    fact_id: null
    claim_id: null
  }>
  estimated_tokens: number
  estimated_cost_usd: 0
  warnings: string[]
  generated_at: string
}

const TYPES: ContractType[] = ['procurement', 'sales', 'nda', 'technical_cooperation']

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function requireString(record: Record<string, unknown>, key: string): string {
  const value = record[key]
  if (typeof value !== 'string' || value.length === 0) throw new Error(`fixture field ${key} must be a non-empty string`)
  return value
}

export function parseContractFixture(input: unknown): ContractFixture {
  if (!isRecord(input)) throw new Error('fixture must be an object')
  if (input.schema_version !== 1) throw new Error('runtime_schema_mismatch')
  if (input.project_id !== 'contract-review-agent' || input.synthetic !== true || input.source_label !== '公开模拟数据') {
    throw new Error('fixture_public_boundary_mismatch')
  }
  if (!isRecord(input.contract) || !Array.isArray(input.contract.clauses) || !Array.isArray(input.rules) || !isRecord(input.expected)) {
    throw new Error('fixture_shape_mismatch')
  }
  const contractType = input.contract.contract_type
  if (typeof contractType !== 'string' || !TYPES.includes(contractType as ContractType)) throw new Error('fixture_contract_type_mismatch')
  const clauses = input.contract.clauses.map((value, index): Clause => {
    if (!isRecord(value) || typeof value.page !== 'number' || value.page < 1) throw new Error(`fixture clause ${index} is invalid`)
    return { clause_id: requireString(value, 'clause_id'), heading: requireString(value, 'heading'), page: value.page, text: requireString(value, 'text') }
  })
  const rules = input.rules.map((value, index): ReviewRule => {
    if (!isRecord(value)) throw new Error(`fixture rule ${index} is invalid`)
    const severity = requireString(value, 'severity')
    if (!['low', 'medium', 'high', 'critical'].includes(severity)) throw new Error(`fixture rule ${index} severity is invalid`)
    return { rule_id: requireString(value, 'rule_id'), version: requireString(value, 'version'), severity: severity as Severity, requirement: requireString(value, 'requirement') }
  })
  const aliases = input.contract.party_aliases
  if (!Array.isArray(aliases) || !aliases.every(value => typeof value === 'string')) throw new Error('fixture party aliases are invalid')
  return {
    schema_version: 1,
    project_id: 'contract-review-agent',
    scenario_id: requireString(input, 'scenario_id'),
    synthetic: true,
    source_label: '公开模拟数据',
    contract: {
      contract_id: requireString(input.contract, 'contract_id'), contract_type: contractType as ContractType,
      version: requireString(input.contract, 'version'), party_aliases: aliases,
      business_context: isRecord(input.contract.business_context) ? input.contract.business_context : {}, clauses,
    },
    rules,
    expected: {
      findings: Array.isArray(input.expected.findings) ? input.expected.findings : [],
      non_findings: Array.isArray(input.expected.non_findings) ? input.expected.non_findings : [],
      forbidden_behavior: Array.isArray(input.expected.forbidden_behavior) && input.expected.forbidden_behavior.every(value => typeof value === 'string') ? input.expected.forbidden_behavior : [],
    },
  }
}
