# GLEPPO R23 接班提示词

你接手 GLEPPO 唯一仓库 `yujian777555/GLEPPO`。

- 工作分支：`c7-g3-diag-v2-r1-fastpath`
- R22 基线：`ff34219185d1b0f5e07afb31e08b4060b365c1ca`
- R22 状态：BLOCKED，PC1/G3 门禁未通过。
- R21-C1 报告值：C0=9/24，C4=24/24，配对 C4 wins=15、C0 wins=0、both=9，报告 p=0.000061035。
- 重要纠正：R22 的复审脚本存在验证缺口，完整独立复审 PASS 尚未建立。静态审查说明见 `research/R22_REVIEW_HARNESS_STATIC_REASSESSMENT.md`。
- R22 原始实验数据必须保持不变。

## 立即做什么

1. 先读 `planner/latest_plan.md` 和 `planner/GLEPPO_R23_REAUDIT_AND_TRAINING_GATE_PROMPT.md`。
2. 先实现 R21-C1 真正 fail-closed 的独立 verifier：manifest 实际比较、逐单元覆盖、正确的 C4 effective-success 语义、账本复算、tamper tests。
3. 做 DAC 全依赖闭包和动态金标隔离审计。
4. 对 PC1 历史所有 blocker 在当前准确分支逐项复核，形成矩阵并修复离线缺陷。
5. 对正式 G3 FAIL 做基于既有证据的机制分解。
6. 冻结 EC 控制器训练预注册与预算，但不启动训练。
7. 所有结果更新仓库、状态、接班提示词，并推送。

## 不可违反

- 不切换 main，不混用其他项目。
- 不访问 Family C。
- 不执行 PC1、正式 G3 或真实控制器训练，除非另行获得全部必要审批。
- 不训练/微调 Qwen 基座模型。
- DAC 必须对所有控制器比较臂保持一致，不能将 DAC 的收益归因于 PPO。
- 不得伪造测试、哈希、审批、模型调用、Token 或统计证据。

完整规范见 `planner/GLEPPO_R23_REAUDIT_AND_TRAINING_GATE_PROMPT.md`。
