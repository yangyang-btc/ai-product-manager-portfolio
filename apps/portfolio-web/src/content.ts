export type ProjectKey = 'quality' | 'contract' | 'rag'

export interface ProjectRecord {
  id: ProjectKey
  index: string
  title: string
  shortTitle: string
  domain: string
  users: string
  problem: string
  role: string
  thesis: string
  outcome: string
  status: string
  claimLabel: string
  accent: 'blue' | 'amber' | 'teal'
  context: string[]
  boundaries: Array<{ layer: string; responsibility: string }>
  workflow: string[]
  metrics: Array<{ name: string; meaning: string }>
  badCase: string
  limitation: string
  localCommand?: string
  evaluationProjectId?: string
}

export const PROJECTS: ProjectRecord[] = [
  {
    id: 'quality', index: 'P01', title: '半导体设备质量异常分析 Agent', shortTitle: '质量异常分析 Agent',
    domain: '半导体设备 · 质量工程', users: '质量工程师 / 研发 / 工艺 / 生产',
    problem: '质量异常事实分散在业务系统和质量知识文件中，人工排查慢，结论也难追溯。',
    role: '场景选择 / 业务建模 / Workflow / Schema / 评测设计',
    thesis: '把跨系统事实组织成可验证的原因方向，而不是让模型直接猜根因。',
    outcome: '形成从跨系统取证、知识检索、假设生成到人工验证的完整分析闭环。',
    status: '可在线体验', claimLabel: '公开重建 · 模拟数据', accent: 'blue',
    context: ['质量异常分散在 QMS、MES、ERP、PLM 以及 SOP、FMEA、8D 和历史案例中。', '核心用户为质量工程师，研发、工艺和生产角色参与验证。', '公开 Demo 覆盖标准、信息不足和 Tool 超时三类可观察路径。'],
    boundaries: [
      { layer: 'Rule', responsibility: '阈值、版本、生效状态与输出 Schema 校验' },
      { layer: 'Tool', responsibility: '查询 QMS / MES / ERP / PLM 当前业务事实' },
      { layer: 'RAG', responsibility: '检索 SOP / FMEA / 8D / 历史案例依据' },
      { layer: 'LLM', responsibility: '组织包含正反证与缺失信息的原因假设矩阵' },
      { layer: 'Human', responsibility: '验证原因、确认处置并承担最终质量判断' },
    ],
    workflow: ['接收异常', '校验案例', '识别场景', '规划查询', '跨系统取证', '检索知识', '构建证据图', '生成假设', '证据校验', '人工决策'],
    metrics: [
      { name: 'Schema 合规率', meaning: '输出能否被下游稳定消费' }, { name: '引用可解析率', meaning: '每条假设能否返回具体证据' },
      { name: '无依据结论率', meaning: 'Agent 是否越权输出确定性根因' }, { name: '反证覆盖率', meaning: '是否主动呈现与假设冲突的事实' },
      { name: '人工边界准确率', meaning: '处置决策是否保留给质量角色' },
    ],
    badCase: '历史相似案例与当前批次事实同时出现时，相关性容易被误写成因果。修复方式是强制绑定支持证据、反证、缺失信息和下一步验证动作。',
    limitation: '公开版本使用模拟系统、模拟数据和确定性离线模型；不代表原企业生产系统，也不替代质量工程师的最终判断。',
  },
  {
    id: 'contract', index: 'P02', title: '半导体设备企业合同审查 Agent', shortTitle: '合同审查 Agent',
    domain: '半导体设备 · 合同治理', users: '采购 / 商务 / 法务 / 技术项目团队',
    problem: '采购、销售与技术合作合同类型复杂，初审标准分散，高风险条款依赖人工经验。',
    role: '业务流程 / 混合架构 / 风险卡片 / HITL / 指标体系',
    thesis: '规则负责确定性风险，RAG 提供依据，大模型判断语义风险，高风险必须人工复核。',
    outcome: '将采购、商务、NDA 与技术合作协议的初审过程沉淀为可解释风险卡片。',
    status: '可在线体验 + 支持本地运行', claimLabel: '公开重建 · 模拟合同', accent: 'amber',
    localCommand: 'uv run python -m projects.contract_review_agent.demo --case procurement_contract_001',
    evaluationProjectId: 'contract-review-agent',
    context: ['合同类型覆盖零部件采购、设备销售、NDA 与联合技术开发。', '业务条款涉及来料检验、FAT/SAT、安装调试、质保、知识产权与责任边界。', '输出嵌入 OA 初审与法务复核协作，不替代最终法律判断。'],
    boundaries: [
      { layer: 'Router', responsibility: '识别合同类型、条款结构与适用审查策略' }, { layer: 'Rule', responsibility: '必审项、缺失条款、数值与结构完整性校验' },
      { layer: 'RAG', responsibility: '返回制度、规则、案例及明确版本' }, { layer: 'LLM', responsibility: '识别跨条款语义冲突并生成修改建议' },
      { layer: 'Human', responsibility: '复核高风险项并做出最终法律判断' },
    ],
    workflow: ['文档解析', '类型路由', '章节切分', '必审规则', '知识检索', '语义风险', '跨条款检查', '风险分级', '人工复核'],
    metrics: [{ name: '关键风险召回率', meaning: '必须发现的风险是否被覆盖' }, { name: '误报率', meaning: '低价值提醒是否占用法务时间' }, { name: '无依据判断率', meaning: '风险结论是否具备规则或案例依据' }, { name: '高风险人工拦截率', meaning: '系统是否守住法律责任边界' }],
    badCase: '关键责任条款可能因章节切分或 Top-K 检索没有进入模型上下文。产品上不能把“未检索到”解释为“没有风险”。',
    limitation: '公开案例不提供法律意见；合同、条款、主体和制度均为符合半导体设备业务结构的模拟版本。',
  },
  {
    id: 'rag', index: 'P03', title: '产业供应链企业 AI 智能问答助手', shortTitle: '企业 AI 智能问答助手',
    domain: '产业供应链 · B2B 知识服务', users: '集团运营 / BD / 业务团队 / 新员工',
    problem: '产业知识与实时履约信息分散，术语不统一，不同角色需要在权限范围内快速获得可信答案。',
    role: '意图体系 / 术语治理 / Query Rewrite / Hybrid RAG / 输出设计',
    thesis: '先判断问题应该查知识还是查实时系统，再决定如何改写、检索和回答。',
    outcome: '形成从 Query 预处理、分层意图路由到多形态答案返回的企业问答链路。',
    status: '可在线体验 + 支持本地运行', claimLabel: '公开重建 · 模拟语料', accent: 'teal',
    localCommand: 'uv run python -m projects.enterprise_rag_assistant.demo --case compound_query_001',
    evaluationProjectId: 'enterprise-rag-assistant',
    context: ['产业知识分散在供应链合同、制造工艺文件、商品资料、培训材料与业务系统中。', '核心用户包含集团运营、BD 与新员工，不同角色拥有不同的数据权限。', '企业、供应商、物料、供应关系、工艺流程、订单与履约事件构成统一业务对象。'],
    boundaries: [
      { layer: 'Normalize', responsibility: '行业术语、别名、缩写与标准名称归一' }, { layer: 'Intent', responsibility: '分层意图识别与任务路由' },
      { layer: 'RAG', responsibility: '回答稳定的产业知识并提供引用' }, { layer: 'Tool', responsibility: '查询询价、报价、订单和物流等实时事实' },
      { layer: 'Guardrail', responsibility: '低置信澄清、无证据拒答与权限控制' },
    ],
    workflow: ['Query 预处理', '术语归一', '问题改写', '意图识别', '静态/实时分流', '混合检索', '重排', '引用校验', '结果返回'],
    metrics: [{ name: '意图准确率', meaning: '问题是否进入正确任务链路' }, { name: 'Hit@K / MRR / nDCG', meaning: '检索覆盖与排序质量' }, { name: '引用与忠实度', meaning: '答案是否忠于可解析证据' }, { name: '拒答 / 澄清准确率', meaning: '信息不足时是否停止猜测' }, { name: '权限命中率', meaning: '用户是否只看到允许的数据' }],
    badCase: '询价、报价、订单或物流问题被静态知识库误答，本质不是 Prompt 问题，而是任务路由与数据源边界错误。',
    limitation: '公开案例只展示脱敏对象关系与模拟语料；实时业务事实必须由授权 Tool 查询，不能由知识库生成。',
  },
]

