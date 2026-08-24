import golden from '../../../../tests/golden/contract-browser-parity.json'
import { describe, expect, it } from 'vitest'

import { CONTRACT_FIXTURES } from './fixtures'
import { normalizeForParity, runContractReview } from './runtime'

describe('Python/browser parity', () => {
  it('matches every normalized golden case field for field', () => {
    expect(CONTRACT_FIXTURES.map(item => normalizeForParity(runContractReview(item)))).toEqual(golden)
  })

  it('is invariant to clause order and unrelated business fields', () => {
    const fixture = structuredClone(CONTRACT_FIXTURES[0])
    fixture.contract.clauses.reverse()
    fixture.contract.business_context.unrelated_public_note = 'does not affect review'
    expect(normalizeForParity(runContractReview(fixture))).toEqual(golden[0])
  })

  it('recognizes controlled synonymous payment wording without case lookup', () => {
    const fixture = structuredClone(CONTRACT_FIXTURES[0])
    fixture.scenario_id = 'metamorphic_procurement'
    const payment = fixture.contract.clauses.find(item => item.heading === '付款安排')!
    payment.text = '每批到货并完成签收后五个工作日内支付该批货款90%。'
    const report = runContractReview(fixture)
    expect(report.findings.some(item => item.rule_id === 'RULE-PROC-012')).toBe(true)
  })
})
