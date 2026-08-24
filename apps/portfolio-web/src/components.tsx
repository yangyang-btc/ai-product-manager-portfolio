import type { ReactNode } from 'react'

import type { ProjectRecord } from './content'

export const QUALITY_DEMO_URL = import.meta.env.VITE_QUALITY_DEMO_URL || (import.meta.env.DEV ? 'http://localhost:5173' : '')
export const CONTRACT_CONSOLE_URL = import.meta.env.VITE_CONTRACT_CONSOLE_URL || (import.meta.env.DEV ? 'http://localhost:5174' : '')
export const RAG_CONSOLE_URL = import.meta.env.VITE_RAG_CONSOLE_URL || (import.meta.env.DEV ? 'http://localhost:5175' : '')
export const EVALUATION_LAB_URL = import.meta.env.VITE_EVALUATION_LAB_URL || (import.meta.env.DEV ? 'http://localhost:8501' : '')
export const GITHUB_REPO_URL = import.meta.env.VITE_GITHUB_REPO_URL || ''
export const PUBLIC_RESUME_URL = import.meta.env.VITE_PUBLIC_RESUME_URL || ''
export const PUBLIC_CONTACT_EMAIL = import.meta.env.VITE_PUBLIC_CONTACT_EMAIL || ''

const PUBLIC_SOURCE_PATHS = (() => {
  try {
    return JSON.parse(import.meta.env.VITE_PUBLIC_SOURCE_MAP_JSON || '{}') as Record<string, string>
  } catch {
    return {}
  }
})()

export function publicSourceUrl(sourcePath: string, view: 'blob' | 'tree' = 'blob') {
  const target = PUBLIC_SOURCE_PATHS[sourcePath]
  if (!GITHUB_REPO_URL || !target) return ''
  const publicPath = view === 'tree' ? target.split('/').slice(0, -1).join('/') : target
  return `${GITHUB_REPO_URL}/${view}/main/${publicPath}`
}

const NAV_ITEMS = [['项目', '/projects'], ['方法论', '/methodology'], ['Skills', '/skills'], ['产品研究', '/research'], ['关于', '/about']] as const

function isActiveNav(href: string) {
  const route = window.location.hash.replace(/^#/, '') || '/'
  return route === href || (href === '/projects' && route.startsWith('/project/'))
}

export function SiteHeader() {
  return <header className="site-header"><a className="identity" href="#/"><strong>杨姣静</strong><span>AI PRODUCT MANAGER</span></a><nav aria-label="主要导航">{NAV_ITEMS.map(([label, href]) => <a key={href} href={`#${href}`} aria-current={isActiveNav(href) ? 'page' : undefined}>{label}</a>)}</nav></header>
}

export function SiteFooter() {
  return <footer className="site-footer"><div><strong>杨姣静 · AI 产品经理</strong><p>企业 AI 场景、Agent / RAG 产品设计与评测交付。</p></div><div className="footer-links"><a href="#/projects">项目</a><a href="#/methodology">方法论</a><a href="#/research">产品研究</a>{GITHUB_REPO_URL && <a href={GITHUB_REPO_URL} target="_blank" rel="noreferrer">GitHub ↗</a>}{PUBLIC_RESUME_URL && <a href={PUBLIC_RESUME_URL} target="_blank" rel="noreferrer">简历 ↗</a>}{PUBLIC_CONTACT_EMAIL && <a href={`mailto:${PUBLIC_CONTACT_EMAIL}`}>联系我</a>}</div><p className="public-note">公开案例基于真实项目经验重建；公司身份、业务数据、接口与代码均已隐去或使用模拟版本。</p></footer>
}

export function PageFrame({ children }: { children: ReactNode }) {
  return <div className="portfolio-shell"><SiteHeader /><main>{children}</main><SiteFooter /></div>
}

export function ProjectCard({ project }: { project: ProjectRecord }) {
  return <article className={`project-card accent-${project.accent}`} data-testid={`project-card-${project.id}`}><header><span>{project.index}</span><small>{project.status}</small></header><p className="project-domain">{project.domain}</p><h3>{project.shortTitle}</h3><dl className="project-facts"><div><dt>业务问题</dt><dd>{project.problem}</dd></div><div><dt>负责范围</dt><dd>{project.role}</dd></div><div><dt>形成结果</dt><dd>{project.outcome}</dd></div></dl><p className="claim-label">{project.claimLabel}</p><a href={`#/project/${project.id}`}>查看项目详情 <span>→</span></a></article>
}

export function Breadcrumb({ current }: { current: string }) {
  return <nav className="breadcrumb" aria-label="面包屑"><a href="#/">作品集</a><span>/</span><span>{current}</span></nav>
}

export function SectionTitle({ eyebrow, title, note }: { eyebrow: string; title: string; note?: string }) {
  return <div className="section-title"><div><p className="eyebrow">{eyebrow}</p><h2>{title}</h2></div>{note && <p>{note}</p>}</div>
}
