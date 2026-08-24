import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync } from 'node:fs'
import { dirname, join, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const OUTPUT = join(ROOT, 'dist-pages')
const MANIFEST = join(ROOT, 'release', 'public-manifest.yml')
const PUBLIC_INVENTORY = join(ROOT, 'public-files.json')

const SOURCE_PATHS = [
  'projects/quality_anomaly_agent/README.md',
  'projects/contract-review-agent/README.md',
  'projects/enterprise-rag-assistant/README.md',
  'projects/enterprise-rag-assistant/evaluation/latest.json',
  'projects/quality_anomaly_agent/workflow.py',
  'apps/quality_agent_api/main.py',
  'apps/quality-agent-web/src/App.tsx',
  'tests/test_quality_agent_api.py',
  'research/codex/article.md',
  'research/workbuddy/article.md',
  'research/claude-code/article.md',
  'research/cursor/article.md',
]

function normalizeBase(value = '/') {
  const trimmed = value.trim()
  if (!trimmed.startsWith('/') || trimmed.includes('..') || trimmed.includes('://')) {
    throw new Error(`BASE_URL must be a safe absolute path: ${value}`)
  }
  return `${trimmed.replace(/\/+$/, '')}/`.replace(/^\/\//, '/')
}

function readPublicPathMap() {
  const entries = new Map()
  if (existsSync(MANIFEST)) {
    const manifest = readFileSync(MANIFEST, 'utf8')
    const pattern = /^\s*-\s*\{source:\s*([^,]+),\s*target:\s*([^}]+)\}\s*$/gm
    for (const match of manifest.matchAll(pattern)) entries.set(match[1].trim(), match[2].trim())
  } else if (existsSync(PUBLIC_INVENTORY)) {
    const inventory = JSON.parse(readFileSync(PUBLIC_INVENTORY, 'utf8'))
    if (inventory.schema_version !== 1 || !Array.isArray(inventory.files)) {
      throw new Error('Public inventory must use schema_version 1')
    }
    for (const item of inventory.files) {
      if (typeof item.path === 'string') entries.set(item.path, item.path)
    }
  } else {
    throw new Error('Missing release/public-manifest.yml or public-files.json')
  }
  const selected = {}
  for (const source of SOURCE_PATHS) {
    const target = entries.get(source)
    if (!target || !existsSync(join(ROOT, target))) throw new Error(`Public source is not allowlisted: ${source}`)
    selected[source] = target
  }
  return selected
}

function sourceUrl(repositoryUrl, sourceMap, source, view = 'blob') {
  if (!repositoryUrl) return ''
  const target = sourceMap[source]
  const publicPath = view === 'tree' ? dirname(target) : target
  return `${repositoryUrl.replace(/\/$/, '')}/${view}/main/${publicPath}`
}

function bundledText(root) {
  return readdirSync(root, { withFileTypes: true }).flatMap(item => {
    const path = join(root, item.name)
    if (item.isDirectory()) return bundledText(path)
    if (!statSync(path).isFile() || !/\.(?:html|js|css)$/.test(item.name)) return []
    return [readFileSync(path, 'utf8')]
  }).join('\n')
}

function buildApp({ filter, directory, target, base, env }) {
  const command = process.platform === 'win32' ? 'pnpm.cmd' : 'pnpm'
  const result = spawnSync(command, ['--filter', filter, 'build'], {
    cwd: ROOT,
    env: { ...process.env, CI: process.env.CI || 'true', ...env, BASE_URL: base },
    stdio: 'inherit',
  })
  if (result.status !== 0) throw new Error(`Pages build failed for ${filter}`)
  const source = join(ROOT, directory, 'dist')
  if (!existsSync(join(source, 'index.html'))) throw new Error(`Missing build output: ${relative(ROOT, source)}`)
  const destination = target ? join(OUTPUT, target) : OUTPUT
  mkdirSync(destination, { recursive: true })
  cpSync(source, destination, { recursive: true })
}

export function buildPagesArtifact(options = process.env) {
  const base = normalizeBase(options.BASE_URL || '/')
  const repositoryUrl = options.GITHUB_REPO_URL || ''
  const evaluationUrl = options.EVALUATION_LAB_URL || ''
  const sourceMap = readPublicPathMap()
  const shared = {
    VITE_GITHUB_REPO_URL: repositoryUrl,
    VITE_EVALUATION_LAB_URL: evaluationUrl,
  }

  rmSync(OUTPUT, { recursive: true, force: true })
  buildApp({
    filter: '@portfolio/portfolio-web',
    directory: 'apps/portfolio-web',
    target: '',
    base,
    env: {
      ...shared,
      VITE_QUALITY_DEMO_URL: `${base}quality-agent/`,
      VITE_CONTRACT_CONSOLE_URL: `${base}contract-console/`,
      VITE_RAG_CONSOLE_URL: `${base}rag-console/`,
      VITE_PUBLIC_SOURCE_MAP_JSON: JSON.stringify(sourceMap),
      VITE_PUBLIC_RESUME_URL: options.PUBLIC_RESUME_URL || '',
      VITE_PUBLIC_CONTACT_EMAIL: options.PUBLIC_CONTACT_EMAIL || '',
    },
  })
  buildApp({
    filter: '@portfolio/quality-agent-web',
    directory: 'apps/quality-agent-web',
    target: 'quality-agent',
    base: `${base}quality-agent/`,
    env: {
      ...shared,
      VITE_API_URL: options.QUALITY_API_URL || '',
      VITE_PORTFOLIO_URL: `${base}#/project/quality`,
      VITE_PUBLIC_SOURCE_URL: sourceUrl(repositoryUrl, sourceMap, 'projects/quality_anomaly_agent/README.md', 'tree'),
    },
  })
  buildApp({
    filter: '@portfolio/contract-console',
    directory: 'apps/contract-console',
    target: 'contract-console',
    base: `${base}contract-console/`,
    env: {
      ...shared,
      VITE_PORTFOLIO_URL: `${base}#/project/contract`,
      VITE_PUBLIC_SOURCE_URL: sourceUrl(repositoryUrl, sourceMap, 'projects/contract-review-agent/README.md', 'tree'),
    },
  })
  buildApp({
    filter: '@portfolio/rag-console',
    directory: 'apps/rag-console',
    target: 'rag-console',
    base: `${base}rag-console/`,
    env: {
      ...shared,
      VITE_PORTFOLIO_URL: `${base}#/project/rag`,
      VITE_PUBLIC_SOURCE_URL: sourceUrl(repositoryUrl, sourceMap, 'projects/enterprise-rag-assistant/README.md', 'tree'),
    },
  })

  for (const path of ['index.html', 'quality-agent/index.html', 'contract-console/index.html', 'rag-console/index.html']) {
    if (!existsSync(join(OUTPUT, path))) throw new Error(`Pages artifact is missing ${path}`)
  }
  const bundle = bundledText(OUTPUT)
  if (bundle.includes('http://localhost') || bundle.includes('http://127.0.0.1')) {
    throw new Error('Pages artifact contains a local-only URL')
  }
  if (!options.QUALITY_API_URL && !bundle.includes('公网 API 部署中')) {
    throw new Error('Pages artifact must disclose that the quality API is not deployed')
  }
  if (!options.EVALUATION_LAB_URL && !bundle.includes('Evaluation Lab 部署中')) {
    throw new Error('Pages artifact must disclose that Evaluation Lab is not deployed')
  }
  return { base, output: OUTPUT, sourceMap }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const result = buildPagesArtifact()
  console.log(`Pages artifact ready: ${result.output} (base ${result.base})`)
}
