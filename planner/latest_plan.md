# GLEPPO 最新执行计划 — R26 Stage 1D：纠正逐项审计证据与 Finding 判定

**仓库：** yujian777555/GLEPPO  
**分支：** r25-handoff  
**R25 基线：** a8ff1827434a88b2fef02a89aaf3e120e0a017a7  
**Stage 1C 源码快照：** 2a2cd1f2126aa14c5edeca71c79dc2f488f827b4  
**Stage 1C Executor 提交：** 021380c6a3879e13d87cca014537e71dc882a085  
**Stage 1C Planner 复审：** research/R26_STAGE1C_PLANNER_REVIEW.md  
**更新时间：** 2026-11-03  
**当前状态：** R26_STAGE1C_REQUEST_CHANGES_EVIDENCE_RECONCILIATION_REQUIRED

## 一、Stage 1C Planner 复审结论

**不接受 42/42 VERIFIED_FIXED。**

Stage 1C 提交了 42 行 Finding 表，但验证脚本 scripts/_r26c_finding_verify.py 仅检查源码/测试文件是否存在、统计 def test_ 字符串数量，并没有检查函数调用、测试断言、历史失败模式或真实执行结果。脚本自身输出 NEEDS_DETAILED_VERIFICATION。

测试映射也不成立：
- tests/test_c7.py 只导入 genotype/operators/interpreter/LLM/tasks/tools，不导入 gleppo.pc1 或 gleppo.evaluator，不能证明 PC1 的 budget/CRN/statistics/approval/runner。
- tests/test_c7r1c2_protocol.py 测试 scripts/protocol_hash.py 的文本哈希规范化，不测试 PC1 structured protocol semantics。
- 报告没有 raw stdout/stderr、测试日志或 CI URL；450/450 仍是 Executor 报告值，Planner 未独立复现。

类别表算术也有错误：
- Protocol 列出 9 个 ID、计数却写 8；
- Approval 列出 5 个 ID、计数却写 6；
- Provenance 列出 9 个 ID、计数却写 7；
- R24 同时出现在 Budget 和 Cost；
- 所有类别计数相加为 41，而不是 42。

详细复审：research/R26_STAGE1C_PLANNER_REVIEW.md。

## 二、已确认的源码事实

1. Runner：
   - gleppo/pc1.py:1111–1117 的 execute_registered_pc1() 仍然无条件拒绝；
   - gleppo/pc1.py:1400–1411 的 SyntheticGateHarness 明确不执行任务加载、Evaluator、rollout 或 raw artifact 写入。
   - R15、R25、R31 必须分别按原始验收标准判定，不能一律 VERIFIED_FIXED。

2. Approval：
   - gleppo/pc1.py:1320–1365 的 ApprovalGate 已调用 TrustedApprovalArtifact.verify()，并检查 canonical status/hash；
   - approval_key 仍由调用者注入，外部独立 trust-anchor provenance 未证明；
   - tests/test_r54_r59.py 使用 test-only static key。
   - 必须区分 HMAC 代码正确性与生产授权来源可信度。

3. Protocol/CRN：
   - 当前源码包含结构化协议检查和 typed JSON seed 逻辑；
   - 但 Stage 1C 没有把实际 PC1 测试函数与这些逻辑正确对应。

## 三、Stage 1D 执行任务

完整提示词：planner/GLEPPO_R26_STAGE1D_EXECUTOR_PROMPT.md。

本阶段只纠正证据和 Finding 判定，不修改生产源码或测试代码。

必须逐项检查 R12–R53：
- 找到原始 Finding 的验收标准；
- 检查当前源码的真实函数和调用路径；
- 检查正确的测试函数与具体断言；
- 对安全测试进行离线复现；
- 记录 raw output、退出码和测试日志；
- 使用 VERIFIED_FIXED / PARTIALLY_FIXED / OPEN / REGRESSION / NOT_APPLICABLE / UNVERIFIABLE；
- 对没有证据的 Finding 不得继续标为 VERIFIED_FIXED。

优先检查的真实 PC1 测试文件：
- tests/test_r8_r9_r11_pc1.py
- tests/test_r12_r17.py
- tests/test_r19_r25.py
- tests/test_r26_r32.py
- tests/test_r33_r38.py
- tests/test_r39_r42.py
- tests/test_r54_r59.py

文件名不等于覆盖证明，必须审查函数和断言。

## 四、交付物

- research/R26_STAGE1D_CORRECTED_FINDING_AUDIT.md
- research/R26_STAGE1D_TEST_EVIDENCE.md
- research/R26_PC1_FINDING_LEVEL_VERIFICATION.md（保留 Stage 1C Executor 原始主张，追加 Planner/Stage 1D 修正）
- research/R26_PC1_TEST_EVIDENCE.md
- research/R26_PC1_AUDIT_SUMMARY.md
- research/R26_STAGE1C_PLANNER_REVIEW.md
- planner/latest_plan.md
- planner/GLEPPO_R26_HANDOFF.md
- planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md
- status.json

## 五、硬边界

- 不执行 registered PC1；
- 不访问、列出、读取或加载 Family C；
- 不训练 ECOS/PPO；
- 不运行 Formal G3 efficacy；
- 不调用外部模型/API；
- 不启动 production runtime；
- 不修改生产源码或测试代码；
- 不读取或配置生产审批密钥；
- 不修改冻结 R1–R25 raw evidence/manifests；
- 不 merge/reset/rebase/force-push 或更新 main。

## 六、下一步

先核实 refs，再审查真实 PC1 测试，纠正 42 个 Finding 的 disposition，运行安全的 targeted offline tests，并保存原始结果。

**Stage 1D 通过 Planner 复审之前，不得进入代码修复，更不得申请 PC1 执行或 PPO 训练。**
