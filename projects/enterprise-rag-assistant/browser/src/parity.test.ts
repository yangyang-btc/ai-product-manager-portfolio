import golden from '../../../../tests/golden/rag-browser-parity.json'
import { describe, expect, it } from 'vitest'

import { QUERY_CASES } from './fixtures'
import { normalizeForParity, runEnterpriseQuery } from './runtime'

describe('Python/browser enterprise RAG parity', () => {
  it('matches all ten normalized golden cases', () => {
    expect(QUERY_CASES.map(item => normalizeForParity(runEnterpriseQuery({ caseId: item.case_id })))).toEqual(golden)
  })
  it('is invariant to case, spacing, and compound clause order', () => {
    expect(runEnterpriseQuery({ query: '  哪些供应商具有 iso9001 资质  ', userRole: 'bd', permissionScope: 'internal' }).intent.level_2).toBe('supplier_qualification')
    const reversed = runEnterpriseQuery({ query: '告诉我当前询价有几家已报价，同时找出能做精密清洗的供应商', userRole: 'operations', permissionScope: 'internal' })
    expect(reversed.route).toBe('rag_and_tool')
  })
})
