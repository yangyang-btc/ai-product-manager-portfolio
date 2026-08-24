import { Fragment, useEffect } from 'react'

import { Breadcrumb, CONTRACT_CONSOLE_URL, EVALUATION_LAB_URL, GITHUB_REPO_URL, PageFrame, ProjectCard, PUBLIC_CONTACT_EMAIL, PUBLIC_RESUME_URL, QUALITY_DEMO_URL, RAG_CONSOLE_URL, SectionTitle, publicSourceUrl } from './components'
import { CAPABILITIES, METHODS, PROJECTS, SKILLS, type ProjectKey } from './content'
import { RESEARCH_ARTICLES, type ResearchArticle, type ResearchBlock } from './research'

function ExternalAction({ href, label, pendingLabel, className }: { href: string; label: string; pendingLabel: string; className: string }) {
  return href
    ? <a className={className} href={href} target="_blank" rel="noreferrer">{label}</a>
    : <span className={`${className} is-disabled`} aria-disabled="true">{pendingLabel}</span>
}

export function HomePage() {
  return <PageFrame>
    <section className="portfolio-hero personal-hero" id="positioning"><div className="hero-index"><span>YANG JIAOJING / PORTFOLIO</span><i /></div><div className="hero-copy"><p className="eyebrow">杨姣静 · AI 产品经理</p><h1>从业务问题，<em>到可验证的 AI 产品。</em></h1><p className="hero-lead">我负责把复杂企业场景拆成清晰的业务对象、能力边界和工作流，再通过评测与人工反馈把方案推进到可交付状态。</p><div className="hero-actions"><a className="button-primary" href="#/projects">查看项目</a><a className="text-link" href={QUALITY_DEMO_URL} target="_blank" rel="noreferrer">体验质量异常分析 Agent ↗</a></div></div><aside className="hero-profile" aria-label="专业方向"><p>FOCUS</p><strong>企业 AI 场景</strong><strong>Agent 与 RAG</strong><strong>评测与交付</strong><span>Business × AI × Delivery</span></aside></section>
    <section className="projects-section"><SectionTitle eyebrow="Selected work" title="代表项目" note="三个项目分别来自质量工程、合同治理和产业知识服务场景。" /><div className="project-grid">{PROJECTS.map(project => <ProjectCard key={project.id} project={project} />)}</div></section>
    <section className="featured-case"><div className="featured-intro"><p className="eyebrow">Featured case / P01</p><h2>质量异常分析 Agent</h2><p>把分散在 QMS、MES、ERP、PLM 与质量文件中的事实，组织成可追溯的原因假设和下一步验证动作。</p><div className="featured-actions"><a className="button-primary" href={QUALITY_DEMO_URL} target="_blank" rel="noreferrer">在线运行 Agent</a><a className="button-light" href="#/project/quality">查看完整项目</a><ExternalAction className="button-light" href={EVALUATION_LAB_URL} label="Evaluation Lab ↗" pendingLabel="Evaluation Lab 部署中" /></div></div><ol className="evidence-chain" aria-label="质量异常分析 Agent 证据链"><li><span>01</span><strong>业务输入</strong><p>异常现象、批次、物料与设备事实</p></li><li><span>02</span><strong>Workflow</strong><p>规则、Tool、RAG 与人工节点协作</p></li><li><span>03</span><strong>Trace</strong><p>节点状态、耗时、警告与证据引用</p></li><li><span>04</span><strong>Evaluation</strong><p>数据集、参数实验、指标与 Bad Case</p></li></ol><p className="truth-note">在线结果来自公开模拟数据，用于展示产品工作流与评测设计，不代表历史生产指标。</p></section>
    <section className="capabilities-section"><SectionTitle eyebrow="AI product capabilities" title="我如何推进一个 AI 产品" note="每项能力都能回到具体项目、交付物和可检查的判断。" /><div className="capabilities-grid">{CAPABILITIES.map(([index,title,description,evidence]) => <article key={index}><span>{index}</span><h3>{title}</h3><p>{description}</p><small>{evidence}</small></article>)}</div></section>
    <section className="capability-map"><div className="capability-thesis"><p className="eyebrow">System boundary</p><h2>让每一种能力，只承担它擅长的判断。</h2></div><div className="capability-rail">{['RULE','TOOL','RAG','LLM','HUMAN'].map((item,index) => <div key={item}><span>{String(index + 1).padStart(2,'0')}</span><strong>{item}</strong></div>)}</div><p>确定性判断交给规则，实时事实交给 Tool，知识依据交给 RAG，语言组织交给模型，责任决策保留给人。</p></section>
    <section className="home-links"><a href="#/methodology"><span>产品方法论</span><strong>从项目中沉淀的六个工作框架</strong><i>→</i></a><a href="#/skills"><span>个人 Skills</span><strong>把高频判断固化为可复用任务模板</strong><i>→</i></a><a href="#/research"><span>产品研究</span><strong>持续记录 Agent、RAG 与企业 AI 治理</strong><i>→</i></a></section>
    <section className="about-strip"><p className="eyebrow">About</p><h2>既做产品判断，也把关键链路实现出来。</h2><p>我关注业务价值，也关心架构边界、Prompt、数据、Trace、评测和交付质量。这里展示的不是概念清单，而是可以继续运行、追问和迭代的项目资产。</p><a className="text-link" href="#/about">了解更多 →</a></section>
  </PageFrame>
}

