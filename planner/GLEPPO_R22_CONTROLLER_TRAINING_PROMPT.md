# GLEPPO R22 — R21-C1 独立复审、PC1 门禁闭合与控制器训练

**角色：** 你是 GLEPPO 项目的 Executor。  
**仓库：** `yujian777555/GLEPPO`  
**唯一工作分支：** `c7-g3-diag-v2-r1-fastpath`  
**起始基线：** `90f964a9ddc9eabd0096cb504755bd1c7c13c23a`（R21-C1，2026-11-02）  
**本轮目标：** 在不绕过研究门禁的前提下，尽快从 R21-C1 的 DAC 正结果推进到真正的 EC 控制器训练。先完成独立复审和 PC1 授权条件；只有所有硬门禁真实通过后，才启动控制器训练。不要把“写计划”当成实验完成。

---

## 0. 不可违反的项目边界

1. 只维护 GLEPPO，不得混入 openissue、agentfotagent、EvoPareto-Agent、CausalEvo-DSH、RecurSyn-NSGAIII 或其他仓库的代码、数据和结论。
2. 从指定分支和基线继续。**不要切换到 `main`**：当前 main/README/旧版 planner 信息滞后，R21-C1 实际位于本分支。
3. R1–R21 的原始数据、冻结协议、账本、manifest 均不可覆盖或重写。所有新实验使用唯一新 Run ID 和新目录。
4. 不访问、加载、执行、调参或探测 Family C。
5. 不读取、打印、复制或写入任何凭据；不得伪造 HMAC、Planner approval、签名、授权 ID 或审批日期。
6. 不微调 Qwen 基座模型，不做 SFT/RLHF。这里的“训练”指 **GLEPPO 的演化控制器训练**，不是训练基础 LLM。
7. R21-C1 的 GO 不是 PC1 批准，也不是正式 G3 通过。当前正式 G3 仍为 FAIL；PC1 当前协议为 PROPOSED_NOT_APPROVED；控制器训练在 PC1 通过前禁止启动。
8. 本提示词授权离线审计、缺陷修复、测试、训练方案实现审查和审批材料准备；**不替代可信 Planner 审批、独立复审批准或 PC1 协议批准**。

## 1. Git 与状态核验

开始时执行并保存真实输出：

- `git fetch origin`
- `git status --short --branch`
- `git branch --show-current`
- `git rev-parse HEAD`
- `git ls-remote origin refs/heads/c7-g3-diag-v2-r1-fastpath`

要求：
- 当前分支必须是 `c7-g3-diag-v2-r1-fastpath`；
- HEAD 必须是 `90f964a9ddc9eabd0096cb504755bd1c7c13c23a` 或其可验证的后代；
- 工作区必须 clean；若不 clean，先审查差异，不得覆盖或 reset 用户改动；
- 若远端分支已前进，先审查新增提交，再决定是否 fast-forward；
- 不允许 force push。

将旧的 R4 `planner/latest_plan.md` 保存在归档文件中（若尚未归档），然后把 `planner/latest_plan.md` 更新为本轮计划入口。同步更新 `status.json`，但不得把待审批状态写成 APPROVED。

## 2. Stage A — R21-C1 独立复审（零新增模型调用）

复审对象：

- Commit：`90f964a9ddc9eabd0096cb504755bd1c7c13c23a`
- Run ID：`20261102T131000Z_R21`
- 目录：`research/runs/20261102T131000Z_R21/`
- 核心文件：`R21_RAW.json`、`R21_LEDGER.jsonl`、`R21_FROZEN_MANIFEST.json`、`R21_RESULT_MANIFEST.json`、`R21_C1_REPORT.md`
- 代码：`gleppo/answer_binding.py`、`gleppo/interpreter.py`、`gleppo/tasks.py`、`scripts/_run_g3_r21.py`、`scripts/_r21c1_recompute.py`、`scripts/_r21c1_check.py`

必须独立完成以下核查，不能只复述 Executor 报告：

### A1. 数据和账本

