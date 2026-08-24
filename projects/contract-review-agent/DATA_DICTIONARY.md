# 合同审查 Agent 数据字典

| 字段 | 含义 | 敏感性 | 模拟规则 |
| --- | --- | --- | --- |
| contract_id | 脱敏合同主键 | 内部 | `CTR-DEMO-NNN` |
| contract_type | procurement/sales/nda/technical_cooperation | 公开 | 固定枚举 |
| party_alias | 对方别名 | 机密 | `PARTY-A/B` |
| project_alias | 设备/研发项目别名 | 机密 | `PROJECT-DEMO-NNN` |
| amount_band | 金额档位 | 机密 | low/medium/high，不使用真实金额 |
| clause_id | 稳定条款定位 | 内部 | `CL-<SECTION>-NNN` |
| page/heading | 原文位置 | 内部 | 由虚构文档生成 |
| rule_id | 审查规则主键 | 内部 | `RULE-<TYPE>-NNN` |
| rule_version | 规则有效版本 | 内部 | 评测必填 |
| risk_severity | low/medium/high/critical | 公开 | 按模拟规则表判定 |
| finding_source | rule/rag/llm/human | 公开 | 强制显示 |
| reviewer_decision | accept/modify/reject | 内部 | 公开 Demo 使用模拟法务标签 |

公开合同文本从零编写，不对真实合同做简单替换。