export function AboutPage() {
  return <PageFrame><section className="page-hero"><Breadcrumb current="关于" /><p className="eyebrow">About Yang Jiaojing</p><h1>连接业务问题、AI 能力与交付闭环。</h1><p>我是一名面向企业场景的 AI 产品经理。工作从定义问题开始：识别业务对象和关键决策，划分人机边界，设计可恢复 Workflow，再用可执行指标判断产品是否值得发布。</p></section><section className="profile-grid"><div><span>01</span><h2>发现问题</h2><p>从用户任务、业务流程、数据条件与风险中筛选真正适合 AI 的场景。</p></div><div><span>02</span><h2>设计系统</h2><p>将 Rule、Tool、RAG、LLM 与 Human 组织成边界清晰的产品能力。</p></div><div><span>03</span><h2>验证结果</h2><p>通过数据集、Trace、Bad Case、参数实验与发布门禁形成评测闭环。</p></div></section><section className="about-detail"><div><p className="eyebrow">Working style</p><h2>从业务定义一直走到可验证交付。</h2></div><p>我的优势不是单独懂某个模型，而是能在业务、产品和技术之间建立清晰的责任边界：什么应该由确定性规则处理，什么需要实时 Tool，什么适合 RAG，模型可以组织什么，以及最终必须由谁确认。</p><div className="contact-actions">{GITHUB_REPO_URL && <a className="button-primary" href={GITHUB_REPO_URL} target="_blank" rel="noreferrer">查看 GitHub</a>}{PUBLIC_RESUME_URL && <a className="button-light" href={PUBLIC_RESUME_URL} target="_blank" rel="noreferrer">查看简历</a>}{PUBLIC_CONTACT_EMAIL && <a className="button-light" href={`mailto:${PUBLIC_CONTACT_EMAIL}`}>联系我</a>}</div></section></PageFrame>
}

export function ProjectsPage() {
  return <PageFrame><section className="page-hero"><Breadcrumb current="项目" /><p className="eyebrow">Project evidence</p><h1>项目不是功能清单，是一组可追问的产品决策。</h1><p>每个案例都按业务问题、架构边界、Workflow、评测、Bad Case 与局限展开。</p></section><section className="projects-index"><div className="project-grid">{PROJECTS.map(project => <ProjectCard key={project.id} project={project} />)}</div></section></PageFrame>
}

