# 质量异常 Agent 领域模型

## 业务目标

将分散在 QMS、MES、ERP 和 PLM 的当前事实与 SOP、FMEA、8D 和历史案例组织为可审计证据，输出待工程师验证的原因假设和验证动作，不自动认定根因。

## 核心对象

| 对象 | 关键字段 | 业务含义 |
| --- | --- | --- |
| QualityAnomaly | anomaly_id, scenario, symptom, severity, discovered_at, status | 一次来料/装配/调试/交付异常 |
| Equipment | equipment_id, model, serial_alias, config_version | 发生异常的设备及配置 |
| WorkOrder | work_order_id, product, planned_bom, route_version, station | 制造与调试任务载体 |
| MaterialLot | material_id, lot_id, supplier_alias, received_at, inspection_status | 物料批次与来料状态 |
| BOMSnapshot | bom_version, item_id, required_qty, actual_lot, effective_at | 异常发生时的实际 BOM 快照 |
| InspectionRecord | record_id, stage, item, value, unit, limit, result, measured_at | 来料/过程/完工/交付检验事实 |
| ProcessRecord | process_id, operation, parameter, value, spec_version, operator_role | 工序与关键工艺参数 |
| SoftwareConfig | version, deployed_at, parameter_set, change_id | 调试测试相关的软件与参数版本 |
| KnowledgeDocument | document_id, type, version, effective_at, applicable_scope | SOP/FMEA/8D/规范 |
| HistoricalCase | case_id, symptom, confirmed_cause, evidence_ids, validation_action | 经人工确认的历史异常案例 |
| Evidence | evidence_id, source_type, source_id, observed_at, version, confidence | Tool/RAG 统一证据引用 |
| Hypothesis | hypothesis_id, statement, support, counter_evidence, missing, actions | 待工程师验证的原因假设 |
| HumanReview | reviewer_role, decision, comment, reviewed_at | 工程师对假设的接受/修改/否定 |

## 核心关系

```text
QualityAnomaly -> Equipment -> WorkOrder
WorkOrder -> BOMSnapshot -> MaterialLot -> InspectionRecord
WorkOrder -> ProcessRecord / SoftwareConfig
QualityAnomaly -> Evidence -> Tool business records
QualityAnomaly -> Evidence -> KnowledgeDocument / HistoricalCase
Evidence -> Hypothesis -> HumanReview
```

## 状态

`reported -> clarifying -> collecting_facts -> retrieving_knowledge -> checking_evidence -> awaiting_human -> validating -> closed`

任意阶段均可进入 `degraded` 或 `manual_only`。`closed` 只能由人工录入已验证根因后进入。

## 不变式

1. 每条假设至少有一条支持证据或明确标注“无支持证据”并禁止进入结论。
2. 历史相似不等于本次因果；历史案例只能作为假设来源。
3. 阈值判定必须引用当时有效规范版本。
4. 冲突数据不由 LLM 自行裁决，必须标注冲突并补查或转人工。
5. 停线、放行、异常关闭和责任认定不属于 Agent 可执行动作。

