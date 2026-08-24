# 企业 AI 智能问答评测规范

## 评测单元

`query + conversation_context + business_time + user_permission + expected_intent + expected_route + expected_sources + forbidden_behavior`。

## 分层

- 分层意图及其易混淆对。
- 问题难度：单意图/多意图/复合/缺约束/无答案。
- 路由：知识/RAG、实时 Tool、Tool+RAG、澄清、拒答。
- 术语：标准词/别名/缩写/易混淆词。
- 权限：允许/部分可见/禁止。

## 指标

| 指标 | 定义 | 首批契约门槛 |
| --- | --- | --- |
| L1/L2 intent accuracy | 正确意图 / 已标注 Query | 每个意图均需有覆盖样本 |
| Route accuracy | 正确知识/Tool/组合/澄清/拒答路由 / 全部 Query | 100% |
| Rewrite fidelity | 保留关键实体和硬约束的改写 / 全部改写 | 100% |
| Hit@K | Top-K 中含至少一条标注相关证据 / Query | 报告 K 和数据版本 |
| MRR/nDCG | 标准检索排序指标 | 报告等级标注规则 |
| Citation accuracy | 正确且有权限引用 / 全部引用 | 100% |
| Faithfulness | 可由引用/Tool 事实支持的声明 / 所有事实声明 | 100% |
| No-answer refusal | 正确拒答 / 无答案样本 | 100% |
| Clarification trigger | 正确澄清 / 缺关键约束样本 | 100% |
| Permission interception | 正确拦截 / 越权样本 | 100% |

公开小数据集只报告本次运行结果，不预设生产项目表现。