export function ProjectPage({ projectId, section }: { projectId: ProjectKey; section?: string }) {
  const project = PROJECTS.find(item => item.id === projectId) || PROJECTS[0]
  const sourceReadme = project.id === 'quality' ? 'projects/quality_anomaly_agent/README.md' : project.id === 'contract' ? 'projects/contract-review-agent/README.md' : 'projects/enterprise-rag-assistant/README.md'
  const sourceUrl = publicSourceUrl(sourceReadme, 'tree')
  const evaluationUrl = EVALUATION_LAB_URL && project.evaluationProjectId ? `${EVALUATION_LAB_URL}?project=${project.evaluationProjectId}` : EVALUATION_LAB_URL
  useEffect(() => { if (section) requestAnimationFrame(() => document.getElementById(section)?.scrollIntoView({ behavior: 'smooth' })) }, [section])
  return <PageFrame>
    <section className={`project-hero project-${project.accent}`}><Breadcrumb current={project.shortTitle} /><div className="project-hero-meta"><span>{project.index}</span><span>{project.domain}</span><span>{project.status}</span></div><h1>{project.title}</h1><p>{project.thesis}</p><div className="role-line"><span>负责范围</span><strong>{project.role}</strong></div><div className="truth-strip"><div><span>项目经验</span><strong>业务问题、角色与方案边界</strong></div><div><span>公开重建</span><strong>脱敏领域模型、工作流与评测规范</strong></div><div><span>演示结果</span><strong>{project.claimLabel}</strong></div></div></section>
    <section className="case-section" id="context"><SectionTitle eyebrow="01 / Context" title="为什么做" /><div className="context-grid">{project.context.map((item,index) => <article key={item}><span>{String(index + 1).padStart(2,'0')}</span><p>{item}</p></article>)}</div><div className="outcome-band"><span>形成结果</span><strong>{project.outcome}</strong></div></section>
    <section className="case-section" id="decision"><SectionTitle eyebrow="02 / Decision boundary" title="能力边界" note="架构不是技术名词的堆叠，而是责任分配。" /><div className="boundary-table">{project.boundaries.map(item => <div key={item.layer}><strong>{item.layer}</strong><p>{item.responsibility}</p></div>)}</div></section>
    <section className="case-section" id="architecture"><SectionTitle eyebrow="03 / Workflow" title="工作流与架构" /><ol className="workflow-list">{project.workflow.map((item,index) => <li key={item}><span>{String(index + 1).padStart(2,'0')}</span><strong>{item}</strong></li>)}</ol></section>
    <section className="case-section" id="evaluation"><SectionTitle eyebrow="04 / Evaluation" title="如何验证" note="指标必须说明评价对象、分母和业务意义。" /><div className="metrics-grid">{project.metrics.map(item => <article key={item.name}><strong>{item.name}</strong><p>{item.meaning}</p></article>)}</div><div className="case-risks"><article><span>BAD CASE</span><p>{project.badCase}</p></article><article><span>LIMITATION</span><p>{project.limitation}</p></article></div></section>
    {project.id === 'quality' ? <section className="project-actions"><div><p className="eyebrow">Runnable project</p><h2>不止看方案，直接运行。</h2></div><div><a className="button-primary" href={QUALITY_DEMO_URL} target="_blank" rel="noreferrer">运行质量 Agent</a><ExternalAction className="button-secondary" href={EVALUATION_LAB_URL} label="打开 Evaluation Lab" pendingLabel="Evaluation Lab 部署中" />{sourceUrl && <a className="button-secondary" href={sourceUrl} target="_blank" rel="noreferrer">查看公开重建源码</a>}<a className="button-secondary" href="#/evidence">查看工程证据</a></div></section> : project.id === 'contract' ? <section className="project-actions local-project-actions"><div><p className="eyebrow">Interactive reconstruction</p><h2>选择模拟合同，走完初审与人工复核。</h2>{project.localCommand && <div className="local-run-command"><span>LOCAL REPRODUCTION</span><code>{project.localCommand}</code></div>}</div><div><a className="button-primary" href={CONTRACT_CONSOLE_URL} target="_blank" rel="noreferrer">打开合同审查操作台</a>{sourceUrl && <a className="button-secondary" href={sourceUrl} target="_blank" rel="noreferrer">查看公开重建源码</a>}<ExternalAction className="button-secondary" href={evaluationUrl} label="查看版本化评测" pendingLabel="Evaluation Lab 部署中" /><a className="button-secondary" href="#/projects">返回全部项目</a></div></section> : <section className="project-actions local-project-actions"><div><p className="eyebrow">Interactive reconstruction</p><h2>输入产业供应问题，查看 Rewrite、路由、证据与权限判断。</h2>{project.localCommand && <div className="local-run-command"><span>LOCAL REPRODUCTION</span><code>{project.localCommand}</code></div>}</div><div><a className="button-primary" href={RAG_CONSOLE_URL} target="_blank" rel="noreferrer">打开企业问答操作台</a>{sourceUrl && <a className="button-secondary" href={sourceUrl} target="_blank" rel="noreferrer">查看公开重建源码</a>}<ExternalAction className="button-secondary" href={evaluationUrl} label="查看版本化评测" pendingLabel="Evaluation Lab 部署中" />{publicSourceUrl('projects/enterprise-rag-assistant/evaluation/latest.json') && <a className="button-secondary" href={publicSourceUrl('projects/enterprise-rag-assistant/evaluation/latest.json')} target="_blank" rel="noreferrer">下载评测 JSON</a>}<a className="button-secondary" href="#/projects">返回全部项目</a></div></section>}
  </PageFrame>
}

