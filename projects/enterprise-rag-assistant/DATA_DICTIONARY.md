# 企业 AI 智能问答数据字典

| 字段 | 来源 | 含义 | 模拟规则 |
| --- | --- | --- | --- |
| enterprise_id | 主数据 | 企业脱敏主键 | `ENT-DEMO-NNN` |
| supplier_id | 主数据 | 供应商脱敏主键 | `SUP-DEMO-NNN` |
| item_id | 商品/物料主数据 | 通用产品物料 | `ITEM-DEMO-NNN` |
| relationship_id | 合同抽取 | 供需关系 | `REL-DEMO-NNN` |
| process_id | 工艺文档抽取 | 工艺流程 | `PROC-DEMO-NNN` |
| canonical_term | 术语库 | 标准名称 | 使用通用行业术语 |
| alias | 术语库 | 缩写/俗称/部门表达 | 不使用公司专有黑话 |
| intent_l1/l2 | 意图模型 | 分层意图标签 | 固定于领域模型 |
| updated_at | 业务 Tool | 实时事实更新时间 | 固定演示时钟 |
| permission_scope | 权限系统 | 用户可见数据范围 | public/internal/restricted |
| citation_id | RAG/Tool | 可追溯证据 | `CIT-DEMO-NNN` |

所有供应关系、工艺参数、订单和物流记录从零生成，不转写真实合同、交易或工艺文件。
