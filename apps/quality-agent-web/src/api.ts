import type {
  ActionName,
  RunCreated,
  RunSnapshot,
  TraceView,
  WorkflowEvent,
} from './types'

const DEFAULT_API_URL = 'http://localhost:8000'
export const QUALITY_API_URL = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? DEFAULT_API_URL : '')
export const QUALITY_API_AVAILABLE = Boolean(QUALITY_API_URL)

export class ApiError extends Error {
  constructor(
    message: string,
    readonly code: string,
    readonly status: number,
    readonly retryable = false,
  ) {
    super(message)
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  const payload = await response.json()
  if (!response.ok) {
    const error = payload?.error
    throw new ApiError(
      error?.message || '服务暂时不可用，请稍后重试。',
      error?.code || 'REQUEST_FAILED',
      response.status,
      Boolean(error?.retryable),
    )
  }
  return payload as T
}

export class QualityAgentApi {
  constructor(private readonly baseUrl = QUALITY_API_URL) {}

  createRun(caseId: string, scenario: string): Promise<RunCreated> {
    return fetch(`${this.baseUrl}/api/v1/runs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Idempotency-Key': crypto.randomUUID(),
      },
      body: JSON.stringify({
        case_id: caseId,
        scenario,
        mode: 'offline',
        client_version: 'quality-web-v1',
      }),
    }).then(parseResponse<RunCreated>)
  }

  getRun(runId: string, sessionToken: string): Promise<RunSnapshot> {
    return fetch(`${this.baseUrl}/api/v1/runs/${runId}`, {
      headers: { Authorization: `Bearer ${sessionToken}` },
    }).then(parseResponse<RunSnapshot>)
  }

  getTrace(runId: string, sessionToken: string): Promise<TraceView> {
    return fetch(`${this.baseUrl}/api/v1/runs/${runId}/trace`, {
      headers: { Authorization: `Bearer ${sessionToken}` },
    }).then(parseResponse<TraceView>)
  }

  postAction(
    runId: string,
    sessionToken: string,
    action: ActionName,
    supplement = '',
  ): Promise<{ status: string }> {
    return fetch(`${this.baseUrl}/api/v1/runs/${runId}/actions`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${sessionToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        action,
        payload: supplement ? { supplement } : {},
        client_action_id: crypto.randomUUID(),
      }),
    }).then(parseResponse<{ status: string }>)
  }

  async downloadBundle(runId: string, sessionToken: string): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/v1/runs/${runId}/bundle`, {
      headers: { Authorization: `Bearer ${sessionToken}` },
    })
    const payload = await parseResponse<{ run_bundle: unknown }>(response)
    return new Blob([JSON.stringify(payload.run_bundle, null, 2)], {
      type: 'application/json',
    })
  }

  createHandoff(
    runId: string,
    sessionToken: string,
  ): Promise<{ redeem_url: string }> {
    return fetch(`${this.baseUrl}/api/v1/evaluation-handoffs`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${sessionToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ run_id: runId }),
    }).then(parseResponse<{ redeem_url: string }>)
  }

  async streamEvents(
    runId: string,
    streamToken: string,
    onEvent: (event: WorkflowEvent) => void,
  ): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/v1/runs/${runId}/events`, {
      headers: { Authorization: `Bearer ${streamToken}` },
    })
    if (!response.ok || !response.body) {
      throw new ApiError('实时进度中断，已切换到运行快照。', 'STREAM_UNAVAILABLE', response.status, true)
    }
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      buffer += decoder.decode(value || new Uint8Array(), { stream: !done })
      const blocks = buffer.split('\n\n')
      buffer = blocks.pop() || ''
      blocks.forEach((block) => {
        const id = Number(block.match(/^id: (.+)$/m)?.[1] || 0)
        const type = block.match(/^event: (.+)$/m)?.[1] || 'message'
        const rawData = block.match(/^data: (.+)$/m)?.[1]
        if (!rawData) return
        const data = JSON.parse(rawData)
        onEvent({ id, type, ...data } as WorkflowEvent)
      })
      if (done) break
    }
  }
}
