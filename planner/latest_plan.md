# GLEPPO 最新执行计划 — R23 复审程序纠偏与训练门禁推进

**仓库：** `yujian777555/GLEPPO`  
**工作分支：** `c7-g3-diag-v2-r1-fastpath`  
**基线：** `ff34219185d1b0f5e07afb31e08b4060b365c1ca`  
**更新时间：** 2026-11-02

## 当前结论

R21-C1 原始报告记录 C0=9/24、C4=24/24、配对 C4 wins=15、C0 wins=0、both=9，报告 McNemar exact p=0.000061035。

但是 R22 的 `scripts/_r22_review.py` 没有真正比较 manifest 哈希、没有严格逐单元断言、没有完整 DAC 依赖/动态隔离测试，且最终 PASS 文本无条件打印；`scripts/_r22_gates.py` 还硬编码 R21 review PASS，与 `status.json` 的 PENDING 状态冲突。

因此，**R22 的完整独立复审 PASS 暂不接受为已充分证明**。这不等于 R21 原始结果已被推翻，而是需要 R23 完成真正的可复现独立复审。

## 当前硬门禁

- R21-C1 独立复审：`PROVISIONAL_REQUIRES_R23_REAUDIT`；
- PC1 协议：`PROPOSED_NOT_APPROVED`；
- 历史 PC1 复审：`REQUEST_CHANGES_REQUIRES_CURRENT_BRANCH_REAUDIT`；
- 正式 G3：`FAIL`；
- PC1：未执行；
- 控制器训练：未授权、未启动；
- Family C：禁止访问。

## R23 执行顺序

1. 修复 R22 审查脚本缺陷，建立真正 fail-closed verifier 和 tamper tests；
2. 独立复算 R21-C1 数据、哈希、账本、分组和配对统计；
3. 审计 DAC 全依赖闭包和动态 gold isolation；
4. 当前分支逐项复核 PC1 历史 blocker，修复离线缺陷；
5. 分解正式 G3 FAIL 的具体机制和判据；
6. 冻结 M1 ECOS 控制器训练方案、基线、任务拆分、预算和停止规则；
7. 取得当前 commit 的独立复审 ACCEPT、可信 Planner 批准、正式 G3 通过及 PC1 批准/执行通过；
8. 只有上述门禁全部通过，才启动真实演化控制器训练。

## 明确禁止

本轮不执行 PC1、不执行正式 G3、不启动控制器训练、不访问 Family C、不微调 Qwen。DAC 作为所有控制器实验臂共享的固定组件，不得把其收益归因于 PPO。

## 执行文件

- 完整 Executor 指令：[`planner/GLEPPO_R23_REAUDIT_AND_TRAINING_GATE_PROMPT.md`](GLEPPO_R23_REAUDIT_AND_TRAINING_GATE_PROMPT.md)
- 接班提示词：[`planner/GLEPPO_R23_HANDOFF.md`](GLEPPO_R23_HANDOFF.md)
- R22 静态复核：[`research/R22_REVIEW_HARNESS_STATIC_REASSESSMENT.md`](../research/R22_REVIEW_HARNESS_STATIC_REASSESSMENT.md)
