# 杨姣静 · AI 产品经理作品集网站

GitHub Pages 入口围绕个人定位、代表项目、产品能力、方法论、Skills、产品研究与关于页面展开。

三个项目详情页统一展示业务问题、负责范围、能力边界、Workflow、评测、Bad Case 与局限。
质量异常分析 Agent 提供在线 Demo 和 Evaluation Lab；合同审查与企业智能问答项目均提供
在线案例操作台、可本地复现的 Workflow，以及符合业务场景的模拟数据和评测资料。

Local preview:

```bash
pnpm --filter @portfolio/portfolio-web dev
```

Deployment URLs are configured through `VITE_QUALITY_DEMO_URL`,
`VITE_CONTRACT_CONSOLE_URL`, `VITE_RAG_CONSOLE_URL`, `VITE_EVALUATION_LAB_URL`, and `VITE_GITHUB_REPO_URL`. Optional public resume and contact links use
`VITE_PUBLIC_RESUME_URL` and `VITE_PUBLIC_CONTACT_EMAIL`. Hash routes keep project and content views
compatible with GitHub Pages without server rewrites.