export function MethodologyPage() {
  return <PageFrame><section className="page-hero"><Breadcrumb current="方法论" /><p className="eyebrow">Product operating system</p><h1>从项目里长出来的方法，而不是概念目录。</h1><p>每个方法都对应一个作品集案例和一个可以被检查的交付物。</p></section><section className="method-list">{METHODS.map(([index,title,description,evidence]) => <article key={index}><span>{index}</span><div><h2>{title}</h2><p>{description}</p></div><strong>{evidence}</strong></article>)}</section></PageFrame>
}

export function SkillsPage() {
  return <PageFrame><section className="page-hero"><Breadcrumb current="Skills" /><p className="eyebrow">Reusable judgement</p><h1>把高频产品判断，沉淀为可复用 Skill。</h1><p>Skill 不代替思考，它固定输入、检查项、交付格式和风险边界。</p></section><section className="skills-grid">{SKILLS.map(([name,description,evidence],index) => <article key={name}><span>{String(index + 1).padStart(2,'0')}</span><code>{name}</code><p>{description}</p><small>项目引用：{evidence}</small></article>)}</section></PageFrame>
}

function markerLabel(kind: string) {
  return ({ fact: '官方事实', marketing_claim: '厂商主张', judgment: '作者判断', inference: '基于事实的推论' } as Record<string, string>)[kind] || kind
}

function AnnotatedText({ text }: { text: string }) {
  const tokens = text.split(/(https:\/\/[^\s，]+|\[(?:fact|marketing_claim|judgment|inference)(?::[^\]]+)?\])/g)
  return <>{tokens.map((token, index) => {
    if (token.startsWith('https://')) return <a key={`${token}-${index}`} href={token} target="_blank" rel="noreferrer">{token}</a>
    const marker = token.match(/^\[(fact|marketing_claim|judgment|inference)(?::([^\]]+))?\]$/)
    if (!marker) return <Fragment key={index}>{token}</Fragment>
    return <span key={`${token}-${index}`} className={`research-marker marker-${marker[1]}`} title={marker[2] ? `来源：${marker[2]}` : markerLabel(marker[1])}>{markerLabel(marker[1])}</span>
  })}</>
}

function ResearchBlocks({ blocks }: { blocks: ResearchBlock[] }) {
  return <>{blocks.map((block, index) => block.type === 'list' ? <ul key={index}>{block.items?.map(item => <li key={item}><AnnotatedText text={item} /></li>)}</ul> : <p key={index}><AnnotatedText text={block.text || ''} /></p>)}</>
}

function ResearchCard({ article, index }: { article: ResearchArticle; index: number }) {
  return <article className="research-card"><header><span>{String(index + 1).padStart(2, '0')}</span><small>{article.product} / {article.vendor}</small></header><div><p className="research-status">{article.readingMinutes} 分钟阅读 · 更新于 {article.updatedAt}</p><h2>{article.title}</h2><p>{article.coreJudgment}</p></div><footer><div>{article.tags.map(tag => <span key={tag}>{tag}</span>)}</div><a href={`#/research/${article.slug}`}>阅读完整拆解 <i>→</i></a></footer></article>
}

export function ResearchPage() {
  return <PageFrame><section className="page-hero research-index-hero"><Breadcrumb current="产品研究" /><p className="eyebrow">Product research</p><h1>不止列功能，追问 AI 产品怎样被信任。</h1><p>每篇拆解都从用户任务出发，追踪 Context、Tool、权限与评测，并把官方事实、厂商主张、作者判断和推论分开。</p></section><section className="research-grid">{RESEARCH_ARTICLES.map((article, index) => <ResearchCard key={article.slug} article={article} index={index} />)}</section><section className="research-principle"><p className="eyebrow">Research principle</p><h2>每次拆解都回答四件事</h2><ol><li>它解决的是哪一个用户任务？</li><li>关键能力与责任边界是什么？</li><li>失败时如何被发现、解释和恢复？</li><li>什么证据足以支持产品发布？</li></ol></section></PageFrame>
}

