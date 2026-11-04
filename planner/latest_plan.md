# GLEPPO 最新执行计划 — R26 Stage 1I-R2

**仓库：** yujian777555/GLEPPO  
**分支：** r25-handoff  
**更新时间：** 2026-11-04  
**Stage 1I Executor HEAD：** a1e6e65e671c876d028492bfed164205c54df08b  
**Stage 1I Planner review：** dfd7ef909ba4ee97e01c4bb57b0177ae8869d61c  
**Stage 1I-R1 Executor HEAD：** 4d2ff06ee01146533501589b264d33ddd30ffcbe  
**Stage 1I-R1 Planner review：** dcdcef5b2e7e68a6590d95c90c4caf453399c127  
**R1 source snapshot：** 29325cfa16441154c833f381f208747b57627a79  
**Planner decision：** R1 REQUEST_CHANGES  
**当前任务：** Stage 1I-R2 corrective completion  
**Executor prompt：** planner/GLEPPO_R26_STAGE1I_R2_CORRECTIVE_EXECUTOR_PROMPT.md

---

## 一、当前决策

**Stage 1I-R1 不接受。继续留在 Stage 1I，完成 R2 后重新独立复审。**

R1 的结构性成果得到认可：
- JSON map 有 42 个唯一 ID，R12–R53；
- Markdown 有 42 个唯一标题；
- JSON 与 Markdown 的处置一致；
- 26/14/1/1 的机械统计正确；
- R53 保持 PARTIALLY_FIXED；
- R18 的 13 条手工证据和单位区分基本完整；
- 生产源码和 tests/ 未修改；
- durable handoff 文件已更新。

但语义证据仍不可靠。部分测试并未到达其声称证明的代码分支，部分调用链和源码符号错误，多个 Finding 漏掉已有的直接测试，且验证器允许空行号和未解析的 source symbol 通过。

完整审查：research/R26_STAGE1I_R1_PLANNER_REVIEW.md。

## 二、R1 的主要阻塞项

### F1：多项 Finding 没有枚举全部相关测试

重点包括：
- R12：只引用初始化计数测试，漏掉 cache hit 不增加 replica 的直接测试。
- R14：漏掉 r_hat 包含 extra_immediate 的直接测试。
- R17：漏掉 evidence record 字段测试，且 counter breakdown 未证明。
- R20：漏掉 task/rollout/replicate 与 override-path 测试。
- R23：漏掉 save/load/replay round-trip 测试。
- R39：7 个直接 CRN 测试没有完整进入结构化证据数组，R20 cross-genotype test 也没有作为完整证据条目。
- R40：只列 happy-path，遗漏版本、seed、reward mutation tests。
- R41：遗漏 tamper、defensive-copy、wrong-hash tests。
- R28：映射到常量检查测试，而不是实际调用 reconcile 的测试。

### F2：存在错误的 test-to-source 调用链

重点包括：
- R20：Evaluator.effective_seed_parts 不调用 pc1.crn_seed；crn_seed 实际位于 gleppo/pc1.py。
- R28：test_registered_budget_exact 只检查常量，不调用 BudgetLedger.reconcile。
- R30/R37：测试实际调用 run_pc1_analysis，缺失字段在 validate_records 之前被拒绝。
- R44：loader 单测不能替代注册分析端到端 artifact 绑定测试。
- R47：alternative mapping 测试在注册哈希比较处失败，没有到达 plan ID/version 分支。
- R50：test_wrong_protocol_hash_rejected 直接调用 art.verify，不是 ApprovalGate.check。
- R51：测试比较 REGISTERED_PROTOCOL_CONTENT_HASH，不是 REGISTERED_PLAN_HASH。
- R52：validate_reward_schema 在源码中不存在。

### F3：source symbol 不完整

R17、R20、R23、R24、R25、R26、R48、R51、R52 有 null source line range；部分符号不存在或文件路径错误。

### F4：验证器仍然有缺口

- wrong_file_path 自测使用不存在的文件，与 missing_source_file 重复。
- null declaration_start_line/end_line 可绕过行号比较。
- source_symbols 的文件和行号完全没有被校验。
- schema_version 和多项字段类型没有严格校验。
- branch_reached 的说明仍有与实际调用路径不符的通用模板。

### F5：处置结论存在过度确认

R12、R17、R26、R28、R40、R44、R51 等 VERIFIED_FIXED 行的证据没有证明全部验收条件。机械计数正确不代表语义分类正确。R2 必须重新评估全部 42 行，不得强行保留 26/14/1/1。

## 三、Stage 1I-R2 唯一任务

执行：planner/GLEPPO_R26_STAGE1I_R2_CORRECTIVE_EXECUTOR_PROMPT.md。

必须完成：

1. 重新核对 8 份原始 review 文件，逐项保留全部验收子条件。
2. 为每个 Finding 枚举所有相关测试，不能只列代表性测试。
3. 修正错误调用链、错误源码符号、错误文件路径和未到达分支的声明。
4. 所有 source symbol 必须有真实文件和非空精确行范围。
5. 根据完整证据重新计算 disposition；不得把旧统计当目标。
6. 强化 AST validator：schema、类型、非空正整数行号、source symbol 路径和范围、branch/harness/manual evidence 均须 fail-closed。
7. 补齐 existing-file/wrong-owner、null line、null source range 等对抗性自测，并要求每项检查对应的具体错误原因。
8. 修正 R1 final SHA 和 source snapshot 的 provenance。
9. 更新所有长期文档和 status.json。

R1 关键纠正要求：
- R28 必须引用 test_ledger_components_sum_to_total。
- R50 必须区分直接调用 TrustedApprovalArtifact.verify 与 ApprovalGate.check。
- R51 不得把协议哈希测试当成 plan hash 测试。
- R52 必须使用真实的 protocol_consistency_check 及其内部校验逻辑。
- R53 仍为 PARTIALLY_FIXED，除非已有直接 hash-invariance 测试；本阶段不得新增 tests。
- R18 保持 MANUAL，生产 tokens/latency UNMEASURED。

## 四、科学完整性状态

GLEPPO 的 ECOS 研究假设仍然保留，但 PPO 优势尚未得到实验证明。

- R21-C1 是 DAC 对照，不是演化算子或控制器对照。
- 固定算子与自适应算子对比：UNTESTED。
- PPO 与规则控制器对比：UNTESTED。
- PPO 与 LinUCB/Neural Bandit 对比：UNTESTED。
- Phase 1、R24、PC1 R4 的 reward/state/gamma/split/budget 定义冲突仍未解决。
- 不得在 Stage 1I-R2 中提前统一协议或训练控制器。

## 五、硬门禁

- PC1 BLOCKED；R4 PROPOSED / NOT APPROVED。
- Formal G3 FAIL。
- Family C NOT ACCESSED。
- Registered PC1 NOT EXECUTED。
- Controller training NOT AUTHORIZED / NOT STARTED。
- 不得修改生产源码或 tests/。
- 不得调用模型/API、生产 runtime 或 signing key。
- 不得修改冻结的 R1–R25 raw evidence/manifests。
- 不得修改/合并 main，不得 reset/rebase/force-push。
- 不得混用其他项目的代码、数据或报告。

**下一步只有：Stage 1I-R2 Executor 完成 → Planner 独立复审。不得进入 R26_ECOS_PROTOCOL_RECONCILIATION、PC1、Family C 或训练。**
