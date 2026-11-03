# GLEPPO 最新执行计划 — R26：PC1 当前分支逐项审计

**仓库：** yujian777555/GLEPPO  
**当前延续分支：** r25-handoff  
**R25 基线：** a8ff1827434a88b2fef02a89aaf3e120e0a017a7  
**更新时间：** 2026-11-03  
**当前状态：** R26_READY_FOR_PC1_CURRENT_BRANCH_AUDIT

## 一、R25 最终结论

R25 独立复审结论为 **R25_ACCEPTED_WITH_LIMITATIONS**：

| 项目 | 当前状态 | 解释 |
|---|---|---|
| R21-C1 | ACCEPT | 独立复审接受，保留 C4 outcome 语义限制 |
| DAC | ACCEPT | 金标隔离审计接受；不是完整 taint analysis 证明 |
| PC1 | BLOCKED | 历史 findings 尚未完成当前分支逐项复核 |
| G3-PREFLIGHT | READY | 仅工程预检，不等于正式 G3 efficacy PASS |
| ECOS | ACCEPT_WITH_LIMITATIONS | PPO 必要性尚未证明，规则控制器可能足够 |
| Formal G3 | FAIL | 原状态保持 |
| Family C | NOT ACCESSED | 继续禁止访问 |
| Controller training | AUTHORIZATION_REQUIRED | 未授权、未启动 |

R21-C1 的 R25 审查记录：24 units、8 tasks、3 seeds、DEV/CONFIRM disjoint、96 ledger rows、token delta 3620、McNemar p=0.000061035、tamper 10/10。C4 使用 source_valid 作为 effective_success 的代理，必须保留这一语义假设，不得改写为无条件等价。

## 二、重要仓库引用说明

R25 提交 SHA：a8ff1827434a88b2fef02a89aaf3e120e0a017a7。

本轮通过 GitHub 连接读取时，main/status.json 仍呈现 2026-10-27 的旧状态，而 R25 commit 可按 SHA 读取、未出现在返回的 branch list 中。为避免在旧 main 上覆盖状态，已从精确 R25 SHA 创建 r25-handoff 分支。后续必须先核实远端 refs；不得盲目 merge、reset 或 force-push main。

## 三、R26 当前任务

### Stage 0 — 精确恢复
- 检查 r25-handoff 的 HEAD、远端 SHA、工作区状态及 R25 ancestry。
- 阅读 R25 六份审查报告、status.json、R26 prompt/handoff。
- 核对 main 是否已同步 R25；未核实前继续在 r25-handoff 工作。

### Stage 1 — PC1 历史问题完整盘点
R25 汇总称“约 43 项、10 轮”，但分类表当前能数出 39 个命名 ID：
- Seed/CRN：R8、R16、R20、R34、R39（5）
- Budget/CTX：R9、R21、R27、R28、R33（5）
- Protocol：R19、R26、R36、R40、R45、R48、R49、R53（8）
- Approval：R38、R42、R43、R46、R50、R54、R59（7）
- Plan/provenance：R22、R29、R35、R37、R41、R44、R47、R51、R55、R58、R60（11）
- PC1 runner：R15、R25、R31（3）

必须检索原始十轮报告，核对遗漏、重复和交叉分类，解释 39 与“约 43”的差异。不要把约数冒充精确统计。

建立 finding-by-finding 审计矩阵：原始描述、报告轮次、当前源码位置、现有测试、独立复现命令与结果、状态分类、证据、修复和验收标准。不能仅凭旧 status、commit message 或 Executor 汇报判定 FIXED。

### Stage 2 — 离线修复与验证
- 只修复已确认且影响科学有效性、预算、协议、溯源或安全门禁的问题。
- 每项修复配套回归测试，分小提交完成。
- 只运行 offline tests 和 synthetic PC1 fixtures。
- 历史 R1–R25 原始证据和 manifest 冻结，不得重写。
- 保持 default-deny；synthetic test 不得标成 registered PC1。

### Stage 3 — PPO 必要性审查
按 R25 要求设计 A0–A3：
- A0：Fixed strategy
- A1：Random intervention
- A2：Deterministic rule-based controller
- A3：PPO ECOS

先核对当前 ECOS preregistration 的 state/action/reward/5 operators/episode/splits/budget/stopping rules，并盘点是否存在可复现的 A3 checkpoint。若没有，必须明确 A3 需要训练；A0–A2 结果不能证明 PPO 优越性。冻结 primary metrics、统计功效、种子、预算和 decision thresholds 后，才可申请后续阶段审批。DAC 必须作为所有 arm 共享的固定组件。

指标至少包括 effective_success_rate、answer_accuracy、tool_path_validity、format_compliance、constraint_violation_rate、适用时的 hypervolume、inference/training cost。必须审计 reward hacking 和 reward/evaluator mismatch。

## 四、不可越过的门禁

当前 R26 不授权：
- registered PC1 execution；
- Family C 的加载、检查、调参或执行；
- ECOS/PPO controller training；
- formal G3 efficacy rerun；
- 新的外部模型/API 调用；
- 修改冻结的 R1–R25 evidence/manifests。

后续顺序仍需满足：R26 当前分支审计与离线修复 → 独立复审 → G3-PREFLIGHT → trusted Planner approval + PC1 protocol approval → registered PC1 → 满足 GO 后再单独申请 controller training → G3-EFFICACY。用户授权与各项门禁缺一不可。

## 五、必须交付的文件

- research/R26_PC1_CURRENT_BRANCH_FINDING_AUDIT.md
- research/R26_PC1_REMEDIATION_REPORT.md
- research/R26_ECOS_A0_A3_COMPARISON_PROTOCOL.md
- planner/latest_plan.md
- planner/GLEPPO_R26_HANDOFF.md
- planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md
- status.json

尚未完成的报告标记 NOT_STARTED，不得创建空壳并声称完成。

## 六、下一条 Executor 任务

**先做只读盘点，不训练、不执行 PC1：**检索原始十轮 PC1 review reports，完成所有历史 finding 的精确清单和 39/约43 数量核对；随后将每个 finding 映射到 r25-handoff 当前源码、测试和可复现证据，形成完整审计矩阵。完成后提交独立复审材料，再决定是否进入离线修复。

每轮结束记录 base SHA、result SHA、final HEAD、remote branch/SHA、文件清单、测试命令与结果、API/model calls、PC1/Family C/training 状态和剩余阻塞项。

## R26 Stage 1 Executor 提示词

已新增可直接交给执行端的详细任务提示词：

- planner/GLEPPO_R26_STAGE1_PC1_AUDIT_EXECUTOR_PROMPT.md
- 提示词创建提交：02ac15adf70d243b1e78da9b118bfa468c64e24a
- R26 延续锚点：3558c65b704efa05bf1f7ad85a2bebf89b1f4414（执行前要求当前 HEAD 是该锚点及 R25 基线的后代，并记录真实本地/远端 SHA；不要求 HEAD 与锚点相等，因为其后已有接班文档提交）

该提示词要求先恢复仓库引用，再检索原始十轮 PC1 审查记录，核对 39 个命名 ID 与“约 43 项”的差异，并逐项映射当前源码、测试和复现证据。Stage 1 只允许审计文档与状态维护，不允许修改源码。

硬边界保持不变：registered PC1 不执行、Family C 不访问、ECOS/PPO 不训练、Formal G3 不重跑、模型/API 调用为 0。

