import { createRunBundle, loadContractFixtures, runContractReview, serializeRunBundle, type ContractFixture, type ContractRunReport, type ReviewStatus } from '@portfolio/contract-browser-runtime'
import { useEffect, useMemo, useRef, useState } from 'react'

import { CaseRail, ContractDocument, RiskCard, TraceDrawer, WorkflowRail } from './components'

const PORTFOLIO_URL = import.meta.env.VITE_PORTFOLIO_URL || (import.meta.env.DEV ? 'http://localhost:4173/#/project/contract' : '')
const EVALUATION_URL = import.meta.env.VITE_EVALUATION_LAB_URL || (import.meta.env.DEV ? 'http://localhost:8501?project=contract-review-agent' : '')
const REPOSITORY_URL = import.meta.env.VITE_PUBLIC_SOURCE_URL || ''
const EXECUTION_TIMEOUT_MS = 5000

type Phase = 'loading' | 'idle' | 'running' | 'complete' | 'error'

function delay(ms: number) { return new Promise(resolve => window.setTimeout(resolve, ms)) }

async function executeWithTimeout(fixture: ContractFixture) {
  let timeoutId = 0
  const timeout = new Promise<never>((_, reject) => { timeoutId = window.setTimeout(() => reject(new Error('browser_execution_timeout')), EXECUTION_TIMEOUT_MS) })
  try { return await Promise.race([Promise.resolve().then(() => runContractReview(fixture)), timeout]) }
  finally { window.clearTimeout(timeoutId) }
}