- 从原始 JSON/JSONL 独立重算 24 个评价单元、8 个任务、DEV/CONFIRM 分组和全部指标；
- 核对 96 条账本记录、唯一且单调的 call_id、模型调用计数、Token delta、运行时总量、失败/重试计数和时间戳；
- 独立重算 C0=9/24、C4=24/24、配对 C4 wins=15、C0 wins=0、双正确=9；
- 独立重算 McNemar exact 双侧 p 值（15 个不一致配对、0 个反向不一致时应约为 0.000061035），并报告效应量和不确定性；
- 检查 DEV 与 CONFIRM 是否严格分开；确认任务是否确实未参与开发、调参或任务契约设计。若不能证明，降低泛化结论等级；
- 验证 manifest 的每个文件 SHA-256，确认原始字节未变化。

### A2. DAC 无金标泄漏审计

对 B2-065 至 B2-072 的八个 TaskContract 逐一审计：

- 契约是否仅表达任务要求的计算步骤、工具依赖、类型和输出格式；
- DAC 是否读取 gold、gold checker、答案文件、任务 ID 分支或实验臂标签；
- 是否存在硬编码答案、特定任务特判、由 gold 反推的参数或把期望结果写入工具输出；
- 所有计算是否真实消费执行轨迹中的工具输出，而非重新解析任务文本后自行生成答案；
- 类型、依赖、工具失败、缺失字段、异常值和不支持运算是否 fail-closed / abstain；
- 通过改变任务输入数字、字符串和工具返回值验证 DAC 输出随真实输入变化；
- 仅改变 gold checker 不得改变 DAC 输出；
- 删除/破坏契约时必须 abstain 或显式失败，不得静默回退成伪成功。

### A3. 指标与因果解释

独立区分：
- `answer_correct`
- `format_compliant`
- `tool_path_valid`
- `hard_validity`
- `effective_success`

核对 C0/C4 是否基于同一执行轨迹分叉；若模型调用、工具执行或随机上下文不等价，明确限制因果结论。不要把 8 个任务上的 100% 写成普遍泛化，也不要把 R21-C1 的 DAC 改进误称为演化控制器训练成功。

### A4. 复审交付

新增独立报告 `research/R21_C1_INDEPENDENT_REVIEW.md`，给出：
- ACCEPT / ACCEPT_WITH_LIMITATIONS / REQUEST_CHANGES；
- 每项核查的文件、行/字段、命令、实际输出；
- 所有指标的独立重算；
- 任何金标泄漏、契约边界或账本问题；
- 是否允许进入下一阶段。

复审脚本不得直接调用被审查的聚合函数作为唯一证据；至少对关键指标提供独立实现或手工可核算的检查。此阶段模型调用必须为 0。

**若复审为 REQUEST_CHANGES：** 修复可证实的实现问题，补充回归测试，保留原始 R21 工件不变；必要时提出新的确认实验协议。不得直接进入训练。

## 3. Stage B — PC1 与正式 G3 门禁审计

当前已知状态（必须重新从当前分支核实，不得照抄旧 status）：

- `research/PC1_PROTOCOL_R4_PROPOSED.md`：PROPOSED / NOT APPROVED；
- `research/PC1_INDEPENDENT_REVIEW.md`：历史复审结论 REQUEST CHANGES，审查对象是旧 main 提交，不代表当前分支已通过；
- `gleppo/pc1.py`：协议代码声明 `pc1-proposed-v1-r5`，默认状态 `PROPOSED_NOT_APPROVED`；
- 正式 G3：FAIL；
- PC1：未执行；
- 控制器：未训练。

执行要求：

