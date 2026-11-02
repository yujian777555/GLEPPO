# GLEPPO 最新执行计划 — R24 纠偏审计与门禁顺序修复

**仓库：** `yujian777555/GLEPPO`  
**工作分支：** `c7-g3-diag-v2-r1-fastpath`  
**R23 基线：** `2c66291ea896246a4f90b1f713c81a7ce931682c`  
**更新时间：** 2026-11-02

## 当前结论

R23 是有价值的阶段性进展，但静态复核发现其部分审计宣称仍缺乏可执行证据：
- R21-C1 报告结论为 `ACCEPT_WITH_LIMITATIONS`；
- 十项 tamper 场景只生成了临时损坏副本，没有实际调用 verifier；
- verifier 的 seed、unit-key/group、manifest size/hash 和 ledger provenance 检查仍不完整；
- C4 `source_valid` 仍是 `effective_success` 的代理；
- DAC AST 审计仅扫描一个文件并无条件打印 PASS；
- PC1 matrix 是历史摘要，当前分支逐项复核尚未完成；
- G3 最终效能门与训练前置条件形成循环；
- PC1 与 ECOS preregistration 的 reward 尚未对齐；
- R23 的 450/450 测试尚无与精确 R23 SHA 绑定的可检索 CI 证据。

详细证据：`research/R23_STATIC_REASSESSMENT.md`。

## 当前硬状态

- R21-C1：`ACCEPT_WITH_LIMITATIONS_REQUIRES_FINAL_INDEPENDENT_REVIEW`；
- PC1 协议：`PROPOSED_NOT_APPROVED`；
- PC1 当前分支 blocker audit：`NOT_COMPLETE`；
- Formal G3：`FAIL`；
- ECOS controller training：`NOT_AUTHORIZED_NOT_STARTED`；
- Family C：禁止访问；
- R24：仅允许离线代码、协议和测试修复；不允许模型/API 调用。

## R24 工作顺序

1. 参数化 R21 verifier，让 tamper tests 真正对临时副本执行并断言拒绝；
2. 补齐精确 seed、unit-key、split、manifest、ledger provenance 和 C4 outcome semantics；
3. 完成 DAC 真实依赖路径审计及实际运行的 metamorphic tests；
4. 对历史 PC1 findings 逐项复核当前代码和测试；
5. 提出 G3-PREFLIGHT / G3-EFFICACY 双阶段门禁修订，消除训练前置循环；
6. 对齐 PC1 与 ECOS reward，补齐 state/action/operator/PPO/数据拆分/统计/预算；
7. 在 exact R24 SHA 上运行 CI、全量测试和 clean-clone；
8. 交由独立 reviewer 复审，不得自我批准。

## 科学实验顺序提案（须独立审查与授权）

`G3-PREFLIGHT`（训练前安全与工程正确性）
→ `PC1`（协议审批后执行 A/B-only myopia diagnostic）
→ `ECOS controller training`（PC1 达到预注册 GO 后）
→ `G3-EFFICACY`（训练后在未见确认集评估因果改进）。

原 Formal G3 状态仍为 FAIL。不能将 preflight 结果改写成正式 G3 PASS。PC1 和训练均须分别满足审批门禁。

## 执行文件

- 静态复核：`research/R23_STATIC_REASSESSMENT.md`
- R24 执行提示词：`planner/GLEPPO_R24_CORRECTIVE_AUDIT_PROMPT.md`
- R24 接班提示词：`planner/GLEPPO_R24_HANDOFF.md`
