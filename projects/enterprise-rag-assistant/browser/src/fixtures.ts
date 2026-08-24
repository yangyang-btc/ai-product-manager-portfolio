import businessData from '../../fixtures/business_data_v1.json'
import taxonomy from '../../fixtures/intent_taxonomy_v1.json'
import queryCases from '../../fixtures/query_cases_v1.json'

import { parseEnterpriseAssets } from './types'

export const ENTERPRISE_ASSETS = parseEnterpriseAssets(queryCases, businessData, taxonomy)
export const QUERY_CASES = ENTERPRISE_ASSETS.cases.cases

export async function loadEnterpriseAssets() { return ENTERPRISE_ASSETS }
export function getQueryCase(caseId: string) {
  const queryCase = QUERY_CASES.find(item => item.case_id === caseId)
  if (!queryCase) throw new Error(`unknown_enterprise_case:${caseId}`)
  return queryCase
}
