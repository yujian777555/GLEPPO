# GLEPPO 最新执行计划 — R26 Adaptive-Operator Algorithm Pilot

**仓库：** `yujian777555/GLEPPO`  
**当前分支：** `r26-algorithm-pilot`  
**基础提交：** `aa16c23101c1b387e8617910601da9a5d96231c1`  
**用户最新指令：** 抓紧做算法实验  
**更新时间：** 2026-11-05

## 一、优先级调整

用户明确要求将精力从文档审查转向算法实验。因此：

- R1.2 最终文档一致性修正：**PAUSED_BY_USER_PRIORITY**，并未接受或关闭。
- 当前主任务：执行 R26 自适应算子选择算法 pilot。
- 实验分支与文档审查分支隔离；不得修改/合并 main。

## 二、当前实验问题

**自适应选择 Agent 演化算子，是否比固定、随机和规则选择带来更好的任务成功率？**

五个算子：
`prompt_local_edit`, `prompt_critique_rewrite`, `tool_subset_edit`, `workflow_step_edit`, `crossover`.

九个实验臂：
- 五个固定算子臂；
- Uniform Random；
- Phase 1 B2 Rule；
- LinUCB（pilot_context_v1）；
- Tabular Q-learning（pilot_context_v1）。

暂不训练 PPO。先确认是否存在超越 Random 和 Rule 的自适应收益。

## 三、立即执行任务

Executor 提示词：

`planner/GLEPPO_R26_ALGORITHM_PILOT_PROMPT.md`

核心工作：
1. 在实验分支修复 offspring evaluation replicate_id 的 action-dependence。
2. 分离 parent-selection RNG 与 crossover mate RNG。
3. 实现配对种子/RNG 回归测试。
4. 使用 StubLLM 运行 324 个 episode 的初步 pilot。
5. 只使用 Family A/B train 与 validation；禁止加载 Family C。
6. 产出逐 episode 原始数据、运行 manifest、汇总统计和下一步决策。

## 四、冻结的 Pilot 配置

| 项目 | 配置 |
|---|---:|
| μ / λ | 8 / 4 |
| T | 15 |
| n_eval | 2 |
| Evolution seeds | 11, 22 |
| TRAIN | 7 train_A + 5 train_B |
| VALIDATION | 3 val_A + 3 val_B |
| Arms | 9 |
| TRAIN episodes | 216 |
| VALIDATION episodes | 108 |
| Total episodes | 324 |
| Planned slots / episode | 136 |
| Total planned slots | 44,064 |

LinUCB/Q-learning 只在 TRAIN 学习，VALIDATION 冻结评估。固定算子中最优臂只允许用 TRAIN 选择。

## 五、解释边界

该 pilot 是**未注册开发性实验**，仅用于快速筛选机制，不是 PC1，不是 Formal G3，也不是论文确认性证据。StubLLM 是确定性策略门控替身，不代表真实 Qwen/LLM Agent 性能。

如 adaptive 未能同时超过 Random 与 Rule，不进入 PPO；先检查算子效应、观测信号和任务机制。若有一致正向信号，再扩大种子/任务规模。

## 六、硬门禁

- Family C 未访问；不读取 `test_C.jsonl`。
- 不执行 PC1 R4、Formal G3 或生产 Qwen。
- 不调用模型 API，不进行本地真实模型推理。
- 不训练 PPO，不因本 pilot 自动获得后续实验授权。
- 不修改 main、不合并实验分支。
- 不修改数据集、manifest、gold 或历史协议。
- 不运行无关 audit/helper scripts。

## 七、下一关口

**配对种子/RNG 修复 → 324-episode StubLLM pilot → Planner 审查真实结果。**

完成后立即报告正结果、负结果、失败与成本，不再延长文档循环。