export const CAPABILITIES = [
  ['01', '业务场景判断', '从任务价值、频率、风险和数据条件判断应该使用规则、RAG、Agent，还是不做 AI。', '三个项目的场景选择与能力边界'],
  ['02', '业务对象建模', '把异常、合同、供应商、物料、订单和知识依据转成可计算、可追溯的对象关系。', '质量证据图 / 合同风险卡 / 产业对象模型'],
  ['03', 'Agent Workflow', '显式设计状态、节点、条件分支、补查循环、人工中断、恢复与失败降级。', '质量 Agent 十节点闭环'],
  ['04', 'RAG 与检索', '设计语料治理、Query Rewrite、混合检索、重排、引用校验与无证据拒答。', '合同审查 / 企业智能问答'],
  ['05', '评测与 Bad Case', '把数据集、参数、Trace、指标、错误归因和版本门禁绑定成可复现的评测运行。', 'Evaluation Lab / 三类运行案例'],
  ['06', '交付与治理', '把权限、隐私、成本、延迟和人机责任边界放进产品方案与验收标准。', 'HITL / Guardrail / 发布门禁'],
] as const

export const METHODS = [
  ['01', '场景判断', '先验证任务价值、频率、风险和数据条件，再决定是否需要 Agent。', '质量异常 / 合同初审 / 企业问答'],
  ['02', '能力边界', '把确定性、实时性、知识性、生成性和责任性判断分配给正确组件。', 'Rule / Tool / RAG / LLM / Human'],
  ['03', 'Workflow 设计', '显式定义状态、条件分支、补查循环、人工中断、恢复和失败降级。', 'LangGraph 状态机'],
  ['04', 'Context Engineering', '控制模型看到的字段、证据数量、版本与引用，而不是堆满上下文。', 'Query / Top-K / Schema'],
  ['05', '评测闭环', '数据集、配置、Trace、指标和版本门禁必须绑定为一次可复现运行。', 'Dataset → Run → Gate'],
  ['06', '风险治理', '同时管理权限、隐私、Token、成本、延迟、幻觉和人机责任边界。', 'Guardrail / HITL'],
] as const

export const SKILLS = [
  ['ai-scene-assessment', '判断业务问题是否适合 AI、RAG、Agent 或传统自动化。', '质量项目：异常分析任务边界'],
  ['agent-workflow-designer', '把业务流程拆成状态、节点、条件、Tool 与人工检查点。', '质量项目：十节点 Workflow'],
  ['rag-evaluation-planner', '设计检索数据集、指标、参数实验与版本门禁。', 'Evaluation Lab：Top-K 实验'],
  ['bad-case-analyzer', '将失败归因到数据、Tool、检索、规则、Prompt、模型或流程。', '无证据与 ERP 超时案例'],
  ['prompt-schema-reviewer', '检查 Prompt 与输出 Schema 的证据约束和下游可消费性。', '假设矩阵 Schema'],
  ['token-cost-reviewer', '评估上下文预算、Top-K 成本、超时与 Kill Switch。', '评测实验：质量与 Token 权衡'],
] as const
