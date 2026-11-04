# GLEPPO 最新执行计划 — R26 Stage 1I

**仓库：** `yujian777555/GLEPPO`  
**项目边界：** 仅 GLEPPO；不得混入 openissue、agentfotagent、CausalEvo-DSH、EvoPareto-Agent 或其他项目  
**工作分支：** `r25-handoff`  
**本轮 Planner 复核起始 HEAD：** `571c34201dde4e63705319670e446cb0e058f086`  
**本轮复核时 main：** `6bad0b77835a2d00c62287c0c7d9d91d1d186d5e`  
**起始分支关系：** r25-handoff 相对 main ahead 194 / behind 0  
**R25 基线：** `a8ff1827434a88b2fef02a89aaf3e120e0a017a7`  
**更新时间：** 2026-11-04  
**当前阶段：** R26 Stage 1I — Finding-level semantic evidence completion  
**当前状态：** Stage 1H Planner = REQUEST_CHANGES；Stage 1I prompt 已增加科学性与协议一致性约束，等待 Executor 执行

---

## 一、当前 Planner 结论

**GLEPPO Idea 保留为可证伪研究假设；PPO 优势尚未证明；PC1 仍 BLOCKED；不启动训练。**

研究主线仍为 ECOS（Execution-Conditioned Operator Selection）：根据 Agent 执行反馈、种群状态和算子历史，在 Agent 基因型演化过程中选择变异/重组算子。

核心科学问题不是“能不能训练 PPO”，而是：

> 当不同演化算子会改变后续种群状态并产生可重复的延迟收益时，序贯控制器能否利用这种跨代依赖，在相同状态、算子库、评估预算和任务条件下，优于最佳固定算子、规则控制器及上下文 Bandit？

当前没有实验结论证明上述优势成立。PPO 只是候选控制器，不是已被证明的创新本身。

## 二、必须纠正的证据归因

R25 的 `research/R25_ECOS_SCIENTIFIC_REVIEW.md` 曾写：

> Fixed strategy enough? UNLIKELY — R21-C1 shows operator matters.

该推断不成立。

R21-C1 实际比较的是 C0（LLM 算术执行）与 C4（DAC 确定性答案计算），不是五种演化算子，也不是固定策略、随机策略、规则策略、Bandit 或 PPO 的对照。R21-C1 的 9/24 vs 24/24、McNemar p=0.000061 支持的是 DAC/算术正确性结果，不能作为“算子选择有益”或“固定算子不够”的证据。

当前应采用以下状态：
- 固定算子是否不足：**UNTESTED**；
- 自适应算子选择是否优于最佳固定算子：**UNTESTED**；
- PPO 是否优于规则控制器：**UNTESTED**；
- PPO 是否优于相同状态输入的 LinUCB/Neural Bandit：**UNTESTED**；
- 五个算子存在异质性：历史 pilot 可作为动机，但不能据此宣称自适应控制器有优势；
- 状态向量和奖励函数的有效性：仍需消融、对照和效度检验。

详细 Planner 复核：`research/R26_ECOS_SCIENTIFIC_INTEGRITY_REVIEW.md`。历史 R25 文件保留，不覆盖、不改写。

## 三、当前协议不一致问题

目前不能把不同文档视为已经统一的可执行协议：

| 来源 | 状态/关键定义 | 未决问题 |
|---|---|---|
| `research/PHASE1_DESIGN.md` | 32-D 状态；每代选择一个算子；generation reward；γ=0.95；15 代 episode；B0–B6 与消融 | 作为 Phase 1 设计基线，需与后续预注册核对 |
| `research/R24_ECOS_CONTROLLER_PREREGISTRATION.md` | child-parent immediate effective_success reward；γ=0.99；4/4/4 task split；1,000 episodes | 与 Phase 1 reward、γ 和 split 不一致；标记 PREREGISTERED 但 NOT AUTHORIZED |
| `research/PC1_PROTOCOL_R4_PROPOSED.md` | PC1 myopia diagnostic；使用 generation_reward；γ=0.95；45,440 planned slots / 50,000 cap | 仅为 PROPOSED / NOT APPROVED 的诊断协议，不是训练授权 |
| `gleppo/reward.py` / `gleppo/evolution.py` | 实际共享 generation_reward：Δbest + 0.1·valid_rate + 0.25·Δmean，clip [-0.5,1.0]；γ=0.95 | 与 R24 即时 child-parent reward、γ=0.99 存在冲突 |

