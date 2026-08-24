# 企业 AI 智能问答领域模型

## 业务目标

为产业供应链/B2B 平台的运营、BD 和新员工提供带依据的产业知识答案，并严格区分静态知识、当前业务事实和模型建议。

## 核心对象

| 对象 | 关键字段 | 用途 |
| --- | --- | --- |
| Enterprise | enterprise_id, industry, region, qualification, status | 产业链企业与主体 |
| SupplierProfile | supplier_id, capabilities, regions, certifications, score_version | 供应商能力与准入 |
| ProductMaterial | item_id, category, specification, aliases, applications | 产品/物料知识 |
| SupplyRelationship | supplier_id, buyer_id, item_id, scope, valid_from, evidence_id | 从合同抽取的供应关系 |
| ProcessFlow | process_id, product, operations, parameters, quality_points, source_id | 从制造文档抽取的工艺流程 |
| KnowledgeDocument | document_id, type, version, scope, permission, effective_at | 合同/工艺/商品/规则/培训知识 |
| TerminologyEntry | canonical, aliases, acronym, broader, narrower, confused_with | 术语治理与 Query Rewrite |
| Inquiry | inquiry_id, item_id, quantity_band, due_date, status, updated_at | 实时询价事实 |
| Quotation | quotation_id, inquiry_id, supplier_id, status, updated_at | 实时报价事实 |
| Order | order_id, quotation_id, delivery_status, updated_at | 实时订单事实 |
| LogisticsEvent | order_id, event, location_region, occurred_at | 实时物流事实 |
| Query | raw, normalized, rewritten, protected_entities, user_context | 用户问题及改写过程 |
| Intent | level_1, level_2, confidence, alternatives | 知识域、路由和输出格式 |
| Answer | facts, knowledge, recommendation, citations, freshness, limitations | 结构化答案 |

## 分层意图体系

1. `enterprise_supplier`：enterprise_profile、supplier_qualification、supply_relationship、supplier_capability。
2. `product_material`：product_specification、category_application、alias_resolution、substitute_material。
3. `manufacturing_process`：process_flow、process_parameter、quality_control_point、equipment_requirement。
4. `platform_knowledge`：platform_rule、contract_policy、onboarding_training、permission_help。
5. `realtime_transaction`：inquiry_status、quotation_status、order_status、logistics_status。
6. `composite_analysis`：supplier_comparison、supply_chain_trace、process_supply_match、knowledge_and_realtime。

## 路由规则

- 合同、工艺、商品、平台规则 -> RAG。
- 当前询价、报价、订单、物流 -> Tool/API。
- 复合问题 -> 拆分后 Tool + RAG，再组织答案。
- 低置信或关键约束缺失 -> 澄清。
- 无证据或无权限 -> 拒答/拦截，不改用模型猜测。

## 不变式

1. Rewrite 保留原问题、关键实体、时间和数值约束。
2. 实时事实必须带数据源和更新时间。
3. 模型不得修改 Tool 返回的询价、报价、订单和物流状态。
4. 知识引用必须通过版本、适用范围和权限检查。
