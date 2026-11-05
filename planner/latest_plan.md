# GLEPPO 最新执行计划 — R26 ECOS Protocol Reconciliation R1.1 Corrective

**仓库：** `yujian777555/GLEPPO`  
**分支：** `r25-handoff`  
**更新时间：** 2026-11-05  
**R2.1.1 Planner decision：** ACCEPT（已关闭）  
**R26 Reconciliation R1 Planner decision：** REQUEST_CHANGES  
**Reviewed Executor commit：** `7423d5f7c753430a2f361400e1b39cd5b125aaf6`  
**Planner review：** `research/R26_ECOS_PROTOCOL_RECONCILIATION_PLANNER_REVIEW.md`  
**R1.1 Executor prompt：** `planner/GLEPPO_R26_ECOS_PROTOCOL_RECONCILIATION_R1_CORRECTIVE_PROMPT.md`

---

## 一、当前决策

**R26 ECOS Protocol Reconciliation R1 不接受。执行一次聚焦的 R1.1 文档修正。**

不是否定 ECOS 研究方向，也不需要重启 Stage 1I。当前问题是 R1 的拟议合同尚不能准确反映源代码和历史协议。

Planner 独立复核发现的主要问题：

1. JSON 只列出 25 个 feature label，却声明 32 维；`budget_used_frac` 源码当前重复使用 `gen_t/T`。
2. R24 reward 与 Phase 1/shared generation reward 并未证明等价；PC1 estimator 消费预先提供的 `gen_rewards`，不在估计器中重新计算共享 reward。
3. `evolution.py` 用含 `operator_name` 的哈希生成 `replicate_id`，导致 action 间接进入 effective evaluation seed。
4. Phase 1 PC1（≥200 states、≥20 rollouts、h=5）与 PC1 R4（100 states、3 Q-rollouts、h=3）是实质设计变化；R1 未充分说明。
5. Phase 1 模板分割与实际 `tasks.py` / manifest 冲突；R24 Confirm 无已提交任务身份，且不能擅自改称 validation。
6. 每个 evolution episode 的 180 slots 漏掉初始化；当前最大计划量是 24 + 180 = 204，而不是 180，先前所称 32 个初始化 slots 也不正确。
7. R24 resource scope、PC1 CI/stop rules、baseline tier 和 JSON provenance 仍有缺口。

完整证据与行号见 Planner review。

## 二、R1.1 唯一任务

执行：

`planner/GLEPPO_R26_ECOS_PROTOCOL_RECONCILIATION_R1_CORRECTIVE_PROMPT.md`

必须修正已有三个文件，不创建重复文件：

- `research/R26_ECOS_PROTOCOL_RECONCILIATION.md`
- `research/ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.md`
- `research/ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.json`

重点是逐维 32-feature 表、reward 冲突、PC1 reward provenance、action-dependent seed call site、PC1 sample design、task split、204-slot episode budget、R24 call/token scope、baseline fairness、CI margins 和 stop rules。

R1.1 仍必须是 **PROPOSED / NOT APPROVED**。历史 Phase 1、R24、PC1 R4 文件不得修改。

## 三、科学结论保持不变

- ECOS 是可证伪研究假设，不是已经证实有效的方法。
- Fixed-vs-adaptive、PPO-vs-rule、PPO-vs-LinUCB 仍未验证。
- R21-C1 是 DAC/arithmetic 比较，不是 operator/controller 比较。
- Reward validity、32-D state utility 和 delayed effects 均未获得正式实验支持。
- 不因本轮协议修订而提前训练 PPO。

## 四、硬门禁

- PC1 BLOCKED；PC1 R4 PROPOSED / NOT APPROVED。
- Formal G3 FAIL。
- Family C NOT ACCESSED；不得读取 task payload/gold、执行或调参。
- Registered PC1 NOT EXECUTED。
- Controller training NOT AUTHORIZED / NOT STARTED。
- 无模型/API 调用、生产 runtime、signing-key 访问。
- 不执行 PC1、baseline pilot、Formal G3 efficacy 或任何实验。
- 不修改生产源码、`tests/`、历史协议、数据、manifest、raw evidence。
- 不更新/合并 main，不 reset/rebase/force-push。
- 不混用其他项目的代码、数据或报告。

## 五、下一关口

**R1.1 Executor 文档修正完成 → Planner 独立复审。**

本轮只允许一次聚焦修正。通过之前，不进入 PC1 执行或控制器训练授权讨论。
