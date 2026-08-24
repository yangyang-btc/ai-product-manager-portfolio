import { render, screen, waitFor, within } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import App from './App'

describe('personal AI product manager portfolio', () => {
  beforeEach(() => { window.location.hash = '#/' })

  it('opens with Yang Jiaojing’s positioning and no public audience selector', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /从业务问题/ })).toBeInTheDocument()
    expect(screen.getAllByText(/杨姣静/).length).toBeGreaterThan(0)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('shows three project cards with problem, role, outcome and claim labels', () => {
    render(<App />)
    const cards = ['quality', 'contract', 'rag'].map(id => screen.getByTestId(`project-card-${id}`))
    expect(cards).toHaveLength(3)
    cards.forEach(card => {
      expect(within(card).getByText('业务问题')).toBeInTheDocument()
      expect(within(card).getByText('负责范围')).toBeInTheDocument()
      expect(within(card).getByText('形成结果')).toBeInTheDocument()
      expect(within(card).getByText(/公开重建/)).toBeInTheDocument()
    })
  })

  it('features a runnable quality Agent and Evaluation Lab on the home page', () => {
    render(<App />)
    expect(screen.getByRole('heading', { level: 2, name: '质量异常分析 Agent' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '在线运行 Agent' })).toHaveAttribute('href', 'http://localhost:5173')
    expect(screen.getByRole('link', { name: /Evaluation Lab/ })).toHaveAttribute('href', 'http://localhost:8501')
    expect(screen.getByText(/在线结果来自公开模拟数据/)).toBeInTheDocument()
  })

  it('renders a deep project evaluation route without a server rewrite', async () => {
    window.location.hash = '#/project/quality/evaluation'
    render(<App />)
    await waitFor(() => expect(screen.getByRole('heading', { name: '如何验证' })).toBeInTheDocument())
    expect(screen.getByText('无依据结论率')).toBeInTheDocument()
    expect(screen.getByText('BAD CASE')).toBeInTheDocument()
  })

  it('opens the contract console while preserving local reproduction and evaluation', () => {
    window.location.hash = '#/project/contract'
    const { unmount } = render(<App />)
    expect(screen.getByText('可在线体验 + 支持本地运行')).toBeInTheDocument()
    expect(screen.getByText(/projects\.contract_review_agent\.demo/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '打开合同审查操作台' })).toHaveAttribute(
      'href',
      'http://localhost:5174',
    )
    expect(screen.getByRole('link', { name: '查看版本化评测' })).toHaveAttribute(
      'href',
      'http://localhost:8501?project=contract-review-agent',
    )
    unmount()
    window.location.hash = '#/project/rag'
    render(<App />)
    expect(screen.getByText(/projects\.enterprise_rag_assistant\.demo/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '打开企业问答操作台' })).toHaveAttribute(
      'href',
      'http://localhost:5175',
    )
    expect(screen.getByRole('link', { name: '查看版本化评测' })).toHaveAttribute(
      'href',
      'http://localhost:8501?project=enterprise-rag-assistant',
    )
  })

  it('renders methodology, skills and evidence as shareable hash routes', async () => {
    window.location.hash = '#/skills'
    render(<App />)
    expect(screen.getByText('agent-workflow-designer')).toBeInTheDocument()
    window.location.hash = '#/evidence'
    window.dispatchEvent(new HashChangeEvent('hashchange'))
    await waitFor(() => expect(screen.getByRole('heading', { name: /从页面一路追到/ })).toBeInTheDocument())
    expect(screen.getByText('projects/quality_anomaly_agent/workflow.py')).toBeInTheDocument()
  })

  it('publishes four complete research studies and an annotated article route', async () => {
    window.location.hash = '#/research'
    render(<App />)
    expect(screen.getByRole('heading', { name: /追问 AI 产品怎样被信任/ })).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: /阅读完整拆解/ })).toHaveLength(4)
    window.location.hash = '#/research/codex'
    window.dispatchEvent(new HashChangeEvent('hashchange'))
    await waitFor(() => expect(screen.getByRole('heading', { level: 1, name: /Codex 产品拆解/ })).toBeInTheDocument())
    expect(screen.getByRole('heading', { name: '评测指标设计' })).toBeInTheDocument()
    expect(screen.getAllByText('作者判断').length).toBeGreaterThan(5)
    expect(screen.getByText(/CODEX-05/)).toBeInTheDocument()
    expect(document.title).toBe('Codex 产品拆解｜杨姣静')
  })

  it('provides a shareable about page', async () => {
    render(<App />)
    window.location.hash = '#/about'
    window.dispatchEvent(new HashChangeEvent('hashchange'))
    await waitFor(() => expect(screen.getByRole('heading', { name: /连接业务问题/ })).toBeInTheDocument())
    expect(document.title).toBe('关于｜杨姣静')
  })

  it('handles unknown routes with a personal-site return path', () => {
    window.location.hash = '#/missing'
    render(<App />)
    expect(screen.getByRole('heading', { name: '这个页面还不存在。' })).toBeInTheDocument()
    expect(screen.getByText(/项目、方法论与产品研究/)).toBeInTheDocument()
  })
})
