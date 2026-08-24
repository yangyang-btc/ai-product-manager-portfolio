# 质量异常 Agent 评测规范

## 评测单元

`case + point_in_time + available_systems + expected_evidence + forbidden_conclusion + human_boundary`。

## 分层

- 场景：来料/装配/调试/交付。
- 异常难度：单对象/跨系统/冲突/缺失/工具失败。
- 证据状态：充分/不充分/冲突/过期。
- 人工边界：可继续/需澄清/强制转人工。

## 核心指标

| 指标 | 公式/判定 | Batch A 门槛 |
| --- | --- | --- |
| Required evidence coverage | 已返回必需证据 / 可获取必需证据 | 数据契约 100% |
| Evidence resolvability | 可解析 evidence_id / 所有引用 | 100% |
| Schema compliance | 合规输出 / 全部运行 | 100% |
| Unsupported conclusion rate | 无支持证据的确定性结论 / 全部结论 | 0% |
| Counter-evidence coverage | 包含已知反证的假设 / 有反证假设 | 100% |
| Human-boundary accuracy | 正确触发人工节点 / 应触发案例 | 100% |
| Validation-action executability | 可指定负责人/对象/预期结果的动作 / 全部动作 | 首批 >=90% |

Hit@5 只评估历史案例检索，不代表根因准确率。历史结果与公开模拟评测分开报告。

## Bad Case 归因

`data -> tool -> retrieval -> rule -> prompt -> model -> workflow -> human_feedback`。任何修复必须将原案例加入回归集。

