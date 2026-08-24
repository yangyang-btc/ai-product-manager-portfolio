import { createRunBundle, loadEnterpriseAssets, runEnterpriseQuery, serializeRunBundle, type EnterpriseAssets, type EnterpriseRunReport, type PermissionScope, type UserRole } from '@portfolio/rag-browser-runtime'
import { useEffect, useMemo, useRef, useState } from 'react'
import { AnswerPanel, QueryPanel, RouteMap, TraceDrawer } from './components'

const PORTFOLIO_URL = import.meta.env.VITE_PORTFOLIO_URL || (import.meta.env.DEV ? 'http://localhost:4173/#/project/rag' : '')
const EVALUATION_URL = import.meta.env.VITE_EVALUATION_LAB_URL || (import.meta.env.DEV ? 'http://localhost:8501?project=enterprise-rag-assistant' : '')
const REPOSITORY_URL = import.meta.env.VITE_PUBLIC_SOURCE_URL || ''
type Phase = 'loading' | 'idle' | 'running' | 'complete' | 'error'
const delay = (ms: number) => new Promise(resolve => window.setTimeout(resolve, ms))
const scopeForRole = (role: UserRole): PermissionScope => role === 'new_employee' ? 'public' : 'internal'

export default function App() {
  const [assets, setAssets] = useState<EnterpriseAssets | null>(null)
  const [selected, setSelected] = useState('compound_query_001')
  const [query, setQuery] = useState('')
  const [role, setRole] = useState<UserRole>('operations')
  const [phase, setPhase] = useState<Phase>('loading')
  const [report, setReport] = useState<EnterpriseRunReport | null>(null)
  const [visibleNodes, setVisibleNodes] = useState(0)
  const [error, setError] = useState('')
  const [traceOpen, setTraceOpen] = useState(false)
  const nonce = useRef(0)

  useEffect(() => { void loadEnterpriseAssets().then(loaded => { const initial = loaded.cases.cases.find(item => item.case_id === 'compound_query_001')!; setAssets(loaded); setQuery(initial.query); setRole(initial.user_role); setPhase('idle') }).catch(() => { setError('公开语料或意图资源加载失败，请刷新后重试。'); setPhase('error') }) }, [])
  const cases = assets?.cases.cases || []
  const preview = useMemo(() => { if (!query.trim()) return null; try { return runEnterpriseQuery(selected === 'custom' ? { query, userRole: role, permissionScope: scopeForRole(role) } : { caseId: selected }) } catch { return null } }, [query, role, selected])

  const chooseCase = (id: string) => { nonce.current += 1; setSelected(id); setReport(null); setVisibleNodes(0); setError(''); setPhase('idle'); if (id !== 'custom') { const item = cases.find(value => value.case_id === id)!; setQuery(item.query); setRole(item.user_role) } }
  const changeQuery = (value: string) => { setQuery(value); setSelected('custom'); setReport(null); setVisibleNodes(0); setError(''); setPhase('idle') }
  const changeRole = (value: UserRole) => { setRole(value); setSelected('custom'); setReport(null); setVisibleNodes(0); setPhase('idle') }
  const run = async () => {
    if (!query.trim() || phase === 'running') return
    const current = ++nonce.current; setError(''); setReport(null); setVisibleNodes(0); setPhase('running')
    try {
      const next = runEnterpriseQuery(selected === 'custom' ? { query, userRole: role, permissionScope: scopeForRole(role) } : { caseId: selected })
      for (let index = 1; index <= next.trace.length; index += 1) { await delay(55); if (nonce.current !== current) return; setVisibleNodes(index) }
      setReport(next); setPhase('complete')
    } catch (reason) { setError(reason instanceof Error && reason.message.includes('length') ? '问题不能超过 500 个字符。' : '当前问题不符合受控输入范围，请调整后重试。'); setPhase('error') }
  }
  const download = () => { if (!report) return; try { const url = URL.createObjectURL(new Blob([serializeRunBundle(createRunBundle(report))], { type: 'application/json' })); const anchor = document.createElement('a'); anchor.href = url; anchor.download = `${report.case_id}-run-bundle-v2.json`; anchor.click(); URL.revokeObjectURL(url); setError('') } catch { setError('Run Bundle 暂时无法导出，当前结果仍保留。') } }

  if (phase === 'loading') return <main className="rag-state"><span>ENTERPRISE QUERY ROUTER</span><h1>正在加载公开供应链语料</h1><i /></main>
  if (!assets) return <main className="rag-state error"><span>ASSET LOAD FAILURE</span><h1>{error}</h1><button onClick={() => window.location.reload()}>刷新页面</button></main>
  const mapReport = report || preview
  return <div className="rag-shell"><header className="rag-header"><a href={PORTFOLIO_URL}><span>YJ / AI PM</span><strong>企业智能问答</strong></a><div className="system-mark">B2B SUPPLY KNOWLEDGE / ROUTER V1</div><nav><a href={PORTFOLIO_URL}>返回项目</a>{REPOSITORY_URL && <a href={REPOSITORY_URL} target="_blank" rel="noreferrer">查看公开重建源码 ↗</a>}</nav></header><section className="boundary-band"><article><span>HISTORICAL CORE / 公开重建</span><strong>Query 处理 · Rewrite · 意图 · RAG · 引用</strong></article><i>+</i><article><span>SIMULATED EXTENSION / 公开模拟</span><strong>询价 · 报价 · 订单 · 物流 Tool</strong></article><p>页面中的角色与权限只演示产品行为，所有打包数据均为访客可见的公开模拟数据。</p></section><main className="exchange-grid"><QueryPanel cases={cases} selected={selected} query={query} role={role} running={phase === 'running'} onCase={chooseCase} onQuery={changeQuery} onRole={changeRole} onRun={() => void run()} />{mapReport ? <RouteMap report={mapReport} visibleNodes={phase === 'complete' ? mapReport.trace.length : visibleNodes} /> : <section className="route-empty"><span>ROUTING GRAPH</span><h2>输入一个受控问题，查看它如何被拆分和路由。</h2></section>}{report && phase === 'complete' ? <AnswerPanel report={report} onTrace={() => setTraceOpen(true)} onDownload={download} /> : <aside className="answer-placeholder"><span>ANSWER / EVIDENCE</span><h2>{phase === 'running' ? `正在执行 ${visibleNodes}/8` : '运行后在这里检查答案与证据。'}</h2><p>静态知识与实时事实分开显示；权限不足、证据冲突和无答案路径不会生成看似确定的结论。</p></aside>}</main>{error && <div className="rag-error" role="alert">{error}</div>}<footer className="rag-footer"><span>RAG-BROWSER-V1</span><div>{EVALUATION_URL ? <a href={EVALUATION_URL} target="_blank" rel="noreferrer">版本化模拟评测 ↗</a> : <span aria-disabled="true">评测报告部署中</span>}{REPOSITORY_URL && <a href={REPOSITORY_URL} target="_blank" rel="noreferrer">公开重建源码 ↗</a>}</div><p>浏览器内离线运行 · 自定义问题不写入 Bundle · 不采集 API Key</p></footer>{report && <TraceDrawer nodes={report.trace} open={traceOpen} onClose={() => setTraceOpen(false)} />}</div>
}