这些定义不能由 Executor 静默选择或改写。Stage 1I 只需把冲突作为未决问题保留。Stage 1I 通过 Planner 独立复审后，必须另行完成 `R26_ECOS_PROTOCOL_RECONCILIATION`，统一状态、动作、episode/rollout/CTX 单位、奖励、γ/GAE λ、数据划分、基线、主指标、预算账本和停止规则；在该审查通过前，不得申请 PC1 批准或训练。

## 四、当前执行任务：R26 Stage 1I

**Executor 提示词：** `planner/GLEPPO_R26_STAGE1I_EXECUTOR_PROMPT.md`

完整上一轮 Planner 复审：`research/R26_STAGE1H_PLANNER_REVIEW.md`  
新增科学性审查：`research/R26_ECOS_SCIENTIFIC_INTEGRITY_REVIEW.md`

Stage 1I 目标是完成 R12–R53 共 42 个 PC1 Finding 的真实语义证据审计，而不是只列测试函数名称。

必须完成：
1. 每个 Finding 记录原始验收条件、真实测试断言、源码符号、调用路径、目标分支是否到达、已证明/间接支持/未覆盖条件；
2. 修正 R53：status-consistency 测试仅是间接证据；没有直接 status-only hash invariance 测试；
3. R39 必须交叉引用 R16/R20 的跨基因型 instrumented evaluator 测试，不能使用同一调用与自身比较的恒真断言；
4. 补齐 R18 手工证据、planned slots 与 actual CTX 的单位区别、token/production cost 未测量说明；
5. 把 `scripts/_r26h_extract.py` 升级为真实的 42-ID / declaration-map validator；明确它不能证明断言语义；
6. 重新评估所有 VERIFIED_FIXED，不以维持既有数量为目标；
7. 更新 Stage 1I 报告、累计 PC1 审计记录、status、latest_plan、handoff 和 next-session prompt；
8. 最终报告增加 Scientific integrity handoff，引用本轮 Planner 科学性复核。

Stage 1I 仅允许文档和非生产审计 helper 修改；不允许生产源码或测试代码变更。不得执行注册 PC1，不得访问 Family C，不得训练控制器，不得调用真实模型/API，不得运行 Formal G3 efficacy。

## 五、Stage 1I 之后的顺序

1. Stage 1I Executor 提交完整证据与 handoff。
2. Planner 独立复审：逐条检查 42 个 Finding 的语义证据与 disposition；Executor 自报结果不等于 Planner 验收。
3. Stage 1I 接受后，单独执行 `R26_ECOS_PROTOCOL_RECONCILIATION`：核对 Phase 1 / R24 / PC1 R4 / 实际代码，形成唯一候选协议及完整差异表；不得覆盖历史注册文件。
4. 对协议进行独立科学审查，尤其确认 R21-C1 不再被用作算子选择证据。
5. 只有在所有前置门禁、可信 Planner 审批、独立审查和用户授权齐备后，才可讨论是否批准 PC1。PC1 未获批准前不得执行。
6. PC1 若按批准协议执行且通过，之后再单独审议控制器训练授权；训练后仍需正式 G3 efficacy 和严格基线比较。

PC1 的 PASS 只证明预注册的非短视诊断达到门槛，不等于 PPO 已经优于 Bandit，也不等于论文创新已经成立。

## 六、硬边界（持续有效）

- PC1：BLOCKED；`PC1_PROTOCOL_R4_PROPOSED.md` 仍 PROPOSED / NOT APPROVED。
- Formal G3：FAIL。
- Family C：NOT ACCESSED；禁止列出、读取、加载、检查、调参或执行。
- Controller training：NOT AUTHORIZED / NOT STARTED。
- Registered PC1：NOT EXECUTED。
- External model/API calls：0。
- Production runtime calls：0。
- 不读取或配置生产签名密钥。
- 不改写冻结 R1–R25 raw evidence、manifest 或历史报告。
- 不修改 `main`，不 merge/reset/rebase/force-push。
- 不跨项目复用代码、数据或报告。

**Stage 1I 的唯一当前动作：** 按最新 Executor prompt 完成 42 个 Finding 的语义证据审计，并保留本轮科学性修正；不得跳过独立复审直接进入 PC1 或训练。