1. 完整阅读 `research/PC1_INDEPENDENT_REVIEW.md`、`research/PC1_PROTOCOL_R4_PROPOSED.md`、`gleppo/pc1.py`、`gleppo/evaluator.py`、`gleppo/reward.py`、`gleppo/evolution.py`、`docs/RUNTIME_LOCK_V2.md` 及相关测试。
2. 将历史独立复审的每个 blocker 映射到当前分支源码和可执行回归测试，逐项标记 FIXED / OPEN / NOT_APPLICABLE，并提供证据。不能因为历史 status.json 声称修复就直接接受。
3. 核实 PC1 协议文档、代码常量、协议哈希、plan artifact、运行锁、审批记录和预算账本一致。
4. 检查 PC1 统计单位、state-to-task/episode/cluster 映射、CRN 种子、cache/replica 计数、sample_role、reward/estimator 定义、planned slots 与 actual executions 的区分。
5. 核实训练/验证模板是否真正不同。历史复审指出 train/validation 模板列表可能相同；必须证明模板 ID 对应不同生成规则且 train/validation 不重叠。
6. 核实当前生产模型 revision、A800 环境、评估器和正式 G3 smoke。R21-C1 的任务成功不能代替正式 G3。
7. 对所有未解决 blocker 先做离线修复和测试，再请求新的只读独立复审。

**PC1 执行和控制器训练的共同前置条件：**

- PC1 协议有真实、可信、可验证的 Planner 批准记录；
- 独立复审对当前准确 commit 和协议哈希给出 ACCEPT；
- production runtime lock 与实际 A800/model revision 精确匹配；
- 正式 G3 / production smoke 按冻结协议通过；
- 预算上限、种子、任务拆分、统计方法和停止规则冻结；
- 所有 gate 默认 deny，任何字段缺失或哈希不匹配均停止。

不得伪造审批或自行把 PROPOSED 改成 APPROVED。没有真实批准时，不运行注册 PC1，不训练控制器。

## 4. Stage C — 控制器训练设计（先做离线，不越权启动）

训练对象是 GLEPPO 的演化控制器，不是 Qwen 基座模型。

必须先审查当前仓库的项目章程、研究计划、状态/动作/奖励定义、已有 ECOS/PPO 实现和强基线。不得凭空新建一套与注册设计不一致的算法。

训练设计必须回答：

1. 控制器究竟控制什么：演化算子选择、参数调节、候选生成/筛选，还是多项联合？只允许采用当前批准协议中明确的动作空间；
2. 状态是否只包含决策时可获得的信息，是否存在 gold、未来结果、确认集或 holdout 泄漏；
3. 奖励是否直接由真实 Agent 执行反馈计算，并与 PC1 注册的 reward 完全一致；
4. 如何处理随机性、CRN、缓存、无效子代、执行失败和多任务差异；
5. 训练、验证、最终确认任务如何按任务/模板/种子隔离；
6. 与固定策略、随机策略、规则策略、现有 bandit/其他基线如何公平比较；
7. 是否需要多训练种子、多个独立任务簇，以及如何给出置信区间；
8. 训练停止条件、过拟合检查、checkpoint 选择规则和失败回滚方案。

**DAC 在控制器实验中的处理：**

- R21-C1 已表明 DAC 可能显著改善算术答案生成。为隔离演化控制器的因果贡献，默认把同一版本 DAC 作为所有比较臂共享的执行环境组件，而不是只给 PPO 臂使用。
- 不得把 DAC 的收益归因于控制器。
- 不得未经预注册就把 DAC 临时加入控制器动作空间。
- 如确实要研究“控制器是否学会选择 DAC/LLM/abstain”，必须另立明确假设、定义 DAC 适用域与 abstain 规则、设计固定/随机/规则/PPO 对照，并重新冻结协议；不得与算子选择训练混为一个结论。

### 训练对照至少包含

以当前正式研究计划和代码为准，核实并冻结：
- 固定策略（无学习控制器）；
- 随机策略；
- 规则策略；
- 现有 bandit 基线（若已在项目设计中）；
- PPO / EC 学习控制器（目标方法）。

所有臂使用相同任务、运行环境、可比的模型调用预算和配对评估种子。任何基线若未实现，先标记缺失，不得伪造结果。

### 训练预算

