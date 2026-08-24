import { describe, expect, it, vi } from 'vitest'

import { QualityAgentApi } from './api'

describe('QualityAgentApi', () => {
  it('creates a run, reads the snapshot and parses buffered SSE', async () => {
    const api = new QualityAgentApi()
    const created = await api.createRun('incoming_material_001', 'incoming')
    expect(created.run_id).toBe('run_test')

    const snapshot = await api.getRun(created.run_id, created.session_token)
    expect(snapshot.result_summary?.hypotheses).toHaveLength(1)

    const onEvent = vi.fn()
    await api.streamEvents(created.run_id, created.stream_token, onEvent)
    expect(onEvent).toHaveBeenCalledWith(expect.objectContaining({ node: 'intake', id: 1 }))
  })
})
