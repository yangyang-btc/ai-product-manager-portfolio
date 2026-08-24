# 合同审查 Agent 领域模型

## 业务边界

辅助半导体设备企业的合同初审。系统负责文档完整性、必审规则覆盖、知识引用、语义风险和修改建议，法务对高风险与最终意见负责。

## 核心对象

| 对象 | 主要字段 | 说明 |
| --- | --- | --- |
| Contract | id, type, version, parties, amount_band, effective_date, status | 采购/设备销售/NDA/技术合作 |
| Clause | id, heading, text, page, parent_id, references | 保留章节层级与跨条款关系 |
| Attachment | id, type, version, checksum, required | 技术协议、交付清单、验收标准等 |
| BusinessContext | purchase_order, project_alias, equipment_model, milestone_plan | 合同所属的业务背景 |
| ReviewRule | id, contract_types, condition, severity, version, valid_from | 确定性必审规则 |
| PolicyDocument | id, type, version, effective_at, scope | 制度、标准模板和已审案例 |
| RiskFinding | id, source, severity, clause_ids, rule_id, evidence, suggestion | 规则/LLM/人工风险卡片 |
| HumanReview | reviewer_role, decision, final_severity, rationale | 法务接受、修改或驳回 |

## 行业关键关系

- 采购合同 -> 采购订单 -> 核心零部件/外协加工 -> 来料检验 -> 质量异议 -> 供应商责任。
- 设备销售合同 -> 交付里程碑 -> FAT -> 安装调试 -> SAT -> 质保起算 -> 售后服务。
- NDA -> 保密信息范围 -> 允许披露 -> 保密期 -> 返还/销毁。
- 技术合作 -> 背景知识产权 -> 新生成果 -> 验收指标 -> 变更 -> 责任。

## 状态与不变式

`uploaded -> parsing -> completeness_check -> reviewing -> awaiting_legal -> revised -> finalized`

1. 每个 RiskFinding 必须绑定条款位置与规则/知识版本。
2. “未发现”不等于“无风险”；必须同时报告已覆盖、未覆盖和无法解析范围。
3. 高风险、解析异常、冲突证据和低置信结果强制法务复核。
4. 规则覆盖和条款完整性不依赖 Top-K RAG。

