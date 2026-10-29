# R3 真实模型 Canary 与配对性能实验 — 执行报告

**日期:** 2026-10-29
**Run ID:** `20261029T052350Z_R3`
**分支:** `c7-g3-diag-v2-r1-fastpath`
**状态:** `PILOT_COMPLETE_REQUIRES_INDEPENDENT_REVIEW`

## 一、Canary 门禁结果

| 条件 | 要求 | 实际 | 结果 |
|------|------|------|------|
| 工具路径合规 | 3/3 | 3/3 | ✅ |
| 最终答案正确 | ≥2/3 | 3/3 | ✅ |
| 模型 revision | 冻结版本 | `a09a35458c...` | ✅ |
| 生成计数=账本行数 | 一致 | 6=6 | ✅ |
| 调用 ID 唯一且单调 | 一致 | ✅ | ✅ |
| Token delta=运行时总量 | 一致 | 42=42 | ✅ |
| 无隐藏失败 | 0 | 0 | ✅ |
| **Canary 通过** | | | **✅ PASS** |

## 二、配对性能实验 (54/100 generations, 42.9s)

### tool_subset_edit — 9 对配对比较

| 指标 | 父代 | 子代 | Δ |
|------|------|------|---|
| answer_correct | 77.8% | 77.8% | 0.0 |
| tool_path_valid | **100%** | **0%** | **-100%** |
| format_compliant | 88.9% | 100% | +11.1% |
| hard_validity | 88.9% | **0%** | **-88.9%** |
| effective_success | 77.8% | **0%** | **-77.8%** |
| format_failures | 1 | 0 | |
| behavior_changed (诊断) | | 9/9 | |

**结论: 负面。** `tool_subset_edit` 在所有 9 次配对中均破坏工具路径。尽管 answer_correct 率持平，但 hard_validity 和 effective_success 均降为 0%。子代不满足硬有效性要求。

### crossover — 9 对配对比较

| 指标 | 父代 | 子代 | Δ |
|------|------|------|---|
| answer_correct | 77.8% | **44.4%** | **-33.3%** |
| tool_path_valid | 100% | 100% | 0 |
| format_compliant | 88.9% | 33.3% | -55.6% |
| hard_validity | 88.9% | **33.3%** | **-55.6%** |
| effective_success | 77.8% | **33.3%** | **-44.4%** |
| format_failures | 1 | **6** | |
| behavior_changed (诊断) | | 6/9 | |

**结论: 负面。** `crossover` 保留了工具路径，但严重降低答案正确性和格式合规性。6/9 子代格式失败。配对正确率变化为 -0.333。

## 三、分任务指标

### B2-001 (calc→64, str_ops→SUM)
| 算子 | 父正确/路径 | 子正确/路径 | 子格式 |
|------|------------|------------|--------|
| tool_subset_edit | 3/3, 3/3 | 1/3, 0/3 | 3/3 |
| crossover | 3/3, 3/3 | 1/3, 3/3 | 0/3 |

### B2-003 (calc→60, str_ops→HI)
| 算子 | 父正确/路径 | 子正确/路径 | 子格式 |
|------|------------|------------|--------|
| tool_subset_edit | 1/3, 3/3 | 3/3, 0/3 | 3/3 |
| crossover | 1/3, 3/3 | 0/3, 3/3 | 0/3 |

### B2-004 (py_sandbox→32, calc→41)
| 算子 | 父正确/路径 | 子正确/路径 | 子格式 |
|------|------------|------------|--------|
| tool_subset_edit | 3/3, 3/3 | 3/3, 0/3 | 3/3 |
| crossover | 3/3, 3/3 | 3/3, 3/3 | 3/3 |

B2-004 的 crossover 无行为变化 (3/3)，可能是任务结构较简单。

## 四、预算与完整性

| 项目 | 值 |
|------|-----|
| 实际 model.generate | 54 / 100 |
| 墙钟 | 42.9s / 300s |
| 账本行数 | 54 |
| 调用 ID 唯一单调 | ✅ |
| Token delta = 运行时总量 | ✅ |
| 预算耗尽 | 否 |
| 矩阵完整 | ✅ (3任务×3种子×2算子) |

## 五、独立验证结果

**28/28 检查全过, 0 失败。**

包括: 产物哈希、冻结清单链接、源码哈希(14文件)、账本完整性、Canary 门禁复算、逐集指标独立复算、矩阵覆盖率、边界合规。

## 六、科学结论

### 算子有效性评估

1. **`tool_subset_edit` 无效。** 系统性破坏必需工具路径 (0% 子代通过 hard_validity)。尽管答案正确率持平，但违反硬有效性约束的子代不应被视为成功。

2. **`crossover` 有害。** 虽保留工具路径，但答案正确率从 77.8% 降至 44.4%，格式合规率从 88.9% 降至 33.3%。配对正确率变化为负。

3. **行为变化 ≠ 性能提升。** 两个算子均产生行为变化 (9/9, 6/9)，但这反映的是性能退化而非改进。

4. **选择机制必要性。** 实验结果表明，当前选择机制需要能够识别并淘汰有害子代。`tool_subset_edit` 子代 100% 破坏工具路径——任何合理的选择机制都应拒绝它们。

### 与 R2 独立审查的对比

R2 审查预测:
- "tool_subset_edit can remove or replace a required tool step" → **R3 确认: 0% 子代工具路径有效**
- "crossover preserves the required tool path but disrupts answer correctness/format" → **R3 确认: 正确率 -33.3%, 格式失败 6/9**

## 七、边界合规

| 项目 | 状态 |
|------|------|
| 正式 G3 | FAIL (未改变) |
| PC1 | NOT_APPROVED / NOT_EXECUTED |
| Family C | NOT_ACCESSED |
| 控制器训练 | NOT_AUTHORIZED |
| R1/R2 数据 | 未覆盖 |

## 八、产物清单

| 文件 | 位置 |
|------|------|
| R3_FROZEN_MANIFEST.json | `research/runs/20261029T052350Z_R3/` |
| R3_RAW.json | 同上 |
| R3_LEDGER.jsonl | 同上 |
| R3_REPORT.md | 同上 |
| R3_RESULT_MANIFEST.json | 同上 |
| 独立验证输出 | 已保存 |

Result manifest SHA-256: `cfadb67b37d40c31`

## 九、下一步建议

1. **提交 Planner 独立复审** R3 结果
2. **不要请求正式 G3 协议修订** 基于当前负面结果
3. **考虑算子改进方向:** `tool_subset_edit` 需保留工具步骤约束; `crossover` 需保持格式合规
4. **扩大任务集和重复数** 在更大规模实验前
