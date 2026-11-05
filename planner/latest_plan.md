# GLEPPO 最新执行计划 — R26 ECOS Protocol R1.2 Final Documentation Consistency

**仓库：** `yujian777555/GLEPPO`  
**分支：** `r25-handoff`  
**更新时间：** 2026-11-05  
**R2.1.1 Planner decision：** ACCEPT（已关闭）  
**R26 R1 Planner decision：** REQUEST_CHANGES  
**R26 R1.1 Planner decision：** REQUEST_CHANGES（实质纠正已完成，剩余文档一致性问题）  
**Reviewed R1.1 commit：** `728bc356bbd4b776839d5f185eb6a2084f0f4de8`  
**R1.1 Planner review：** `research/R26_ECOS_PROTOCOL_R1_1_PLANNER_REVIEW.md`  
**R1.2 Executor prompt：** `planner/GLEPPO_R26_ECOS_PROTOCOL_R1_2_FINAL_DOC_CORRECTIVE_PROMPT.md`

---

## 一、当前决策

**R1.1 不接受为最终 canonical protocol。只执行一次范围严格受限的 R1.2 文档一致性修正。**

R1.1 已经正确修正了核心问题：32 个特征名称、Reward 冲突、Action-dependent seed、PC1 采样差异、204 预算、split 类型、B6/B5 基线定位和 γ 修正案要求。

第二轮复审发现的剩余问题：

1. Reconciliation A–K 主矩阵仍保留 R1 的错误结论，与末尾 R1.1 修订记录冲突。
2. 32 维 feature 表把大量必需输入误标为缺失值自动补 0；源码实际没有这种 imputation。
3. PC1 R4 的 PASS/FAIL/INCONCLUSIVE 三分支 CI 规则未完整进入 JSON 和 Markdown。
4. JSON 缺少 train_A/train_B/val_A/val_B 的完整 split SHA-256；manifest/source provenance 不完整。
5. Baseline fairness 缺少共同初始化、配对 seed、state visibility、预算、停止规则和独立成本账本的明确合同。
6. Operator LLM-call 账本与当前 source 描述不一致，尤其 prompt_local_edit 当前实现是确定性 0 call。
7. status.json 的嵌套 R1/R1.1 记录仍含旧结论；latest_plan/handoff 尚未记录最终 R1.1 review 状态。
8. R1→R1.1 compare range 携带 15 个 scripts helper 文件；必须记录来源与未执行事实，不得运行或修改。

详细证据见 Planner review。

## 二、R1.2 唯一任务

执行：

`planner/GLEPPO_R26_ECOS_PROTOCOL_R1_2_FINAL_DOC_CORRECTIVE_PROMPT.md`

仅修改以下六个现有文件：

- `research/R26_ECOS_PROTOCOL_RECONCILIATION.md`
- `research/ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.md`
- `research/ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.json`
- `status.json`
- `planner/latest_plan.md`
- `planner/GLEPPO_R26_HANDOFF.md`

不得创建重复协议文件。不得修改 scripts、生产源码、tests、数据、manifest 或历史协议。不得执行项目代码或 helper scripts。

## 三、科学状态与未解决门槛

- ECOS 仍是待证伪研究假设；固定 vs 自适应、PPO vs rule、PPO vs LinUCB 尚未证明优势。
- R24 reward 与 shared generation reward 不等价；采用 shared reward 需正式 amendment。
- γ=0.95 supersedes R24 γ=0.99 only after formal amendment.
- 32-D state 未接入 controller；budget_used_frac 是 source defect；pop_size_norm normalization 未解决。
- Evaluation seed 仍通过 replicate_id 间接受 operator 影响，CRN 跨算子配对未实现。
- PC1 R4 的样本量/预测 horizon 相对 Phase 1 的统计充分性未解决。
- PC1 reward provenance 尚不能由当前记录 schema 验证。
- R24 call/token budget scope 未解决。
- PPO architecture/observation/rollout/optimizer semantics 未实现。
- Baseline fairness contract 需要明确；B5 是外部参考，不是相同动作集对照。

## 四、硬门禁

- PC1 BLOCKED；PC1 R4 PROPOSED / NOT APPROVED。
- Formal G3 FAIL。
- Family C NOT ACCESSED；不得读取 task payload/gold。
- Registered PC1 NOT EXECUTED。
- Controller training NOT AUTHORIZED / NOT STARTED。
- 无模型/API 调用、local model inference、生产 runtime、signing-key 访问。
- 不执行 PC1、baseline pilot、Formal G3 efficacy 或任何实验。
- 不修改生产源码、tests、scripts、数据、manifest、raw evidence 或历史协议。
- 不更新/合并 main，不 reset/rebase/force-push。
- 不混用其他项目的代码、数据或报告。

## 五、下一关口

**R1.2 文档一致性修正完成 → Planner 独立复审。**

这是最后一轮文档一致性修正，不再启动新的宽泛协议审计。R1.2 通过后，仍需单独评估正式协议 amendment、seed 修复和 PC1 授权；本阶段不授予实验权限。
