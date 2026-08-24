import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import App from './App'

describe('quality Agent console', () => {
  it('shows the evidence-first thesis before a run', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /不是猜根因/ })).toBeInTheDocument()
    expect(screen.getByText('证据先于结论')).toBeInTheDocument()
    expect(screen.getByText('固定离线模拟 · 不调用外部模型')).toBeInTheDocument()
  })

  it('renders evidence, hypotheses and the human checkpoint after a run', async () => {
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: /运行证据分析/ }))

    await waitFor(() => {
      expect(screen.getByText('模拟来料检漏结果超过当前有效规范。')).toBeInTheDocument()
    })
    expect(screen.getByText('测量系统或检漏夹具污染')).toBeInTheDocument()
    expect(screen.getByText('系统不会替你做质量处置')).toBeInTheDocument()
  })
})
