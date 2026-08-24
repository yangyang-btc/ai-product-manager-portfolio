import { describe, expect, it } from 'vitest'

import { CONTRACT_FIXTURES, getContractFixture } from './fixtures'
import { createRunBundle } from './runBundle'
import { runContractReview } from './runtime'
import { parseContractFixture } from './types'

describe('contract browser runtime', () => {
  it('loads six strict public fixtures', () => {
    expect(CONTRACT_FIXTURES).toHaveLength(6)
    expect(() => parseContractFixture({ schema_version: 9 })).toThrow('runtime_schema_mismatch')
  })

  it('finds procurement cross-clause risks and keeps human review', () => {
    const report = runContractReview(getContractFixture('procurement_contract_001'))
    expect(report.findings.map(item => item.finding_id)).toEqual(['RF-DEMO-002', 'RF-DEMO-001'])
    expect(report.trace).toHaveLength(10)
    expect(report.status).toBe('awaiting_human')
  })

  it('does not invent risk for the safe counterexample', () => {
    const report = runContractReview(getContractFixture('procurement_safe_001'))
    expect(report.findings).toEqual([])
    expect(report.warnings).toContain('NO_AUTOMATED_RISK_IS_NOT_LEGAL_APPROVAL')
  })

  it('exports a v2 bundle without complete clause text', () => {
    const fixture = getContractFixture('nda_001')
    const bundleText = JSON.stringify(createRunBundle(fixture, runContractReview(fixture)))
    expect(bundleText).not.toContain(fixture.contract.clauses[0].text)
    expect(bundleText).toContain('公开模拟条款')
  })
})
