import claudeArticle from '../../../research/claude-code/article.md?raw'
import codexArticle from '../../../research/codex/article.md?raw'
import cursorArticle from '../../../research/cursor/article.md?raw'
import researchIndex from '../../../research/index.yml?raw'
import workbuddyArticle from '../../../research/workbuddy/article.md?raw'

export type ResearchSlug = 'codex' | 'workbuddy' | 'claude-code' | 'cursor'

export interface ResearchBlock {
  type: 'paragraph' | 'list'
  text?: string
  items?: string[]
}

export interface ResearchSection {
  id: string
  heading: string
  blocks: ResearchBlock[]
}

export interface ResearchArticle {
  slug: ResearchSlug
  product: string
  vendor: string
  title: string
  summary: string
  tags: string[]
  readingMinutes: number
  updatedAt: string
  lead: ResearchBlock[]
  sections: ResearchSection[]
  coreJudgment: string
}

interface ResearchMetadata {
  slug: ResearchSlug
  product: string
  vendor: string
  title: string
  summary: string
  tags: string[]
  readingMinutes: number
  updatedAt: string
}

const ARTICLE_FILES: Record<ResearchSlug, string> = {
  codex: codexArticle,
  workbuddy: workbuddyArticle,
  'claude-code': claudeArticle,
  cursor: cursorArticle,
}

function valueAfterColon(line: string) {
  const value = line.slice(line.indexOf(':') + 1).trim()
  return value.replace(/^['"]|['"]$/g, '')
}

function parseIndex(raw: string): ResearchMetadata[] {
  return raw.split(/\n(?=  - slug: )/).slice(1).map(block => {
    const lines = block.split('\n').map(line => line.trim()).filter(Boolean)
    const values = Object.fromEntries(lines.map(line => [line.slice(0, line.indexOf(':')), valueAfterColon(line)]))
    const slug = values['- slug'] as ResearchSlug
    if (!ARTICLE_FILES[slug]) throw new Error(`Unknown research slug: ${slug}`)
    return {
      slug,
      product: values.product,
      vendor: values.vendor,
      title: values.title,
      summary: values.summary,
      tags: values.tags.replace(/^\[|\]$/g, '').split(',').map(tag => tag.trim()),
      readingMinutes: Number(values.reading_minutes),
      updatedAt: values.updated_at,
    }
  })
}

function sectionId(index: number) {
  return `research-section-${String(index + 1).padStart(2, '0')}`
}

function parseBlocks(lines: string[]): ResearchBlock[] {
  const blocks: ResearchBlock[] = []
  let list: string[] = []
  const flushList = () => {
    if (list.length) blocks.push({ type: 'list', items: list })
    list = []
  }
  lines.forEach(line => {
    const value = line.trim()
    if (!value) return
    if (value.startsWith('- ')) {
      list.push(value.slice(2))
      return
    }
    flushList()
    blocks.push({ type: 'paragraph', text: value })
  })
  flushList()
  return blocks
}

function stripMarkers(text: string) {
  return text.replace(/\[(?:fact|marketing_claim|judgment|inference)(?::[^\]]+)?\]/g, '').trim()
}

function parseArticle(metadata: ResearchMetadata, raw: string): ResearchArticle {
  const lines = raw.split('\n')
  const leadLines: string[] = []
  const sectionLines: Array<{ heading: string; lines: string[] }> = []
  let current: { heading: string; lines: string[] } | undefined

  lines.slice(1).forEach(line => {
    if (line.startsWith('## ')) {
      current = { heading: line.slice(3).trim(), lines: [] }
      sectionLines.push(current)
    } else if (current) {
      current.lines.push(line)
    } else {
      leadLines.push(line)
    }
  })

  const sections = sectionLines.map((section, index) => ({
    id: sectionId(index),
    heading: section.heading,
    blocks: parseBlocks(section.lines),
  }))
  const judgment = sections.find(section => section.heading === '一句话判断')?.blocks.find(block => block.type === 'paragraph')?.text || metadata.summary

  return {
    ...metadata,
    lead: parseBlocks(leadLines),
    sections,
    coreJudgment: stripMarkers(judgment),
  }
}

export const RESEARCH_ARTICLES = parseIndex(researchIndex).map(metadata => parseArticle(metadata, ARTICLE_FILES[metadata.slug]))

export function getResearchArticle(slug: string) {
  return RESEARCH_ARTICLES.find(article => article.slug === slug)
}
