# 杨姣静 · AI 产品经理作品集

这个仓库展示我在企业 AI 场景中的项目实践、产品方法与可运行作品，重点关注 Agent、RAG、Workflow、评测和人机责任边界。

作品集网站通过 GitHub Pages 发布，首页是个人介绍与项目入口；代码仓库承载可运行 Demo、领域模型、模拟数据、评测规范和自动化测试。

## 代表项目

### 1. 半导体设备质量异常分析 Agent

将 QMS、MES、ERP、PLM 的业务事实与 SOP、FMEA、8D、历史案例组织成可审计证据，输出待质量工程师验证的原因假设和行动建议。

- FastAPI + React + 状态化 Workflow
- 标准闭环、信息不足拒答、Tool 超时降级
- 隐私安全 Trace、Run Bundle、人工确认节点
- Evaluation Lab：数据集、参数实验、指标、Bad Case 与发布门禁
- 默认离线模拟，可选本地 OpenAI-compatible 模型

### 2. 半导体设备企业合同审查 Agent

围绕零部件采购、设备销售、NDA 和联合技术开发，设计 Router + Rule + RAG + LLM + Human 的混合审查流程。

- 条款结构、跨条款关系与业务上下文
- 可解释风险卡片、规则版本和原文定位
- 六个版本化模拟案例，可在浏览器中运行并进入人工复核
- Trace、脱敏 Run Bundle v2 与 Python/TypeScript 一致性测试
- 关键风险召回、误报、依据完整性与人工拦截评测
- 公开重建的模拟合同、领域模型和场景目录

### 3. 产业供应链企业 AI 智能问答助手

面向集团运营、BD 和业务团队，将产业知识问答与询价、报价、订单、物流等实时任务分开路由。

- 行业术语治理、Query Rewrite 与分层意图
- Hybrid RAG、引用校验、澄清与无证据拒答
- 静态知识 / 实时 Tool / 复合任务边界
- 十个版本化案例，可在浏览器中查看 Rewrite、路由、证据、权限与 Trace
- Python / TypeScript Runtime 黄金用例一致性测试
- 公开重建的供应关系、工艺流程和业务事件数据

## 产品研究

首批四篇研究围绕 AI 产品的任务边界、Context、Tool、权限与评测展开：

- Codex：从代码生成工具到多 Agent 工程工作台
- WorkBuddy：AI 办公产品如何从回答问题走向交付成果
- Claude Code：终端原生 Agent 如何设计上下文、权限与自主性
- Cursor：AI 编程产品如何设计“自主性滑杆”

每篇文章都就近标注官方事实、厂商主张、作者判断和基于事实的推论，并维护独立的官方来源清单。

## 本地运行

```bash
uv sync --dev
pnpm install

# 个人作品集网站
pnpm --filter @portfolio/portfolio-web dev

# 合同审查在线操作台
pnpm --filter @portfolio/contract-console dev

# 企业智能问答在线操作台
pnpm --filter @portfolio/rag-console dev

# 质量 Agent API / React 界面 / Evaluation Lab
uv run uvicorn apps.quality_agent_api.main:app --reload --port 8000
pnpm --filter @portfolio/quality-agent-web dev
EVALUATION_LAB_MODE=local uv run python -m streamlit run apps/evaluation_lab/app.py
```

也可以直接运行离线示例：

```bash
uv run python -m apps.quality_agent_api.demo --case incoming_material_001
uv run python -m projects.contract_review_agent.demo --case procurement_contract_001
uv run python -m projects.enterprise_rag_assistant.demo --case compound_query_001
uv run python -m apps.evaluation_lab.demo
```

## 验证

```bash
make lint
make test
make verify-research
BASE_URL=/ai-product-manager-portfolio/ make build-pages
```

公开案例使用重新生成的模拟数据，不包含前公司身份、真实合同、客户/供应商信息、内部接口或生产代码。在线演示结果仅代表公开数据集上的本次运行，不代表历史生产指标。
