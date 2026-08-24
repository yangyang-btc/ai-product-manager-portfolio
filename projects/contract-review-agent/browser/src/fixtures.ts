import boundary from '../../fixtures/cross_clause_context_loss.json'
import nda from '../../fixtures/nda_001.json'
import procurement from '../../fixtures/procurement_contract_001.json'
import safeProcurement from '../../fixtures/procurement_safe_001.json'
import sales from '../../fixtures/sales_contract_001.json'
import technical from '../../fixtures/technical_cooperation_001.json'

import { parseContractFixture, type ContractFixture } from './types'

const RAW_FIXTURES: unknown[] = [procurement, sales, nda, technical, safeProcurement, boundary]

export const CONTRACT_FIXTURES: ContractFixture[] = RAW_FIXTURES.map(parseContractFixture)

export function getContractFixture(caseId: string): ContractFixture {
  const fixture = CONTRACT_FIXTURES.find(item => item.scenario_id === caseId)
  if (!fixture) throw new Error(`unknown_contract_case:${caseId}`)
  return fixture
}

export async function loadContractFixtures(): Promise<ContractFixture[]> {
  return CONTRACT_FIXTURES
}
