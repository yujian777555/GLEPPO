# GLEPPO 最新执行计划 — R21-C1 复审与 R22 控制器训练门禁

**仓库：** `yujian777555/GLEPPO`  
**工作分支：** `c7-g3-diag-v2-r1-fastpath`  
**R21-C1 基线：** `90f964a9ddc9eabd0096cb504755bd1c7c13c23a`  
**更新时间：** 2026-11-02

## 当前结论

R21-C1 报告为 GO：C0 有效成功 9/24，C4(DAC) 24/24，配对 C4 wins=15、C0 wins=0，McNemar exact p≈0.000061。该结果支持 DAC 在当前八个任务上的有效性，但不是演化控制器训练结果，也不能证明普遍泛化。

## 当前硬门禁

- R21-C1 独立复审：待在当前准确 commit 上完成；
- PC1 协议：`PROPOSED_NOT_APPROVED`；
- 历史 PC1 独立复审：`REQUEST_CHANGES`，必须对当前分支逐项复核；
- 正式 G3：`FAIL`；
- PC1：未执行；
- 控制器训练：未授权、未启动；
- Family C：禁止访问。

**不得把 R21-C1 的 GO 当作 PC1 批准或训练许可。**

## 下一阶段顺序

1. R21-C1 原始证据独立复算与 DAC 无金标泄漏审计；
2. 修复并复核 PC1 历史审查中的全部 blocker；
3. 验证 A/B 训练集与验证集真正按任务/模板隔离；
4. 冻结 EC 控制器训练算法、状态/动作/奖励、强基线、种子、预算和停止条件；
5. 取得可信 Planner 批准、独立复审 ACCEPT、production runtime 与正式 G3 通过；
6. PC1 获批并通过后，才启动真实 EC 控制器训练；
7. 训练后在未见确认任务上独立评估。

## 执行规范

完整 Executor 指令：[`planner/GLEPPO_R22_CONTROLLER_TRAINING_PROMPT.md`](GLEPPO_R22_CONTROLLER_TRAINING_PROMPT.md)  
接班提示词：[`planner/GLEPPO_R22_HANDOFF.md`](GLEPPO_R22_HANDOFF.md)

本轮允许离线审计、修复、测试、预算和训练预注册；不允许绕过 PC1/G3 门禁启动训练。
