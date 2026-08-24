export type RunStatus = 'created' | 'running' | 'awaiting_human' | 'completed' | 'failed'
export type ActionName = 'confirm' | 'reject' | 'supplement' | 'resume'

export interface Evidence {
  evidence_id: string
  source: 'QMS' | 'MES' | 'ERP' | 'PLM' | 'FMEA' | 'CASE'
  source_record_id: string
  title: string
  public_summary: string
  supports: string[]
  conflicts: string[]
  observed_at: string | null
}

export interface ValidationAction {
  action_id: string
  action: string
  owner_role: string
  target: string
  expected_result: string
}

export interface Hypothesis {
  hypothesis_id: string
  direction: string
  confidence: 'high' | 'medium' | 'low'
  reasoning_summary: string
  supporting_evidence_ids: string[]
  counter_evidence_ids: string[]
  missing_information: string[]
  validation_actions: ValidationAction[]
  deterministic_conclusion: boolean
}

export interface RunResult {
  result_type: 'hypothesis_matrix' | 'clarification' | 'degraded'
  summary: string
  facts: string[]
  evidence: Evidence[]
  hypotheses: Hypothesis[]
  required_clarifications: string[]
  human_decision: string | null
}

export interface RunCreated {
  run_id: string
  case_id: string
  trace_id: string
  session_token: string
  stream_token: string
  status: RunStatus
  expires_at: string
}

export interface RunSnapshot {
  run_id: string
  case_id: string
  status: RunStatus
  current_node: string
  result_summary: RunResult | null
  allowed_actions: ActionName[]
  updated_at: string
  expires_at: string
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

export interface TraceView {
  trace_id: string
  nodes: TraceNode[]
  total_duration_ms: number
  estimated_tokens: number
  estimated_cost_usd: number
  warnings: string[]
}

export interface WorkflowEvent {
  id: number
  type: string
  node: string
  status: RunStatus
  warning_codes: string[]
}

export interface DemoCase {
  caseId: string
  scenario: 'incoming' | 'assembly' | 'debug' | 'delivery'
  label: string
  eyebrow: string
  description: string
  tone: 'standard' | 'edge' | 'failure'
}
