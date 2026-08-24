import { describe, expect, it } from 'vitest'

import { ENTERPRISE_ASSETS, QUERY_CASES } from './fixtures'
import { createRunBundle } from './runBundle'
import { classifyIntent, runEnterpriseQuery } from './runtime'
import { parseEnterpriseAssets } from './types'

describe('enterprise RAG browser runtime', () => {
  it('loads the canonical 10 cases and 24 intents', () => {
    expect(QUERY_CASES).toHaveLength(10)
    expect(ENTERPRISE_ASSETS.taxonomy.definitions).toHaveLength(24)
    expect(() => parseEnterpriseAssets({ schema_version: 9 }, {}, {})).toThrow('runtime_schema_mismatch')
  })
  it('splits knowledge evidence from simulated realtime Tool facts', () => {
    const report = runEnterpriseQuery({ caseId: 'compound_query_001' })
    expect(report.route).toBe('rag_and_tool')
    expect(new Set(report.answer.citations.map(item => item.source_type))).toEqual(new Set(['knowledge', 'tool']))
    expect(report.trace[4].source_type).toBe('simulated_extension')
  })
  it('closes permission, refusal, conflict, and clarification paths', () => {
    expect(runEnterpriseQuery({ caseId: 'permission_denied_001' }).result_type).toBe('permission_denied')
    expect(runEnterpriseQuery({ caseId: 'no_answer_001' }).result_type).toBe('refusal')
    expect(runEnterpriseQuery({ caseId: 'conflicting_sources_001' }).warnings).toContain('SOURCE_VERSION_CONFLICT')
    expect(runEnterpriseQuery({ query: '帮我看看', userRole: 'bd', permissionScope: 'internal' }).result_type).toBe('clarification')
  })
  it('limits custom input and never exports query text', () => {
    expect(() => runEnterpriseQuery({ query: '问'.repeat(501) })).toThrow('invalid_custom_query:length')
    const report = runEnterpriseQuery({ query: '<script>alert(1)</script>', userRole: 'new_employee', permissionScope: 'public' })
    const bundle = JSON.stringify(createRunBundle(report))
    expect(bundle).not.toContain('<script>')
    expect(bundle).not.toContain(report.rewritten_query)
  })
  it('classifies controlled aliases without case lookup', () => {
    expect(classifyIntent('请解释氦检这个简称').level_2).toBe('alias_resolution')
  })
})
