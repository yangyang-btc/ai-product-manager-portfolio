import { useMemo, useRef, useState } from 'react'

import { ApiError, QUALITY_API_AVAILABLE, QualityAgentApi } from './api'
import {
  EvidenceList,
  EvidenceRail,
  HumanGate,
  HypothesisMatrix,
  ScenarioPicker,
  TraceDrawer,
  WorkflowTimeline,
} from './components'
import type { ActionName, DemoCase, RunCreated, RunSnapshot, TraceView, WorkflowEvent } from './types'

const PORTFOLIO_URL = import.meta.env.VITE_PORTFOLIO_URL || 'http://localhost:4173/#/project/quality'
const PUBLIC_SOURCE_URL = import.meta.env.VITE_PUBLIC_SOURCE_URL || ''

const DEMO_CASES: DemoCase[] = [
  {
    caseId: 'incoming_material_001',
    scenario: 'incoming',
    label: '真空阀来料检漏超限',
    eyebrow: '标准闭环',
    description: '跨 QMS / ERP / PLM，输出三类待验证方向。',
    tone: 'standard',
  },
  {
    caseId: 'no_evidence',
    scenario: 'incoming',
    label: '只有模糊异常描述',
    eyebrow: '证据边界',
    description: '缺少批次与检验记录，验证系统能否克制拒答。',
    tone: 'edge',
  },
  {
    caseId: 'tool_timeout',
    scenario: 'delivery',
    label: '现场异常且 ERP 超时',
    eyebrow: '系统失败',
    description: '保留可用证据，标记缺失来源并转人工。',
    tone: 'failure',
  },
]

function statusCopy(snapshot: RunSnapshot | null, busy: boolean): string {
  if (busy) return '正在执行 Tool、检索与证据校验'
  if (!snapshot) return '选择案例后开始一次新的证据分析'
  if (snapshot.status === 'awaiting_human') return '证据分析完成，等待人工决策'
  if (snapshot.status === 'completed') return '本次运行已完成，可导出或进入评测'
  return snapshot.result_summary?.summary || '运行状态已更新'
}

