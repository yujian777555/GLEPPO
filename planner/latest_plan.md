# GLEPPO 最新执行计划 — R26 Stage 1I-R1

**仓库：** yujian777555/GLEPPO  
**项目边界：** 仅 GLEPPO；不得混入 openissue、agentfotagent、CausalEvo-DSH、EvoPareto-Agent 或其他项目  
**工作分支：** r25-handoff  
**更新时间：** 2026-11-04  
**Stage 1I Executor commit：** a1e6e65e671c876d028492bfed164205c54df08b  
**Stage 1I Planner review：** research/R26_STAGE1I_PLANNER_REVIEW.md  
**Planner decision：** REQUEST_CHANGES  
**当前任务：** Stage 1I-R1 corrective completion；尚未验收  
**Executor prompt：** planner/GLEPPO_R26_STAGE1I_CORRECTIVE_EXECUTOR_PROMPT.md

---

## 一、当前 Planner 决策

**R26 Stage 1I 不接受。必须留在 Stage 1I，完成 Stage 1I-R1 后重新独立复审。**

本轮核实了远端 r25-handoff HEAD 为 a1e6e65e671c876d028492bfed164205c54df08b，main 为 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e，分支相对 main ahead 202 / behind 0。Stage 1I commit 仅新增两份报告和一个 helper，并修改 status.json；未更新 latest_plan、handoff、next-session prompt 或累计 PC1 summary。

独立审查报告：research/R26_STAGE1I_PLANNER_REVIEW.md。

## 二、为什么 Stage 1I 未通过

### F1：42 个 Finding 的语义证据矩阵缺失

要求的 research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.md 不存在。最终审计报告 73 行、测试证据 34 行，均没有 R12–R53 的完整逐项矩阵。

因此无法独立检查每个 Finding 的：
- 原始 review、问题标题和完整验收条件；
- 真实断言、测试行号和源码符号；
- test → source 的调用路径及目标分支；
- 直接证据、间接证据、手工证据和无证据项；
- 已证明/未覆盖条件；
- 每个 Finding 的 disposition 和理由。

26/14/1/1 加总为 42，但没有 42 行数据支撑，不能视为已验证的分类结果。

### F2：_r26i_validator.py 没有验证实际报告

- 主程序不读取语义证据表；
- 主程序不调用 validate_report_map()；
- 只输出 class/function 数量；
- 没有比较报告 test_file 与真实声明所属文件；
- 不拒绝未知额外 ID；
- 不检查 42 行、39 mapped / 3 NONE；
- 缺失测试文件会被静默跳过；
- 没有 helper 自测输出或 CI 证据。

下一轮必须用 AST 构建按文件/类/函数索引的声明清单，读取真实 JSON map，验证 ID/cardinality、文件归属、函数和行号，并提供负向自测。helper 只能验证结构与声明映射，不能证明语义。

### F3：长期接班记录没有更新

Stage 1I commit 没有更新：
- planner/latest_plan.md；
- planner/GLEPPO_R26_HANDOFF.md；
- planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md；
- research/R26_PC1_AUDIT_SUMMARY.md。

status.json 虽有变更，但 Stage 1I 对象过度简化，丢失 prompt、scope、硬门禁和下一动作等关键状态；durable-doc commit 引用和 top-level current_task/next_gate 仍陈旧。

### 其他待修正

- R53 改为 status-consistency test 仅是间接证据，未证明 status-only hash invariance；必须保持 PARTIALLY_FIXED。
- R39 的 R16/R20 cross-genotype evaluator 测试有价值，但证据文件未完整列出 R20；需要区分 genotype 行为测试、action 结构性排除和未测试的 action-varying collector integration。
- test_operator_rng_independent_of_eval_seed 实际改变 draw index 并检查不相等，不等于直接证明与 eval seed 独立。
- R18 手工证据已有明显改进，但缺少 COST_BASELINE.md line 44 的明确引用，且必须进入完整 Finding row。
- Stage 1I 报告的 CURRENT_BRANCH_HEAD=e2cb353 是 Stage 1I parent/pre-work HEAD，不是最终 Stage 1I commit；下一轮要区分 parent、source snapshot、Executor commit 和 final HEAD。
- GitHub 对 Stage 1I SHA 返回 0 check runs / 0 status entries。450/450 仍为 EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED。

## 三、Stage 1I-R1 唯一当前任务

执行：planner/GLEPPO_R26_STAGE1I_CORRECTIVE_EXECUTOR_PROMPT.md。

必须交付：

1. research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json：规范化机器可读 42 Finding map。
2. research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.md：人类可读的 42 行表。
3. scripts/_r26i_validator.py：AST 声明映射验证器，必须读取实际 JSON map 并执行校验。
4. validator self-test：有效样例通过；错误文件/类/函数/行号、缺失/重复/未知 ID、非法 NONE、缺失源文件、映射数量错误均 fail。
5. research/R26_STAGE1I_R1_CORRECTIVE_REPORT.md：实际执行结果、行级证据、SHA 和边界声明。
6. 更新 Stage 1I audit/test evidence、PC1 cumulative summary、latest_plan、handoff、next-session prompt、status.json。

Disposition 必须从 42 行 JSON map 机械统计，不得预设 26/14/1/1。R53 必须保持 PARTIALLY_FIXED，除非未来获得新授权并完成直接 hash-invariance 证据。R39 需准确标出 action/genotype 证据边界。R18 为 MANUAL，无行为测试。

本轮仅允许文档、JSON map 和非生产审计 helper 修改；不允许修改 tests/ 或生产源码。

## 四、ECOS 科学完整性边界

GLEPPO 的研究假设仍然保留，但 PPO 优势尚未证明。

- R21-C1 是 C0 LLM 算术执行 vs C4 DAC 确定性答案计算，不是演化算子/控制器对照。
- 固定算子是否不足：UNTESTED。
- 自适应选择是否优于最佳固定算子：UNTESTED。
- PPO 是否优于规则控制器：UNTESTED。
- PPO 是否优于相同状态输入的 LinUCB/Neural Bandit：UNTESTED。
- Phase 1、R24、PC1 R4 与共享实现的 reward/state/gamma/split/budget 仍需统一审查；不能静默选择一个版本。

独立科学性审查：research/R26_ECOS_SCIENTIFIC_INTEGRITY_REVIEW.md。

## 五、Stage 1I-R1 之后的顺序

1. Executor 完成 Stage 1I-R1 并推送。
2. Planner 独立审查完整 42-row map、helper 和负向自测输出。
3. 只有 Stage 1I 被正式接受后，才进入独立的 R26_ECOS_PROTOCOL_RECONCILIATION。
4. 协议统一并通过独立科学审查后，才讨论 PC1 审批。
5. PC1 批准与执行仍需所有门禁和用户授权；PC1 PASS 也不等于 PPO 优于 Bandit。
6. 训练必须另行授权；正式 G3 efficacy 仍需独立评估。

## 六、硬边界

- PC1 BLOCKED；PC1 R4 PROPOSED / NOT APPROVED。
- Formal G3 FAIL。
- Family C NOT ACCESSED，持续禁止访问。
- Registered PC1 NOT EXECUTED。
- Controller training NOT AUTHORIZED / NOT STARTED。
- No production runtime / model API calls / signing-key access。
- No production source or tests/ modifications in Stage 1I-R1.
- No frozen R1–R25 evidence/manifest changes.
- No main update/merge/reset/rebase/force-push.
- No cross-project code/data/report reuse.

**当前唯一动作：完成 Stage 1I-R1，提交后等待 Planner 独立复审。不得提前进入 PC1、协议统一或训练。**
