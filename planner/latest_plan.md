# GLEPPO 最新执行计划 — R26 Stage 1C：逐项 Finding 语义验证

**仓库：** yujian777555/GLEPPO  
**延续分支：** r25-handoff  
**R25 基线：** a8ff1827434a88b2fef02a89aaf3e120e0a017a7  
**Stage 1B 报告提交：** bcdc24f4d3c7bbaf390678670c54f642b9948a99  
**Stage 1B 源码快照：** a1940a220bc2b7cdc4e6ba4fe0c723fbfb33c4ec  
**Stage 1B Planner 复审：** research/R26_STAGE1B_PLANNER_REVIEW.md  
**更新时间：** 2026-11-03  
**当前状态：** R26_STAGE1B_TAXONOMY_MILESTONE_ACCEPTED_FINDING_LEVEL_AUDIT_REQUIRED

## 一、Stage 1B 验收边界

Planner 接受 Stage 1B 的历史分类里程碑：
- 正式审查 Finding 标题：42 个，R12–R53；
- SECOND 无编号 blocker：5–6 个，拆分规则未定；
- TENTH remediation records：8 个，R54–R61；
- R60–R61 Independent Review Result：review-result 标题，不是正式 Finding。

但 42 个正式标题不等于已经证明 42 个独立问题簇。历史跨轮重复、拆分、合并和 SECOND 5/6 差异仍须建立 crosswalk。

Stage 1B 的七域检查脚本 scripts/_r26b_source_audit.py 主要检查关键词是否存在，不是语义源码审计。450/450 测试是 Executor 报告值，Planner 未独立复现，也没有附原始 stdout/stderr 或 CI URL。所有 42 项继续保持 UNVERIFIABLE。

详细复审：research/R26_STAGE1B_PLANNER_REVIEW.md。

## 二、当前仓库引用

Planner 核对时：
- r25-handoff = bcdc24f4d3c7bbaf390678670c54f642b9948a99；
- main = 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e；
- main 相对 r25-handoff 落后 104 commits，未领先；
- R25 base 相对 bcdc24f 落后 23 commits，未领先；
- bcdc24f 的父提交是 a1940a220bc2b7cdc4e6ba4fe0c723fbfb33c4ec。

Executor 开始时必须重新核实这些 refs。继续只在 r25-handoff 工作，不自动更新 main。

## 三、Stage 1C 目标

执行提示词：planner/GLEPPO_R26_STAGE1C_EXECUTOR_PROMPT.md。

本阶段必须把 42 个正式 Finding 从“存在某些关键词/模块”推进到逐项证据审计。每项都要给出原始问题、源码路径和行号、真实调用路径、对应测试函数、测试实际断言、复现命令和结果、Disposition、剩余风险、最小修复建议和验收测试。

重点审查：

1. Seed/CRN：有效 RNG seed、replica_index、action/genotype 隔离、cache key、pc1.crn_seed 与 evaluator.effective_seed_parts 的关系。
2. Budget/CTX：logical slots、replica execution、cache bundle、planned/actual、episode deltas、atomic update、reconciliation。
3. Statistics：sample roles、coverage、duplicate/missing records、cluster/episode/task provenance、estimator/bootstrap、fail-closed。
4. Protocol：canonical parsing、duplicate keys、schema、strict types、hash/version/status lifecycle、真实文件修改检测。
5. Approval：HMAC 正确性与可信密钥来源必须区分；测试密钥不能冒充生产 trust anchor；检查 action/status/document/hash/version/replay/expiry/branch binding。
6. Plan/provenance/evidence：plan identity、registered hash、protocol/runtime/evaluator binding、manifest、path safety、replay。
7. Runner/gates：SyntheticGateHarness 不等于 registered runner；核实 execute_registered_pc1、所有 gates、拒绝路径和绕过风险。

Planner 已观察到：
- gleppo/pc1.py:1111–1117 的 execute_registered_pc1() 无条件拒绝 registered PC1；
- gleppo/pc1.py:1400–1411 的 SyntheticGateHarness 明确不是完整 collection/rollout runner；
- gleppo/pc1.py:1320–1365 的 ApprovalGate 使用调用者注入的 approval_key，可信密钥来源尚未证明；
- tests/test_r54_r59.py 使用 test-only static key；
- tests/test_r39_r42.py:96–100 有同一函数调用与自身比较的 tautological assertion；tests/test_r8_r9_r11_pc1.py:50–64 有更强的跨 genotype instrumented test，需要一起评估；
- evaluator.effective_seed_parts 包含 replica_index，而 pc1.crn_seed 没有该参数，必须查明二者真实调用关系。

这些是审计线索，不是未经验证的最终缺陷判决。

## 四、交付物

- research/R26_PC1_FINDING_LEVEL_VERIFICATION.md：42 个正式 Finding 的逐项矩阵及 SECOND/R54–R61 crosswalk。
- research/R26_PC1_TEST_EVIDENCE.md：测试安全审查、精确命令、原始结果、覆盖映射和跳过原因。
- research/R26_PC1_FINDING_REGISTER.md：只在有证据时更新 crosswalk 和 deduplication，不强行合并。
- research/R26_PC1_CURRENT_BRANCH_FINDING_AUDIT.md：保留 Stage 1B 初步记录，补充 Stage 1C 真正的逐项审计结果。
- research/R26_PC1_AUDIT_SUMMARY.md：更新真实 disposition 和剩余阻塞。
- planner/latest_plan.md
- planner/GLEPPO_R26_HANDOFF.md
- planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md
- status.json

若不能完成所有 42 项，逐项列明完成/未完成，不能宣称完整。

## 五、严格边界

- 不执行 registered PC1；
- 不访问、列出、读取、加载、检查、调参或执行 Family C；
- 不训练 ECOS/PPO；
- 不运行 Formal G3 efficacy；
- 不调用外部模型/API；
- 不启动 production runtime；
- 不修改生产源码或测试代码；
- 不创建审批 artifact 或签名，不读取/配置生产签名密钥；
- 不修改冻结的 R1–R25 raw evidence/manifests；
- 不 merge/reset/rebase/force-push 或更新 main；
- 不混用其他项目的代码和产物。

只允许运行经过安全审查的离线测试。450/450 aggregate pass 不能替代逐项行为覆盖证据。

## 六、Stage 1C 验收标准

只有当：
1. FIRST review 搜索范围和结果已记录；
2. 42 个 formal IDs 均有可追溯原始来源；
3. SECOND blocker 和 R54–R61 remediation crosswalk 清楚；
4. 每项 Finding 都有真实源码/测试/复现证据，或明确、可解释的 UNVERIFIABLE 原因；
5. runner 与 approval trust-anchor 缺口被准确表达；
6. 测试无 Family C/API/生产 runtime/PC1/训练副作用；
7. 状态、提交和证据路径一致；

才可提交 Planner 独立复审。

**下一步：严格执行 planner/GLEPPO_R26_STAGE1C_EXECUTOR_PROMPT.md。Stage 1C 仍然只审计，不修复生产源码。**
