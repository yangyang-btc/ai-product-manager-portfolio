import type {
  DemoCase,
  Evidence,
  Hypothesis,
  RunSnapshot,
  TraceView,
  WorkflowEvent,
} from './types'

const NODE_LABELS: Record<string, string> = {
  intake: '接收异常',
  validate_case: '校验案例',
  classify_scenario: '识别场景',
  plan_queries: '规划查询',
  fetch_qms_mes_erp_plm: '跨系统取证',
  retrieve_sop_fmea_8d_cases: '检索知识',
  build_evidence_graph: '构建证据图',
  generate_hypothesis_matrix: '生成假设',
  validate_schema_and_evidence: '证据校验',
  await_human: '等待人工',
  supplement_or_finalize: '人工处置',
}

const SOURCE_LABELS: Record<Evidence['source'], string> = {
  QMS: '质量',
  MES: '制造',
  ERP: '批次',
  PLM: '规范',
  FMEA: '失效模式',
  CASE: '历史案例',
}

export function ScenarioPicker({
  cases,
  selected,
  busy,
  onSelect,
  onRun,
}: {
  cases: DemoCase[]
  selected: DemoCase
  busy: boolean
  onSelect: (item: DemoCase) => void
  onRun: () => void
}) {
  return (
    <aside className="scenario-panel" aria-label="演示案例">
      <div className="panel-heading">
        <span className="section-index">CASE</span>
        <div>
          <p className="eyebrow">选择证据条件</p>
          <h2>异常案例</h2>
        </div>
      </div>
      <div className="case-list">
        {cases.map((item) => (
          <button
            className={`case-card ${selected.caseId === item.caseId ? 'is-selected' : ''}`}
            key={item.caseId}
            onClick={() => onSelect(item)}
            aria-pressed={selected.caseId === item.caseId}
            disabled={busy}
          >
            <span className={`case-tone ${item.tone}`}>{item.eyebrow}</span>
            <strong>{item.label}</strong>
            <small>{item.description}</small>
          </button>
        ))}
      </div>
      <button className="run-button" onClick={onRun} disabled={busy}>
        <span>{busy ? '正在唤醒分析链路' : '运行证据分析'}</span>
        <span aria-hidden="true">→</span>
      </button>
      <p className="mode-note">
        <span className="mode-dot" /> 固定离线模拟 · 不调用外部模型
      </p>
    </aside>
  )
}

export function EvidenceRail({ evidence }: { evidence: Evidence[] }) {
  const sources: Evidence['source'][] = ['QMS', 'MES', 'ERP', 'PLM', 'FMEA', 'CASE']
  return (
    <section className="evidence-rail" aria-label="证据信号轨道">
      <div className="rail-copy">
        <p className="eyebrow">Evidence rail</p>
        <h2>证据先于结论</h2>
        <p>业务系统事实与知识依据必须在假设生成前完成引用绑定。</p>
      </div>
      <div className="signal-lines">
        {sources.map((source, index) => {
          const count = evidence.filter((item) => item.source === source).length
          return (
            <div className={`signal-line ${count ? 'is-live' : ''}`} key={source}>
              <span className="signal-source">{source}</span>
              <span className="signal-track">
                <span className="signal-pulse" style={{ animationDelay: `${index * 90}ms` }} />
              </span>
              <span className="signal-count">{count || '—'}</span>
              <small>{SOURCE_LABELS[source]}</small>
            </div>
          )
        })}
      </div>
      <div className="rail-terminal" aria-label={`${evidence.length} 条证据`}>
        <span>{evidence.length.toString().padStart(2, '0')}</span>
        <small>可解析证据</small>
      </div>
    </section>
  )
}

export function WorkflowTimeline({
  events,
  activeNode,
}: {
  events: WorkflowEvent[]
  activeNode?: string
}) {
  const nodes = [
    'intake',
    'validate_case',
    'plan_queries',
    'fetch_qms_mes_erp_plm',
    'retrieve_sop_fmea_8d_cases',
    'build_evidence_graph',
    'generate_hypothesis_matrix',
    'validate_schema_and_evidence',
    'await_human',
  ]
  const completed = new Set(events.map((event) => event.node))
  return (
    <section className="workflow-strip" aria-label="工作流执行进度">
      <div className="strip-label">
        <span className="section-index">FLOW</span>
        <span>运行路径</span>
      </div>
      <ol>
        {nodes.map((node) => (
          <li
            key={node}
            className={`${completed.has(node) ? 'is-complete' : ''} ${activeNode === node ? 'is-active' : ''}`}
          >
            <span className="node-mark" />
            <small>{NODE_LABELS[node]}</small>
          </li>
        ))}
      </ol>
    </section>
  )
}

export function EvidenceList({ evidence }: { evidence: Evidence[] }) {
  if (!evidence.length) {
    return (
      <div className="empty-state">
        <strong>当前没有可验证证据</strong>
        <p>补充物料、批次和检验记录后，系统才会进入原因分析。</p>
      </div>
    )
  }
  return (
    <div className="evidence-list">
      {evidence.map((item) => (
        <article className="evidence-card" key={item.evidence_id}>
          <div className="evidence-meta">
            <span className={`source-tag source-${item.source.toLowerCase()}`}>{item.source}</span>
            <code>{item.evidence_id}</code>
          </div>
          <h4>{item.title}</h4>
          <p>{item.public_summary}</p>
          <small>{item.source_record_id}</small>
        </article>
      ))}
    </div>
  )
}

