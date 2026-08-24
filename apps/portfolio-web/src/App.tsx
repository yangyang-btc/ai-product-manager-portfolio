import { useEffect, useState } from 'react'

import type { ProjectKey } from './content'
import { AboutPage, EvidencePage, HomePage, MethodologyPage, NotFoundPage, ProjectPage, ProjectsPage, ResearchArticlePage, ResearchPage, SkillsPage } from './pages'
import { getResearchArticle } from './research'

function currentRoute() {
  return window.location.hash.replace(/^#/, '') || '/'
}

export default function App() {
  const [route, setRoute] = useState(currentRoute)
  useEffect(() => {
    const update = () => { setRoute(currentRoute()); window.scrollTo({ top: 0 }) }
    window.addEventListener('hashchange', update)
    return () => window.removeEventListener('hashchange', update)
  }, [])

  useEffect(() => {
    const labels: Record<string, string> = { '/': '杨姣静｜AI 产品经理', '/projects': '项目｜杨姣静', '/methodology': '产品方法论｜杨姣静', '/skills': '个人 Skills｜杨姣静', '/research': '产品研究｜杨姣静', '/about': '关于｜杨姣静', '/evidence': '质量 Agent 工程证据｜杨姣静' }
    const researchSlug = route.match(/^\/research\/([^?]+)/)?.[1]
    const researchTitle = researchSlug ? getResearchArticle(researchSlug)?.product : undefined
    document.title = researchTitle ? `${researchTitle} 产品拆解｜杨姣静` : labels[route] || (route.startsWith('/project/') ? 'AI 产品项目｜杨姣静' : '杨姣静｜AI 产品经理')
  }, [route])

  if (route === '/') return <HomePage />
  if (route === '/profile' || route === '/about') return <AboutPage />
  if (route === '/projects') return <ProjectsPage />
  if (route === '/methodology') return <MethodologyPage />
  if (route === '/skills') return <SkillsPage />
  if (route === '/research') return <ResearchPage />
  if (route === '/evidence') return <EvidencePage />
  const match = route.match(/^\/project\/(quality|contract|rag)(?:\/(context|decision|architecture|evaluation))?$/)
  if (match) return <ProjectPage projectId={match[1] as ProjectKey} section={match[2]} />
  const researchMatch = route.match(/^\/research\/([^?]+)(?:\?.*)?$/)
  const article = researchMatch ? getResearchArticle(researchMatch[1]) : undefined
  if (article) return <ResearchArticlePage article={article} />
  return <NotFoundPage />
}