- PC1 的 50,000 planned slots 不是训练预算，不得混用。
- 先统计 A800 可用 GPU、显存、运行时间、实际模型调用和 Token 成本。
- 提交独立的训练预算表：训练 episodes、模型生成调用、Token、GPU 小时、墙钟上限、最大重试和停止阈值。
- 预算必须在首次训练调用前冻结并获得授权。
- 不能根据中途结果追加预算或更换任务。

完成后生成 `research/R22_CONTROLLER_TRAINING_PREREGISTRATION.md`、机器可读 JSON、训练运行锁和哈希 manifest。只有 Stage A/B 所有 gate 通过并取得所需批准后，才可启动真实训练。

## 5. Stage D — 条件式真实训练执行

**仅当 Stage A/B 全部通过且所有真实审批已存在时执行。** 否则停止在最近一个未通过 gate，明确报告 BLOCKED，不得绕过。

若获准训练：

1. 只加载 Family A/B 训练集；Family C 仍完全禁止。
2. 只使用已批准的训练/验证任务；确认集与 holdout 在训练前封存。
3. 使用冻结的 Qwen2.5-7B-Instruct revision：
   `a09a35458c702b33eeacc393d103063234e8bc28`。
4. 不更改模型 revision、解码参数、工具环境、gold checker、DAC 或 reward，除非新协议明确批准。
5. 执行预注册的训练轮次和随机种子；每轮保存 controller checkpoint、完整轨迹、奖励、动作分布、有效成功率和资源账本。
6. 训练中只用 train 数据更新参数；validation 只用于按预注册规则选择 checkpoint；最终确认集不得反复用于调参。
7. 每次调用前检查预算，硬上限先到即停；不允许后台无限重试。
8. 若训练出现 reward hacking、任务成功下降、策略塌缩、动作单一化、seed 不可复现或训练/验证泄漏，按预注册规则停止。
9. 完成后用独立脚本复算结果，比较固定/随机/规则/bandit/PPO 的有效成功率、配对差值、置信区间和任务级异质性。
10. 只有确认集结果支持时才能报告性能提升；训练 reward 上升不等于 Agent 性能提升。

## 6. 必需交付物

- `research/R21_C1_INDEPENDENT_REVIEW.md`
- PC1 blocker 对照与修复报告；
- PC1 最新协议和可信审批状态（未批准时明确标记 PROPOSED）；
- `research/R22_CONTROLLER_TRAINING_PREREGISTRATION.md`
- 训练预算审计、运行锁、任务拆分和 manifest；
- 若获准训练：训练原始轨迹、逐调用账本、checkpoint、独立复算报告和最终统计；
- 更新 `planner/latest_plan.md`、`status.json` 和 `SESSION_HANDOFF`；
- 定向测试、全量测试、clean-clone 复验；
- Git commit、push、远端 SHA 和 clean worktree 证据。

## 7. 最终状态只能从以下选择

- `TRAINING_COMPLETE_REQUIRES_INDEPENDENT_REVIEW`
- `TRAINING_READY_FOR_USER_AUTHORIZATION`
- `BLOCKED_R21_REVIEW`
- `BLOCKED_PC1_REMEDIATION`
- `BLOCKED_PC1_APPROVAL`
- `BLOCKED_FORMAL_G3`
- `INCONCLUSIVE`

**严禁**在 PC1 未通过时写 `TRAINING_COMPLETE` 或启动控制器训练。

## 8. 立即开始的执行顺序

不要只回复计划。现在按以下顺序执行：
1. Git/branch/hash 核验；
2. R21-C1 原始证据独立复算；
3. DAC 金标隔离与契约审计；
4. 当前 PC1 blocker 逐项复核；
5. 对可修复问题做离线修复和测试；
6. 冻结训练方案和预算；
7. 仅在真实审批与 G3 gate 全部通过后启动训练；
8. 更新仓库并提交接班提示词。

如果遇到门禁阻塞，继续完成所有不需要越权的工作，不要空等；但绝不能把“准备好了”写成“已经训练”。
