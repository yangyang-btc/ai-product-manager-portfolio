import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('enterprise RAG console', () => {
  it('loads B2B cases and shows the historical/simulated boundary', async () => {
    render(<App />)
    expect(await screen.findByText('知识 + 实时复合查询')).toBeInTheDocument()
    expect(screen.getByText(/Query 处理 · Rewrite/)).toBeInTheDocument()
    expect(screen.getByText(/询价 · 报价 · 订单/)).toBeInTheDocument()
  })
  it('runs the compound query with separate RAG and Tool evidence', async () => {
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: /运行受控查询/ }))
    expect(await screen.findByText('结构化结果', {}, { timeout: 2500 })).toBeInTheDocument()
    expect(screen.getByText('CIT-DEMO-CONTRACT-01')).toBeInTheDocument()
    expect(screen.getByText('TOOL-QUOTATION-DEMO-001')).toBeInTheDocument()
    expect(screen.getAllByText('模拟扩展').length).toBeGreaterThan(0)
  })
  it('blocks restricted facts for the public new-employee role', async () => {
    render(<App />)
    fireEvent.change(await screen.findByLabelText('版本化案例'), { target: { value: 'permission_denied_001' } })
    fireEvent.click(screen.getByRole('button', { name: /运行受控查询/ }))
    expect(await screen.findByText('权限已拦截', {}, { timeout: 2500 })).toBeInTheDocument()
    expect(screen.getAllByText(/且不披露数据是否存在/).length).toBeGreaterThan(0)
  })
  it('treats script-like custom input as text and asks for clarification', async () => {
    render(<App />)
    const input = await screen.findByLabelText('问题')
    fireEvent.change(input, { target: { value: '<script>alert(1)</script>' } })
    fireEvent.click(screen.getByRole('button', { name: /运行受控查询/ }))
    expect(await screen.findByText('需要澄清', {}, { timeout: 2500 })).toBeInTheDocument()
    expect(document.querySelector('script[src="alert(1)"]')).toBeNull()
  })
})
