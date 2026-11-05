# GLEPPO 最新执行计划 — R26 ECOS Protocol Reconciliation

**仓库：** `yujian777555/GLEPPO`  
**分支：** `r25-handoff`  
**更新时间：** 2026-11-05  
**最近接受的 Executor work commit：** `362f343f43befc7f43c00ba5edd1059b01d523d1`  
**Stage 1I-R2.1.1 Planner review：** ACCEPT  
**Planner review report：** `research/R26_STAGE1I_R2_1_1_PLANNER_REVIEW.md`  
**下一阶段 Executor prompt：** `planner/GLEPPO_R26_ECOS_PROTOCOL_RECONCILIATION_EXECUTOR_PROMPT.md`

---

## 一、当前决策

**Stage 1I-R2.1.1 已接受。进入 R26_ECOS_PROTOCOL_RECONCILIATION，限文档与只读源码审查。**

R2.1.1 完成并接受的内容：

- R39/R41/R48 保持 PARTIALLY_FIXED，42 项处置为 25/15/1/1。
- 42 个唯一 ID R12–R53，JSON/Markdown 处置一致。
- Validator 的 21 个自测名称和顺序与代码中的 21 个检查项一致；实际 stdout 和 exit code 0 已由 Executor 持久化。
- R41 不再把 raw-evidence identity 作为原始验收条件；唯一未完成条件是 registered analysis 端到端消费验证 artifact 的行为测试。
- R2.1、R2.1.1 SHA 链已记录。
- R2.1.1 仅修改证据映射、测试证据与 status；没有生产源码或 `tests/` 变更。

**证据限制：** 21/21 stdout 与 exit code 是 Executor-captured；Planner 未独立执行。该提交无 GitHub CI status/workflow run。450/450 仍为 EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED。

完整决定：`research/R26_STAGE1I_R2_1_1_PLANNER_REVIEW.md`。

## 二、当前科学事实

ECOS 保留为可证伪研究假设，但算法优势仍未得到证明：

- R21-C1 是 LLM arithmetic execution 与 DAC 的比较，不是固定/自适应算子或控制器比较。
- Fixed-vs-adaptive operator selection：UNTESTED。
- PPO-vs-rule：UNTESTED。
- PPO-vs-LinUCB/contextual Bandit：UNTESTED。
- Reward validity、32-D state utility、delayed effects 均不能仅凭设计文档认定成立。

## 三、R26_ECOS_PROTOCOL_RECONCILIATION 的目标

Phase 1、R24、PC1 R4 和 active shared code 尚未形成单一可执行协议。重点核对：

1. decision / generation / episode / rollout / evaluation replica / CTX 的单位和嵌套关系；
2. 32-D state 的精确字段、时序、缺失值、归一化和泄漏风险；
3. 五个 operator 的 ID、语义和每代动作规则；
4. Phase 1/shared-code/PC1 generation reward 与 R24 immediate effective-success reward 的冲突；
5. gamma 0.95 vs 0.99、GAE lambda 与 PC1 return 的一致性；
6. Train / Validation / Confirm / Family C 的任务身份、种子和隔离；
7. 固定、随机、规则、LinUCB、PPO、Q-learning、FM rewrite 与 ablation 的基线层级；
8. 主终点、PC1 myopia diagnostic、有效性和成本指标；
9. 候选任务执行、PC1 slots、训练算力、model calls、tokens 的独立预算账本；
10. evaluator 与 PC1 的 CRN seed serialization 是否真正统一；
11. SR1、PC1 PASS/FAIL/INCONCLUSIVE 与 R24 stopping rules 的衔接。

## 四、本阶段交付

执行 `planner/GLEPPO_R26_ECOS_PROTOCOL_RECONCILIATION_EXECUTOR_PROMPT.md`，形成：

- `research/R26_ECOS_PROTOCOL_RECONCILIATION.md`
- `research/ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.md`
- `research/ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.json`

并更新 `status.json`、本文件和 `planner/GLEPPO_R26_HANDOFF.md`。

所有历史协议保留原样。新协议必须标记 **PROPOSED / NOT APPROVED**，列出 unresolved items 和后续代码改造清单。不得用当前实现存在某个值作为唯一选择理由，也不得静默覆盖 R24/Phase 1 历史设计。

## 五、硬门禁

- PC1 BLOCKED；PC1 R4 PROPOSED / NOT APPROVED。
- Formal G3 FAIL。
- Family C NOT ACCESSED；不得加载、检查 gold、执行或调参。
- Registered PC1 NOT EXECUTED。
- Controller training NOT AUTHORIZED / NOT STARTED。
- 不调用模型/API，不运行生产 runtime，不访问 signing key。
- 本阶段不执行 PC1、不训练、不做 baseline pilot。
- 不修改生产源码、`tests/`、Phase 1/R24/PC1 R4 历史协议、数据、raw evidence 或 manifests。
- 不更新/合并 main，不 reset/rebase/force-push。
- 不混用其他项目的代码、数据或报告。

**下一关口：** Protocol reconciliation Executor completion → Planner independent review。只有新协议经 Planner 独立审查后，才讨论后续授权门槛；本阶段本身不授予任何实验权限。

---

## R26 ECOS Protocol Reconciliation (2026-11-05)

文档专用阶段完成。交付物：
- research/R26_ECOS_PROTOCOL_RECONCILIATION.md（差异矩阵，A-K 全维度）
- research/ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.md（拟议合同）
- research/ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.json（机器可读镜像）

关键决策：共享 reward（Phase 1 + 实现一致）、γ=0.95（R24 γ=0.99 为错误）、32 维 state、5 算子、tiered baselines。

未解决：特征归一化常数、R24 confirm ≠ Family C、种子 schema 双路径、无 controller 实现。

**状态：** PROPOSED / NOT APPROVED。等待 Planner 独立复核。

## R1.1 纠正完成 (2026-11-05)

R1 未被接受。R1.1 纠正完成：32 特征精确 schema、reward 冲突声明、种子 call-path 缺陷、PC1 采样差异、预算 204、模板 provenance、baseline 分层。等待 Planner 复核。