export default function App() {
  const [fixtures, setFixtures] = useState<ContractFixture[]>([])
  const [selectedId, setSelectedId] = useState('procurement_contract_001')
  const [phase, setPhase] = useState<Phase>('loading')
  const [report, setReport] = useState<ContractRunReport | null>(null)
  const [visibleNodes, setVisibleNodes] = useState(0)
  const [error, setError] = useState('')
  const [traceOpen, setTraceOpen] = useState(false)
  const [reviewStatuses, setReviewStatuses] = useState<Record<string, ReviewStatus>>({})
  const runNonce = useRef(0)

  const loadCases = async () => {
    setPhase('loading'); setError('')
    try { const loaded = await loadContractFixtures(); setFixtures(loaded); setSelectedId(current => loaded.some(item => item.scenario_id === current) ? current : loaded[0].scenario_id); setPhase('idle') }
    catch (reason) { setError(reason instanceof Error && reason.message === 'runtime_schema_mismatch' ? '当前案例版本不受支持。' : '案例资源加载失败，请刷新或查看本地运行说明。'); setPhase('error') }
  }

  useEffect(() => { void loadCases() }, [])
  const fixture = useMemo(() => fixtures.find(item => item.scenario_id === selectedId) || fixtures[0], [fixtures, selectedId])
  const previewNodes = report?.trace || (fixture ? runContractReview(fixture).trace : [])

  const selectCase = (id: string) => { runNonce.current += 1; setSelectedId(id); setReport(null); setVisibleNodes(0); setReviewStatuses({}); setError(''); setPhase('idle') }

  const run = async () => {
    if (!fixture || phase === 'running') return
    const nonce = ++runNonce.current
    setPhase('running'); setReport(null); setVisibleNodes(0); setReviewStatuses({}); setError('')
    try {
      const nextReport = await executeWithTimeout(fixture)
      for (let index = 1; index <= nextReport.trace.length; index += 1) { await delay(45); if (runNonce.current !== nonce) return; setVisibleNodes(index) }
      setReport(nextReport)
      setReviewStatuses(Object.fromEntries(nextReport.findings.map(item => [item.finding_id, item.human_status])))
      setPhase('complete')
    } catch (reason) {
      setError(reason instanceof Error && reason.message === 'browser_execution_timeout' ? '运行已超过 5 秒并停止，请重试。' : '审查运行停止。请检查案例版本后重试。')
      setPhase('error')
    }
  }

  const downloadBundle = () => {
    if (!fixture || !report) return
    try {
      const blob = new Blob([serializeRunBundle(createRunBundle(fixture, report))], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a'); anchor.href = url; anchor.download = `${report.case_id}-run-bundle-v2.json`; anchor.click(); URL.revokeObjectURL(url)
      setError('')
    } catch { setError('Run Bundle 暂时无法导出，当前审查结果仍保留，请重试。') }
  }

  if (phase === 'loading') return <main className="state-page"><span>CONTRACT REVIEW / LOADING</span><h1>正在装入公开模拟案卷</h1><i /></main>
  if (!fixture) return <main className="state-page error"><span>ASSET LOAD FAILURE</span><h1>{error || '案例资源不可用'}</h1><button onClick={() => void loadCases()}>重新加载</button></main>

  return <div className="console-shell"><header className="console-header"><a href={PORTFOLIO_URL} className="brand"><span>YJ / AI PM</span><strong>合同审查 Agent</strong></a><div className="header-boundary"><i />公开重建 · 离线模拟</div><nav><a href={PORTFOLIO_URL}>返回项目</a>{REPOSITORY_URL && <a href={REPOSITORY_URL} target="_blank" rel="noreferrer">查看公开重建源码 ↗</a>}</nav></header><div className="legal-notice"><strong>演示边界</strong><span>案例为符合半导体设备交易关系的公开模拟合同；结果不构成法律意见，关键风险必须由法务和业务人员复核。</span></div><main className="workbench"><CaseRail fixtures={fixtures} selectedId={fixture.scenario_id} onSelect={selectCase} disabled={phase === 'running'} /><ContractDocument fixture={fixture} findings={report?.findings} /><aside className="review-pane"><section className="run-command"><div><span>AUTOMATED FIRST PASS</span><h1>{phase === 'complete' ? `发现 ${report?.findings.length || 0} 个待复核风险` : '运行合同初审'}</h1><p>{phase === 'complete' && report?.findings.length === 0 ? '未发现版本化规则覆盖的自动风险；这不表示合同已经获得法律批准。' : '规则、检索和语义判断只提供初审证据，最终判断保留给人。'}</p></div><button className="run-button" onClick={() => void run()} disabled={phase === 'running'}>{phase === 'running' ? `审查中 ${visibleNodes}/${previewNodes.length}` : phase === 'complete' ? '重新运行' : '开始模拟审查'}<span>→</span></button></section>{error && <div className="inline-error" role="alert">{error}</div>}<WorkflowRail nodes={previewNodes} visibleCount={phase === 'complete' ? previewNodes.length : visibleNodes} running={phase === 'running'} />{phase === 'complete' && report && <section className="results" aria-live="polite"><header><span>RISK LEDGER</span><strong>{report.findings.length ? '人工复核队列' : '自动检查完成'}</strong></header>{report.findings.map(finding => <RiskCard key={finding.finding_id} finding={finding} status={reviewStatuses[finding.finding_id]} onStatus={status => setReviewStatuses(current => ({ ...current, [finding.finding_id]: status }))} />)}<div className="evidence-actions"><button onClick={() => setTraceOpen(true)}>查看 Trace</button><button onClick={downloadBundle}>下载 Run Bundle</button>{EVALUATION_URL ? <a href={EVALUATION_URL} target="_blank" rel="noreferrer">版本化评测 ↗</a> : <span aria-disabled="true">评测报告部署中</span>}{REPOSITORY_URL && <a href={REPOSITORY_URL} target="_blank" rel="noreferrer">公开重建源码 ↗</a>}</div></section>}</aside></main>{report && <TraceDrawer report={report} open={traceOpen} onClose={() => setTraceOpen(false)} />}<footer className="console-footer"><span>CONTRACT-BROWSER-V1</span><p>浏览器内确定性运行 · 不上传合同 · 不采集 API Key · Bundle 不含完整条款</p></footer></div>
}
