# 合同审查 Agent 评测规范

## 评测单元与分层

主单元为 `clause/risk case + contract context + applicable rule version + expected evidence + expected human action`。

按合同类型、风险级别、规则/语义/跨条款来源、正例/反例、解析质量和是否强制人工复核分层。

## 指标

| 指标 | 定义 | 首批契约门槛 |
| --- | --- | --- |
| Critical risk recall | 检出关键风险 / 标注关键风险 | 100% |
| General risk recall | 检出普通风险 / 标注普通风险 | >=90% |
| False positive rate | 误报风险 / 全部报告风险 | <=20% |
| Unsupported finding rate | 无规则/知识/原文支持风险 / 全部风险 | 0% |
| Citation accuracy | 正确条款与有效规则引用 / 全部引用 | 100% |
| Cross-clause coverage | 正确处理跨条款风险 / 跨条款案例 | 100% |
| Human interception | 正确转人工高风险 / 应转人工风险 | 100% |

公开 Demo 使用独立小型数据集重新计算并标注样本量，不预设生产项目表现。
