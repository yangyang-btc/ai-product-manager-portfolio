import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

export const sampleEvidence = {
  evidence_id: 'EV-QMS-001',
  source: 'QMS',
  source_record_id: 'QA-INCOMING-001',
  title: '质量异常单',
  public_summary: '模拟来料检漏结果超过当前有效规范。',
  supports: [],
  conflicts: [],
  observed_at: '2026-01-15T09:10:00+08:00',
}

export const sampleHypothesis = {
  hypothesis_id: 'H1',
  direction: '测量系统或检漏夹具污染',
  confidence: 'medium',
  reasoning_summary: '当前证据支持优先排查测量链路。',
  supporting_evidence_ids: ['EV-QMS-001'],
  counter_evidence_ids: ['EV-QMS-001'],
  missing_information: ['独立设备复测结果'],
  validation_actions: [{
    action_id: 'VA-H1-01',
    action: '执行独立设备复测',
    owner_role: '质量工程师',
    target: '当前批次',
    expected_result: '区分产品与测量系统偏差',
  }],
  deterministic_conclusion: false,
}

const created = {
  schema_version: 1,
  run_id: 'run_test',
  case_id: 'incoming_material_001',
  trace_id: 'trace_test',
  session_token: 'session_test',
  stream_token: 'stream_test',
  status: 'awaiting_human',
  expires_at: '2026-01-15T11:00:00+08:00',
}

const snapshot = {
  schema_version: 1,
  run_id: 'run_test',
  case_id: 'incoming_material_001',
  status: 'awaiting_human',
  current_node: 'await_human',
  result_summary: {
    result_type: 'hypothesis_matrix',
    summary: '已形成待验证原因方向。',
    facts: ['current_lot_exceeds_effective_limit'],
    evidence: [sampleEvidence],
    hypotheses: [sampleHypothesis],
    required_clarifications: [],
    human_decision: null,
  },
  allowed_actions: ['confirm', 'reject', 'supplement', 'resume'],
  updated_at: '2026-01-15T10:30:00+08:00',
  expires_at: '2026-01-15T11:00:00+08:00',
}

export const handlers = [
  http.post('http://localhost:8000/api/v1/runs', () => HttpResponse.json(created)),
  http.get('http://localhost:8000/api/v1/runs/run_test', () => HttpResponse.json(snapshot)),
  http.get('http://localhost:8000/api/v1/runs/run_test/trace', () => HttpResponse.json({
    schema_version: 1,
    trace_id: 'trace_test',
    nodes: [{ sequence: 1, node: 'intake', status: 'completed', duration_ms: 2, input_count: 1, output_count: 1, warning_codes: [] }],
    total_duration_ms: 2,
    estimated_tokens: 120,
    estimated_cost_usd: 0.00024,
    warnings: [],
  })),
  http.get('http://localhost:8000/api/v1/runs/run_test/events', () => new HttpResponse(
    'id: 1\nevent: node_completed\ndata: {"node":"intake","status":"running","warning_codes":[]}\n\n',
    { headers: { 'Content-Type': 'text/event-stream' } },
  )),
]

export const server = setupServer(...handlers)