export function ResearchArticlePage({ article }: { article: ResearchArticle }) {
  useEffect(() => {
    const id = window.location.hash.split('?section=')[1]
    if (id) requestAnimationFrame(() => document.getElementById(id)?.scrollIntoView())
  }, [article.slug])
  const articleSource = publicSourceUrl(`research/${article.slug}/article.md`)
  return <PageFrame><section className="research-article-hero"><Breadcrumb current={article.product} /><div className="research-product-line"><span>{article.product}</span><i /> <span>{article.vendor}</span></div><h1>{article.title}</h1><p>{article.summary}</p><div className="article-meta"><span>{article.readingMinutes} 分钟阅读</span><span>调研截止 {article.updatedAt}</span><span>{article.sections.length} 个分析维度</span></div></section><section className="research-reading-grid"><aside className="research-toc"><p>ON THIS PAGE</p><nav>{article.sections.map((section, index) => <a key={section.id} href={`#/research/${article.slug}?section=${section.id}`}><span>{String(index + 1).padStart(2, '0')}</span>{section.heading}</a>)}</nav><div className="research-legend"><strong>阅读标尺</strong>{['fact', 'marketing_claim', 'judgment', 'inference'].map(kind => <span key={kind} className={`research-marker marker-${kind}`}>{markerLabel(kind)}</span>)}</div>{articleSource && <a className="research-source-cta" href={articleSource} target="_blank" rel="noreferrer">查看公开重建源文 ↗</a>}</aside><article className="research-article"><div className="research-lead"><ResearchBlocks blocks={article.lead} /></div>{article.sections.map((section, index) => <section key={section.id} id={section.id} className={section.heading === '官方参考资料与调研日期' ? 'source-section' : undefined}><header><span>{String(index + 1).padStart(2, '0')}</span><h2>{section.heading}</h2></header><ResearchBlocks blocks={section.blocks} /></section>)}</article></section><nav className="research-next" aria-label="其他产品研究"><a href="#/research">← 返回全部研究</a>{RESEARCH_ARTICLES.filter(item => item.slug !== article.slug).slice(0, 2).map(item => <a key={item.slug} href={`#/research/${item.slug}`}>{item.product} <span>→</span></a>)}</nav></PageFrame>
}

export function EvidencePage() {
  const groups = [['RUN','质量 Agent 三条路径','标准闭环、信息不足拒答、ERP Tool 超时降级。',QUALITY_DEMO_URL,true],['TRACE','节点执行与隐私安全 Trace','节点状态、耗时、输入输出计数、警告与 Token 估算。',QUALITY_DEMO_URL,true],['EVAL','Evaluation Lab','数据集、参数实验、指标、版本门禁与 Bad Case。',EVALUATION_LAB_URL,true],['TEST','自动化测试','Python 工作流/API/评测测试与 React 交互测试。','#/project/quality/evaluation',false]] as const
  const sourceFiles = [['WORKFLOW','projects/quality_anomaly_agent/workflow.py'],['API','apps/quality_agent_api/main.py'],['REACT','apps/quality-agent-web/src/App.tsx'],['TEST','tests/test_quality_agent_api.py']] as const
  return <PageFrame><section className="page-hero"><Breadcrumb current="工程证据" /><p className="eyebrow">Runnable proof</p><h1>从页面一路追到运行、Trace、评测与测试。</h1><p>公开模式固定使用模拟数据和离线模型；真实模型模式仅用于本地配置。</p></section><section className="evidence-index">{groups.map(([type,title,description,href,external]) => href ? <a key={type} href={href} target={external ? '_blank' : undefined} rel={external ? 'noreferrer' : undefined}><span>{type}</span><div><h2>{title}</h2><p>{description}</p></div><i>→</i></a> : <article key={type} className="is-disabled" aria-disabled="true"><span>{type}</span><div><h2>{title}</h2><p>{description} 公网版本部署中。</p></div><i>—</i></article>)}</section><section className="test-summary"><div><strong>32</strong><span>Python tests</span></div><div><strong>08</strong><span>React tests</span></div><div><strong>03</strong><span>Runnable projects</span></div><p>测试数字是当前公开重建代码的自动化测试数量，不是历史生产项目指标。</p></section><section className="source-index"><SectionTitle eyebrow="Source map" title="关键代码从哪里看" />{sourceFiles.map(([label,path]) => publicSourceUrl(path) ? <a key={path} href={publicSourceUrl(path)} target="_blank" rel="noreferrer" aria-label={`查看公开重建源码：${label}`}><span>{label}</span><code>{path}</code><i>↗</i></a> : <article key={path}><span>{label}</span><code>{path}</code></article>)}</section></PageFrame>
}

export function NotFoundPage() {
  return <PageFrame><section className="page-hero"><p className="eyebrow">404 / Route not found</p><h1>这个页面还不存在。</h1><p>返回首页继续查看杨姣静的项目、方法论与产品研究。</p><a className="button-primary inline-button" href="#/">返回作品集</a></section></PageFrame>
}
