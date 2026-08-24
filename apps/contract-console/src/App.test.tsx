import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import App from './App'

describe('contract review console', () => {
  it('loads realistic contract cases without an upload control', async () => {
    render(<App />)
    expect(await screen.findByRole('button', { name: /核心部件采购/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /设备销售/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /上传/ })).not.toBeInTheDocument()
    expect(screen.getByText('precision_motion_module')).toBeInTheDocument()
  })

  it('runs the workflow and exposes evidence-bound risks', async () => {
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: /开始模拟审查/ }))
    expect(await screen.findByText('人工复核队列', {}, { timeout: 2500 })).toBeInTheDocument()
    expect(screen.getByText('RF-DEMO-002')).toBeInTheDocument()
    expect(screen.getByText(/RULE-PROC-021/)).toBeInTheDocument()
    fireEvent.click(screen.getAllByRole('button', { name: '确认风险' })[0])
    expect(screen.getByText('风险已确认')).toBeInTheDocument()
  })

  it('shows the safe counterexample without declaring legal approval', async () => {
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: /采购反例/ }))
    fireEvent.click(screen.getByRole('button', { name: /开始模拟审查/ }))
    expect(await screen.findByText(/不表示合同已经获得法律批准/, {}, { timeout: 2500 })).toBeInTheDocument()
  })

  it('keeps results visible when bundle export fails', async () => {
    vi.stubGlobal('URL', { createObjectURL: () => { throw new Error('blocked') }, revokeObjectURL: vi.fn() })
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: /开始模拟审查/ }))
    await screen.findByText('人工复核队列', {}, { timeout: 2500 })
    fireEvent.click(screen.getByRole('button', { name: '下载 Run Bundle' }))
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('当前审查结果仍保留'))
    expect(screen.getByText('RF-DEMO-002')).toBeInTheDocument()
    vi.unstubAllGlobals()
  })
})
