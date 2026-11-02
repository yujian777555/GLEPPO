# GLEPPO R22 接班提示词

你接手的是 GLEPPO 唯一项目仓库 `yujian777555/GLEPPO`，工作分支 `c7-g3-diag-v2-r1-fastpath`，R21-C1 基线 `90f964a9ddc9eabd0096cb504755bd1c7c13c23a`。

## 当前已知事实
- R21-C1 Run ID：`20261102T131000Z_R21`。
- R21-C1 报告：C0=9/24，C4(DAC)=24/24，McNemar exact p≈0.000061，报告决策 GO。
- 结果位于 DEV 12 个评价单元和 CONFIRM 12 个评价单元；8 个任务各 3 个种子。
- R21-C1 结果不是控制器训练结果。
- 正式 G3 仍 FAIL；PC1 协议仍 PROPOSED_NOT_APPROVED；PC1 未执行；Family C 未访问；控制器未训练。
- 远端 main 与当前 R21-C1 分支不一致；继续工作必须留在 `c7-g3-diag-v2-r1-fastpath`，不能切回 main。
- 原 `planner/latest_plan.md` 是 R4 提案，已归档；新的 latest plan 指向 R22 训练门禁任务。

## 下一步
1. 从最新远端 HEAD 开始，核验工作区与分支。
2. 完成 R21-C1 原始 JSON/ledger/manifest 的独立复算和 DAC 无金标泄漏审计。
3. 完成 PC1 历史独立复审 blocker 的当前代码逐项核验。
4. 训练/验证模板必须真正隔离；修复并测试任何残留缺陷。
5. 先取得可信 Planner 批准、当前 commit 的独立复审 ACCEPT、production runtime 与正式 G3 通过，再执行 PC1。
6. PC1 通过后，按已批准协议训练 EC 控制器；不微调 Qwen，不访问 Family C。
7. 若门禁未通过，停止真实训练，但继续完成离线修复、训练方案、预算、测试和审批材料。

完整执行规范见 `planner/GLEPPO_R22_CONTROLLER_TRAINING_PROMPT.md`。不得虚报模型调用、训练、审批、统计或 Git 操作。
