# 产业供应链企业 AI 智能问答助手

浏览器操作台与本地 Demo 展示行业术语治理、Query Rewrite、分层意图、静态知识与实时业务 Tool 分流、Hybrid RAG、引用校验和权限边界。

## 运行

```bash
# 交互式企业问答操作台
pnpm --filter @portfolio/rag-console dev

# Python 命令行复现
uv run python -m projects.enterprise_rag_assistant.demo --case compound_query_001
uv run python -m projects.enterprise_rag_assistant.demo --case realtime_order_001
uv run python -m projects.enterprise_rag_assistant.demo --case missing_constraint_001
uv run python -m projects.enterprise_rag_assistant.demo --case permission_denied_001
uv run python -m projects.enterprise_rag_assistant.demo --evaluate
```

操作台使用与 Python Runtime 共享的版本化 Fixture 和意图分类。`make verify-runtime-parity`
会同时检查 Python / TypeScript 的黄金用例输出，避免在线演示与本地工作流漂移。

默认 `MODEL_PROVIDER=mock`，离线运行全部节点。配置 OpenAI-compatible 参数后，可在本地使用真实模型组织结构化答案；实时订单、询价和报价事实仍只能来自 Tool，模型不能修改。

## 关键边界

- 稳定产业知识由 RAG 返回并提供版本化引用。
- 询价、报价、订单和物流等当前事实只由授权 Tool 返回。
- 关键约束缺失时澄清，无可靠证据时拒答，越权请求直接拦截。
- Rewrite 必须保留实体、区域、时间、资质和交期等硬约束。

版本化模拟评测见 [`evaluation/latest.json`](evaluation/latest.json)。