function EvidenceChips({ ids, kind }: { ids: string[]; kind: 'support' | 'counter' }) {
  return (
    <div className={`evidence-chips ${kind}`}>
      {ids.map((id) => (
        <code key={id}>{id}</code>
      ))}
    </div>
  )
}

export function HypothesisMatrix({ hypotheses }: { hypotheses: Hypothesis[] }) {
  if (!hypotheses.length) {
    return (
      <div className="empty-state guarded">
        <span className="guard-symbol">∅</span>
        <strong>已阻止无依据根因生成</strong>
        <p>当前证据不满足假设生成条件，流程停留在澄清与人工边界。</p>
      </div>
    )
  }
  return (
    <div className="hypothesis-matrix">
      {hypotheses.map((item) => (
        <article className="hypothesis-card" key={item.hypothesis_id}>
          <header>
            <span className="hypothesis-id">{item.hypothesis_id}</span>
            <div>
              <h4>{item.direction}</h4>
              <span className={`confidence ${item.confidence}`}>{item.confidence} confidence</span>
            </div>
          </header>
          <p className="reasoning">{item.reasoning_summary}</p>
          <div className="matrix-row">
            <span>支持证据</span>
            <EvidenceChips ids={item.supporting_evidence_ids} kind="support" />
          </div>
          <div className="matrix-row">
            <span>反证</span>
            <EvidenceChips ids={item.counter_evidence_ids} kind="counter" />
          </div>
          <div className="matrix-row missing-row">
            <span>仍缺少</span>
            <p>{item.missing_information.join('；')}</p>
          </div>
          {item.validation_actions.map((action) => (
            <div className="validation-action" key={action.action_id}>
              <div>
                <span>下一步验证</span>
                <strong>{action.action}</strong>
              </div>
              <small>{action.owner_role} · {action.target}</small>
            </div>
          ))}
        </article>
      ))}
    </div>
  )
}

export function HumanGate({
  snapshot,
  supplement,
  busy,
  onSupplementChange,
  onAction,
}: {
  snapshot: RunSnapshot
  supplement: string
  busy: boolean
  onSupplementChange: (value: string) => void
  onAction: (action: 'confirm' | 'reject' | 'supplement') => void
}) {
  const isComplete = snapshot.status === 'completed'
  return (
    <section className={`human-gate ${isComplete ? 'is-complete' : ''}`}>
      <div className="gate-marker"><span>H</span></div>
      <div className="gate-copy">
        <p className="eyebrow">Human checkpoint</p>
        <h3>{isComplete ? '人工决策已写入运行记录' : '系统不会替你做质量处置'}</h3>
        <p>
          {snapshot.result_summary?.human_decision ||
            '请确认分析方向、退回，或补充只在当前会话使用的信息。放行、拒收与供应商处置仍由质量角色决定。'}
        </p>
      </div>
      {!isComplete && (
        <div className="gate-controls">
          <label htmlFor="supplement">补充说明（不会进入公开 Run Bundle）</label>
          <textarea
            id="supplement"
            value={supplement}
            onChange={(event) => onSupplementChange(event.target.value)}
            placeholder="例如：已完成独立设备复测，结果仍超限"
            maxLength={500}
          />
          <div className="gate-actions">
            <button className="secondary-button" onClick={() => onAction('reject')} disabled={busy}>
              退回分析
            </button>
            <button
              className="secondary-button"
              onClick={() => onAction('supplement')}
              disabled={busy || !supplement.trim()}
            >
              补充后结束
            </button>
            <button className="primary-button" onClick={() => onAction('confirm')} disabled={busy}>
              确认分析方向
            </button>
          </div>
        </div>
      )}
    </section>
  )
}

export function TraceDrawer({ trace, open, onClose }: { trace: TraceView | null; open: boolean; onClose: () => void }) {
  if (!open) return null
  return (
    <div className="drawer-layer" role="presentation" onMouseDown={onClose}>
      <aside className="trace-drawer" role="dialog" aria-modal="true" aria-label="运行 Trace" onMouseDown={(event) => event.stopPropagation()}>
        <header>
          <div>
            <p className="eyebrow">Privacy-safe trace</p>
            <h2>节点执行记录</h2>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="关闭 Trace">×</button>
        </header>
        {trace ? (
          <>
            <div className="trace-stats">
              <span><strong>{trace.nodes.length}</strong> 节点</span>
              <span><strong>{trace.total_duration_ms}</strong> ms</span>
              <span><strong>{trace.estimated_tokens}</strong> 估算 Token</span>
              <span><strong>${trace.estimated_cost_usd.toFixed(4)}</strong> 估算成本</span>
            </div>
            <ol className="trace-list">
              {trace.nodes.map((node) => (
                <li key={`${node.sequence}-${node.node}`}>
                  <span className="trace-sequence">{node.sequence.toString().padStart(2, '0')}</span>
                  <div><strong>{NODE_LABELS[node.node] || node.node}</strong><code>{node.node}</code></div>
                  <small>{node.input_count} in / {node.output_count} out</small>
                  <span className={`trace-status ${node.status}`}>{node.status}</span>
                </li>
              ))}
            </ol>
          </>
        ) : <div className="empty-state"><p>Trace 尚未生成。</p></div>}
      </aside>
    </div>
  )
}
