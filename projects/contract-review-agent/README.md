# 半导体设备企业合同审查 Agent

公开 Demo 使用重新生成的采购、设备销售、NDA 和技术合作合同，展示 Router、确定性规则、知识检索、语义风险、跨条款检查与强制法务复核。另包含一个无自动风险反例和一个正文/附件跨条款边界案例。

## 运行

浏览器操作台：

```bash
pnpm --filter @portfolio/contract-console dev
```

Python 离线复现：

```bash
uv run python -m projects.contract_review_agent.demo --case procurement_contract_001
uv run python -m projects.contract_review_agent.demo --case sales_contract_001
uv run python -m projects.contract_review_agent.demo --case nda_001
uv run python -m projects.contract_review_agent.demo --case technical_cooperation_001
uv run python -m projects.contract_review_agent.demo --evaluate
```

默认 `MODEL_PROVIDER=mock`，无 API Key 也能执行完整 Workflow。配置 `.env.example` 中的 OpenAI-compatible 参数后，语义风险节点可在本地使用真实模型；模型输出仍必须通过 Pydantic Schema、引用和成本边界校验。

## 输出

每张风险卡包含合同原文位置、规则/知识版本、风险来源、风险级别、修改建议和人工状态。高风险结果固定为 `pending_legal_review`，Demo 不输出最终法律意见。

版本化模拟评测见 [`evaluation/latest.json`](evaluation/latest.json)。

浏览器 Runtime 与 Python Runtime 的规范化结果通过 `make verify-runtime-parity` 校验。Run Bundle v2 只导出公开摘要，不包含完整条款文本。