export default function App() {
  const api = useMemo(() => new QualityAgentApi(), [])
  const [selectedCase, setSelectedCase] = useState(DEMO_CASES[0])
  const [created, setCreated] = useState<RunCreated | null>(null)
  const [snapshot, setSnapshot] = useState<RunSnapshot | null>(null)
  const [trace, setTrace] = useState<TraceView | null>(null)
  const [events, setEvents] = useState<WorkflowEvent[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [supplement, setSupplement] = useState('')
  const [traceOpen, setTraceOpen] = useState(false)
  const runGeneration = useRef(0)

  const result = snapshot?.result_summary
  const evidence = result?.evidence || []
  const hypotheses = result?.hypotheses || []

  async function refreshRun(active: RunCreated) {
    const [nextSnapshot, nextTrace] = await Promise.all([
      api.getRun(active.run_id, active.session_token),
      api.getTrace(active.run_id, active.session_token),
    ])
    setSnapshot(nextSnapshot)
    setTrace(nextTrace)
  }

  async function startRun() {
    if (!QUALITY_API_AVAILABLE) {
      setError('公网 API 部署中。当前可查看完整工作流与公开源码，或按 README 在本地运行。')
      return
    }
    const generation = runGeneration.current + 1
    runGeneration.current = generation
    setBusy(true)
    setError(null)
    setNotice(null)
    setCreated(null)
    setSnapshot(null)
    setTrace(null)
    setEvents([])
    setSupplement('')
    try {
      const next = await api.createRun(selectedCase.caseId, selectedCase.scenario)
      if (generation !== runGeneration.current) return
      setCreated(next)
      const streamPromise = api.streamEvents(next.run_id, next.stream_token, (event) => {
        if (generation !== runGeneration.current) return
        setEvents((current) => current.some((item) => item.id === event.id) ? current : [...current, event])
      }).catch(() => setNotice('实时连接已结束，当前结果已通过运行快照恢复。'))
      await refreshRun(next)
      await streamPromise
    } catch (caught) {
      const message = caught instanceof ApiError ? caught.message : '运行未完成，请检查本地 API 是否已启动。'
      setError(message)
    } finally {
      if (generation === runGeneration.current) setBusy(false)
    }
  }

  async function handleAction(action: ActionName) {
    if (!created) return
    setBusy(true)
    setError(null)
    try {
      await api.postAction(created.run_id, created.session_token, action, supplement)
      await refreshRun(created)
      setSupplement('')
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : '人工操作未写入，请重试。')
    } finally {
      setBusy(false)
    }
  }

  async function downloadBundle() {
    if (!created) return
    const blob = await api.downloadBundle(created.run_id, created.session_token)
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${created.case_id}-run-bundle.json`
    anchor.click()
    URL.revokeObjectURL(url)
  }

  async function openEvaluation() {
    if (!created) return
    setBusy(true)
    try {
      const handoff = await api.createHandoff(created.run_id, created.session_token)
      window.location.assign(handoff.redeem_url)
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : '评测交接创建失败，可先导出 Run Bundle。')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="质量异常分析 Agent 首页">
          <span className="brand-glyph"><i /><i /><i /></span>
          <span><strong>Evidence Console</strong><small>Quality anomaly agent</small></span>
        </a>
        <div className="topbar-meta">
          <span>WORKFLOW V1</span><span>DATASET V1</span><span className="online-mark">OFFLINE / MOCK</span>
          <a href={PORTFOLIO_URL}>返回作品集</a>
          {PUBLIC_SOURCE_URL && <a href={PUBLIC_SOURCE_URL} target="_blank" rel="noreferrer">查看公开重建源码 ↗</a>}
        </div>
      </header>

      <main id="top">
        <section className="hero">
          <div className="hero-copy">
            <p className="eyebrow">半导体设备 · 质量异常分析</p>
            <h1>不是猜根因，<br /><em>是组织证据。</em></h1>
            <p className="hero-intro">
              Agent 将跨系统事实、FMEA 与历史案例组织成可验证假设；每项结论都保留反证、缺失信息和人工边界。
            </p>
          </div>
          <div className="hero-instrument" aria-label="运行原则">
            <span className="instrument-label">DECISION BOUNDARY</span>
            <div className="instrument-reading"><strong>0</strong><span>自动根因判定</span></div>
            <div className="instrument-rule" />
            <p>Rule / Tool / RAG / LLM / Human 各自只处理擅长的判断。</p>
          </div>
        </section>

        {!QUALITY_API_AVAILABLE && (
          <section className="deployment-note" role="status">
            <strong>公网 API 部署中</strong>
            <span>界面与工作流已发布；在线运行将在后端服务完成部署后开放。现可查看公开重建源码或本地运行。</span>
          </section>
        )}

        <section className="console-grid">
          <ScenarioPicker
            cases={DEMO_CASES}
            selected={selectedCase}
            busy={busy}
            onSelect={setSelectedCase}
            onRun={startRun}
          />
          <div className="run-workspace">
            <div className={`run-status ${busy ? 'is-running' : ''}`}>
              <span className="status-light" />
              <div><small>{created?.run_id || 'NEW RUN'}</small><strong>{statusCopy(snapshot, busy)}</strong></div>
              {created && <span className="expiry">会话仅保留 30 分钟</span>}
            </div>
            {error && <div className="message error-message"><strong>运行未完成</strong><span>{error}</span><button onClick={startRun}>重新运行</button></div>}
            {notice && <div className="message notice-message">{notice}</div>}
            <EvidenceRail evidence={evidence} />
          </div>
        </section>

        <WorkflowTimeline events={events} activeNode={snapshot?.current_node} />

        <section className="analysis-grid">
          <div className="analysis-column evidence-column">
            <div className="section-heading">
              <div><p className="eyebrow">Cross-system facts</p><h2>证据账本</h2></div>
              <span>{evidence.length} records</span>
            </div>
            <EvidenceList evidence={evidence} />
          </div>
          <div className="analysis-column hypothesis-column">
            <div className="section-heading">
              <div><p className="eyebrow">Hypothesis matrix</p><h2>待验证原因方向</h2></div>
              <span>{hypotheses.length} directions</span>
            </div>
            <HypothesisMatrix hypotheses={hypotheses} />
          </div>
        </section>

        {snapshot && (
          <HumanGate
            snapshot={snapshot}
            supplement={supplement}
            busy={busy}
            onSupplementChange={setSupplement}
            onAction={handleAction}
          />
        )}

        <section className="run-tools">
          <div><p className="eyebrow">Run artifacts</p><h2>查看执行证据，或带着结果进入评测。</h2></div>
          <div className="tool-actions">
            <button className="secondary-button" onClick={() => setTraceOpen(true)} disabled={!trace}>查看 Trace</button>
            <button className="secondary-button" onClick={downloadBundle} disabled={!created}>导出 Run Bundle</button>
            <button className="primary-button" onClick={openEvaluation} disabled={!created || busy}>进入 Evaluation Lab</button>
          </div>
        </section>
      </main>

      <footer>
        <span>公开模拟数据 · 模拟运行结果</span>
        <span>不会上传 API Key、公司数据或自由文本补充</span>
      </footer>
      <TraceDrawer trace={trace} open={traceOpen} onClose={() => setTraceOpen(false)} />
    </div>
  )
}
