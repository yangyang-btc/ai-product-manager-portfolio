# 质量异常 Agent 数据字典

| 字段 | 类型 | 来源 | 含义 | 敏感级别 | 模拟规则 |
| --- | --- | --- | --- | --- | --- |
| anomaly_id | string | QMS | 脱敏异常编号 | 内部 | `QA-<SCENE>-NNN` |
| scenario | enum | QMS | incoming/assembly/debug/delivery | 公开 | 固定枚举 |
| equipment_id | string | MES | 设备别名 | 内部 | `EQ-DEMO-NNN` |
| work_order_id | string | MES | 制造工单 | 内部 | `WO-DEMO-NNN` |
| bom_version | string | PLM | 异常时有效 BOM | 内部 | 虚构版本号 |
| material_id | string | ERP/PLM | 通用物料类型 | 可公开脱敏 | 使用功能型名称 |
| lot_id | string | ERP/QMS | 物料批次 | 内部 | 随机生成，不映射真实批次 |
| supplier_alias | string | ERP | 供应商别名 | 机密 | `SUP-A/B/C` |
| inspection_value | decimal | QMS | 检验实测值 | 内部 | 围绕虚构规范上下限生成 |
| specification | decimal/range | SOP/FMEA | 有效判定阈值 | 内部 | 使用工程合理但非真实参数 |
| source_timestamp | datetime | 各业务系统 | 事实发生/更新时间 | 内部 | 固定演示时间窗 |
| document_version | string | 知识库 | 知识有效版本 | 内部 | `V1.0/V1.1` |
| evidence_id | string | Agent | 证据引用主键 | 公开 | `EV-<SOURCE>-NNN` |
| estimated_tokens | integer | Trace | 离线估算 Token | 公开 | 显式标注“估算” |

禁止生成能对应真实设备、真实客户、真实批次或真实工艺窗口的值。

