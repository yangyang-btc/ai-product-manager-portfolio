import type { ContractFixture, ContractRunReport, ReviewStatus, RiskFinding, TraceNode } from '@portfolio/contract-browser-runtime'

const CASE_LABELS: Record<string, { index: string; title: string; note: string }> = {
  procurement_contract_001: { index: 'C-01', title: '核心部件采购', note: '付款、来料检验与质量异议' },
  sales_contract_001: { index: 'C-02', title: '设备销售', note: 'FAT、SAT 与质保起算' },
  nda_001: { index: 'C-03', title: '技术资料 NDA', note: '保密范围与允许披露' },
  technical_cooperation_001: { index: 'C-04', title: '联合技术开发', note: '背景与新生成果知识产权' },
  procurement_safe_001: { index: 'C-05', title: '采购反例', note: '无自动风险不等于法律批准' },
  cross_clause_context_loss: { index: 'C-06', title: '跨条款边界', note: '正文责任上限与附件例外' },
}

const TYPE_LABELS = { procurement: '采购合同', sales: '设备销售合同', nda: '保密协议', technical_cooperation: '技术合作协议' } as const
const NODE_LABELS: Record<string, string> = {
  ingest_document: '加载模拟合同', classify_contract: '合同类型路由', structural_clause_split: '结构化条款切分',
  deterministic_rules: '确定性规则检查', retrieve_policy_and_precedent: '规则与案例检索', semantic_risk_review: '语义风险判断',
  cross_clause_consistency: '跨条款一致性', evidence_validation: '证据完整性校验', risk_ranking: '风险稳定排序', mandatory_human_review: '高风险人工复核',
}

export function CaseRail({ fixtures, selectedId, onSelect, disabled }: { fixtures: ContractFixture[]; selectedId: string; onSelect: (id: string) => void; disabled: boolean }) {
  return <aside className="case-rail" aria-label="合同案例"><div className="rail-title"><span>CASE FILES</span><strong>公开模拟案卷</strong></div><div className="case-list">{fixtures.map(fixture => {
    const label = CASE_LABELS[fixture.scenario_id]
    return <button key={fixture.scenario_id} className={selectedId === fixture.scenario_id ? 'selected' : ''} onClick={() => onSelect(fixture.scenario_id)} disabled={disabled}><span>{label.index}</span><div><strong>{label.title}</strong><small>{label.note}</small></div></button>
  })}</div><p className="rail-boundary">不支持上传真实合同<br />所有数据仅在浏览器内运行</p></aside>
}

function valueLabel(value: unknown) {
  if (Array.isArray(value)) return value.join(' → ')
  if (typeof value === 'string' || typeof value === 'number') return String(value)
  return JSON.stringify(value)
}

export function ContractDocument({ fixture, findings = [] }: { fixture: ContractFixture; findings?: RiskFinding[] }) {
  const riskByClause = new Map<string, RiskFinding[]>()
  for (const finding of findings) for (const id of finding.clause_ids) riskByClause.set(id, [...(riskByClause.get(id) || []), finding])
  return <section className="document-pane"><header className="document-head"><div><span>{TYPE_LABELS[fixture.contract.contract_type]}</span><h2>{fixture.contract.contract_id}</h2></div><div><small>VERSION</small><strong>{fixture.contract.version}</strong></div></header><div className="party-line"><span>{fixture.contract.party_aliases[0]}</span><i>×</i><span>{fixture.contract.party_aliases[1]}</span></div><dl className="business-context">{Object.entries(fixture.contract.business_context).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{valueLabel(value)}</dd></div>)}</dl><div className="clause-sheet">{fixture.contract.clauses.map(clause => {
    const risks = riskByClause.get(clause.clause_id) || []
    return <article key={clause.clause_id} className={risks.length ? 'clause flagged' : 'clause'}><div className="page-marker">P.{clause.page}</div><div><header><strong>{clause.heading}</strong><code>{clause.clause_id}</code></header><p>{clause.text}</p></div>{risks.length > 0 && <aside aria-label="条款风险标记">{risks.map(risk => <span key={risk.finding_id} className={`risk-dot ${risk.severity}`}>{risk.severity === 'critical' ? '关键' : '高'}</span>)}</aside>}</article>
  })}</div></section>
}

export function WorkflowRail({ nodes, visibleCount, running }: { nodes: TraceNode[]; visibleCount: number; running: boolean }) {
  return <section className="workflow-panel" aria-label="审查工作流"><header><div><span>WORKFLOW / V1</span><strong>审查进度</strong></div><small>{visibleCount}/{nodes.length}</small></header><ol>{nodes.map((node, index) => {
    const visible = index < visibleCount
    const active = running && index === visibleCount
    return <li key={node.node} className={visible ? 'done' : active ? 'active' : ''}><i>{visible ? '✓' : String(index + 1).padStart(2, '0')}</i><div><strong>{NODE_LABELS[node.node] || node.node}</strong>{visible && <small>{node.output_count} 个输出 · {node.duration_ms} ms</small>}</div></li>
  })}</ol></section>
}

const STATUS_LABELS: Record<ReviewStatus, string> = { pending_legal_review: '待法务复核', confirmed: '风险已确认', supplement_requested: '已退回补充' }

export function RiskCard({ finding, status, onStatus }: { finding: RiskFinding; status: ReviewStatus; onStatus: (value: ReviewStatus) => void }) {
  return <article className={`risk-card severity-${finding.severity}`}><header><div><span>{finding.severity === 'critical' ? '关键风险' : '高风险'}</span><code>{finding.finding_id}</code></div><strong>{STATUS_LABELS[status]}</strong></header><h3>{finding.rationale}</h3><dl><div><dt>定位条款</dt><dd>{finding.clause_ids.join(' · ')}</dd></div><div><dt>审查依据</dt><dd>{finding.rule_id} / {finding.rule_version}<small>{finding.policy_document_id}</small></dd></div><div><dt>修改建议</dt><dd>{finding.suggestion}</dd></div><div><dt>仍需确认</dt><dd>{finding.missing_information.join('；')}</dd></div></dl><div className="review-actions"><button onClick={() => onStatus('confirmed')}>确认风险</button><button onClick={() => onStatus('supplement_requested')}>退回补充</button><button onClick={() => onStatus('pending_legal_review')}>保持待复核</button></div></article>
}

export function TraceDrawer({ report, open, onClose }: { report: ContractRunReport; open: boolean; onClose: () => void }) {
  if (!open) return null
  return <div className="drawer-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) onClose() }}><aside className="trace-drawer" role="dialog" aria-modal="true" aria-label="运行 Trace"><header><div><span>TRACE VIEW</span><h2>节点执行记录</h2></div><button onClick={onClose} aria-label="关闭 Trace">×</button></header><div className="trace-identity"><span>CASE</span><code>{report.case_id}</code><span>PROVIDER</span><code>{report.model_provider}</code></div><ol>{report.trace.map(node => <li key={node.node}><span>{String(node.sequence).padStart(2, '0')}</span><div><strong>{NODE_LABELS[node.node] || node.node}</strong><code>{node.node}</code></div><dl><div><dt>IN</dt><dd>{node.input_count}</dd></div><div><dt>OUT</dt><dd>{node.output_count}</dd></div><div><dt>TIME</dt><dd>{node.duration_ms}ms</dd></div></dl></li>)}</ol><p>Trace 仅记录节点名称、数量、耗时和错误码，不保存完整合同文本。</p></aside></div>
}
