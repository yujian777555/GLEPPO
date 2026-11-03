# GLEPPO 最新执行计划 — R26 Stage 1B：Finding 台账纠偏与当前源码审计

**仓库：** yujian777555/GLEPPO  
**分支：** r25-handoff  
**R25 基线：** a8ff1827434a88b2fef02a89aaf3e120e0a017a7  
**R26 Stage 1 Executor 提交：** 60f60e5c40ef65b6b5395182d322863780e9784f  
**更新时间：** 2026-11-03  
**当前状态：** R26_STAGE1_PRELIMINARY_INVENTORY_ACCEPTED_WITH_CORRECTIONS_REQUIRED

## 一、Planner 对 R26 Stage 1 的结论

Stage 1 找到了 SECOND 至 TENTH 九份审查文件，并完成初步编号比较；所有候选项均标记为 UNVERIFIABLE，没有冒称修复通过。

但 Planner 独立检查发现，43 项的计数算法不可靠：
- scripts/_r26_findings.py 把 “R60-R61 Independent Review Result” 当成 R60 Finding；
- 该正则遗漏 Markdown 表格中的加粗编号；
- THIRD 至 TENTH 中可确认的正式 Finding 标题是 R12-R53，共 42 个；
- SECOND 中有 5 个编号 blocker bullets，而 status.json 记录 6 个 blocker，因为其中一个 bullet 合并了 accounting 与 smoke-slot 两个问题；
- R8-R11、R54-R61 出现在 Executor remediation logs，不能不加区分地当成独立审查 Finding；
- Stage 1 审计文件只有数量摘要，没有逐项源码/测试/复现矩阵。

因此，“43 unique findings”暂不作为最终统计结论。正式审查 Finding、无编号 blocker、Executor remediation item、review result 和重复/拆分问题必须分别登记、去重后再报告。

详细 Planner 复审：research/R26_STAGE1_PLANNER_REVIEW.md。

## 二、R26 Stage 1B 当前任务

执行提示词：planner/GLEPPO_R26_STAGE1B_EXECUTOR_PROMPT.md。

### Work Package A — 建立历史 Finding Register

1. 检索 FIRST review 是否存在；Stage 1 仅恢复 SECOND–TENTH。
2. 手工检查 SECOND–TENTH 原始报告。
3. 区分正式审查 Finding、无编号 blocker、Executor remediation item、review result、交叉引用、重复/拆分问题。
4. 核对 R25 表 39 个标签与历史原始记录。
5. 解释 SECOND 五条 blocker bullet 与 status.json 六项 blocker 的差异。
6. 形成 research/R26_PC1_FINDING_REGISTER.md，分别报告各类记录数和去重后的 actionable issue cluster 数。不能强行凑成 43。

### Work Package B — 当前分支源码验证

对每个 distinct actionable issue：
- 映射当前源码路径、函数/类和行号；
- 映射实际相关测试函数；
- 检查测试体是否真正覆盖问题；
- 运行安全的 offline reproduction/test；
- 记录输出、退出码和证据；
- 分类 VERIFIED_FIXED / PARTIALLY_FIXED / OPEN / REGRESSION / NOT_APPLICABLE / UNVERIFIABLE；
- 记录残余风险、最小修复建议和验收标准。

优先审计 seed/CRN、budget/CTX、统计样本与 provenance、protocol hash/schema、trusted approval、plan identity、PC1 runner 和 gate sequence。

### Work Package C — 交付

- research/R26_PC1_FINDING_REGISTER.md
- research/R26_PC1_CURRENT_BRANCH_FINDING_AUDIT.md（完整逐项矩阵）
- research/R26_PC1_AUDIT_SUMMARY.md
- research/R26_STAGE1_PLANNER_REVIEW.md
- planner/latest_plan.md
- planner/GLEPPO_R26_HANDOFF.md
- planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md
- status.json

Stage 1B 是只读审计。不得在本阶段修复生产源码。

## 三、当前科学门禁状态

| 项目 | 状态 |
|---|---|
| R21-C1 | ACCEPT（保留 C4 source_valid/effective_success 代理语义限制） |
| DAC | ACCEPT（不是完整 taint-analysis 证明） |
| PC1 | BLOCKED |
| G3-PREFLIGHT | READY（仅工程预检） |
| ECOS 协议 | ACCEPT_WITH_LIMITATIONS |
| Formal G3 | FAIL |
| Family C | NOT ACCESSED |
| Controller training | AUTHORIZATION_REQUIRED / NOT STARTED |

A0-A3 PPO 必要性比较仍是后续研究任务；Stage 1B 不执行训练、不读取 checkpoint 以外的 Family C 资源，也不做新模型调用。

## 四、硬边界

- 不执行 registered PC1；
- 不访问、列出、读取、加载或执行 Family C；
- 不训练 ECOS/PPO；
- 不运行 formal G3 efficacy；
- 不发起外部模型/API 调用或 production runtime；
- 不修改 R1-R25 冻结 raw evidence/manifests；
- 不修改生产源码；
- 不 merge/reset/force-push main；
- 不将 synthetic fixture 说成 registered experiment。

## 五、Stage 1B 完成标准

只有当历史台账有明确的记录类型与去重规则、FIRST 报告搜索结果已说明、每个 distinct actionable issue 均有当前源码/测试证据或明确 UNVERIFIABLE 理由、所有运行测试均可复现且未越过门禁时，才可提交 Planner 独立复审。

若一次不能完成全部矩阵，明确标记未完成域，保持 PC1 BLOCKED。不得为了阶段完成而将未审项目改成 OPEN 或 VERIFIED_FIXED。

**下一步：执行 Stage 1B 提示词。先核实 refs，再建立 finding register 和当前源码逐项验证矩阵。**
