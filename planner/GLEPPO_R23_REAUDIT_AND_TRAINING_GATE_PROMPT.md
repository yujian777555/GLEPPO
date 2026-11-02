# GLEPPO R23 — R22 复审程序纠偏、R21-C1 真正独立复审与训练门禁推进

**仓库：** `yujian777555/GLEPPO`  
**唯一工作分支：** `c7-g3-diag-v2-r1-fastpath`  
**起始 HEAD：** `ff34219185d1b0f5e07afb31e08b4060b365c1ca`  
**任务目标：** 纠正 R22 审查程序的证据缺口，完成真正可复现的 R21-C1 独立复审；然后逐项审计 PC1 历史 blocker 和正式 G3 失败原因，为真实控制器训练解除门禁。不得把任何“准备完成”写成训练完成。

---

## 0. 先纠正当前状态认识

R22 汇报为 R21-C1 独立复审 PASS，但静态复核发现：
- `scripts/_r22_review.py` 的 SHA 只打印、不比较；
- C4 以 `source_valid` 代替 `effective_success`，未证明语义等价；
- DEV/CONFIRM 仅检查任务列表不相交，未校验逐单元覆盖；
- DAC 检查只是对一个文件做简单字符串扫描；
- 最后 PASS 是无条件打印；
- `scripts/_r22_gates.py` 硬编码 R21 review PASS，而同一 commit 的 `status.json` 却写着 `PENDING_ON_CURRENT_COMMIT`；
- R22 未提交完整独立复审报告。

静态审查记录见 `research/R22_REVIEW_HARNESS_STATIC_REASSESSMENT.md`。

因此，本轮起始状态应当是：
- R21-C1 原始结果：REPORTED_GO，待完整复核；
- R22 独立复审声明：PROVISIONAL / NOT YET ESTABLISHED；
- PC1：PROPOSED_NOT_APPROVED；
- 历史 PC1 复审：REQUEST_CHANGES，当前分支复核未完成；
- 正式 G3：FAIL；
- 控制器训练：NOT_AUTHORIZED；
- Family C：禁止访问。

不要删除或覆盖 R22 的历史报告和脚本。R23 应新增更严格的验证器和审查报告。

## 1. Git 与边界

开始先核验：
- `git fetch origin`
- `git status --short --branch`
- `git branch --show-current`
- `git rev-parse HEAD`
- `git ls-remote origin refs/heads/c7-g3-diag-v2-r1-fastpath`

要求：
- 只能在 `c7-g3-diag-v2-r1-fastpath` 工作，不得切换 main；
- 起始 HEAD 必须是 `ff34219185d1b0f5e07afb31e08b4060b365c1ca` 或其后代；
- 不得 reset、force push、覆盖用户改动；
- R1–R22 的原始数据、ledger、manifest 和历史报告只读；
- 不访问、加载、执行、调参 Family C；
- 不读取或输出凭据，不伪造 HMAC、签名、Planner approval 或授权 ID；
- 本轮没有获得 PC1 或真实训练授权，不能执行 PC1、正式 G3 或控制器训练；
- 真实模型调用数必须为 0，除非后续单独取得明确授权。

## 2. Stage A — 修复 R21-C1 复审验证器

新建独立验证模块，例如 `scripts/verify_r21_c1_independent.py`，不要只修改旧脚本输出。

### A1. Manifest 与原始字节完整性

必须读取并真正比较：
- `R21_RESULT_MANIFEST.json` 的 `raw_sha256`、`ledger_sha256`、`frozen_manifest_sha256`；
- 对应文件的实际 SHA-256；
- `R21_FROZEN_MANIFEST.json` 中每个源码/任务文件的 SHA-256 和 size；
- 当前检出源码与冻结清单逐文件一致。

任何缺失、额外文件、大小不一致、哈希不一致都必须非零退出。不能只打印哈希前缀。

### A2. 数据结构和逐单元覆盖

必须断言：
- 恰好 24 个唯一 unit_key；
- 恰好 8 个任务，每个任务恰好 3 个预注册 seed；
- DEV 任务恰为 B2-065–B2-068，CONFIRM 恰为 B2-069–B2-072；
- DEV/CONFIRM 不相交；
- 每个 unit 的 task_id、seed_id、unit_key、group 归属一致；
- 没有重复、缺失或额外单元；
- group_aggregates 与逐单元重算值完全一致；
- C0、C4 的结果记录完整，无空值被默认当成功。

### A3. 正确的结果语义

不得直接把 `c4_result.source_valid` 当作 `effective_success`。

先沿着 R21 runner、DAC answer binding、interpreter、tool output 和 evaluator 的真实执行路径，定义 C4 成功条件。至少区分：
- answer correctness；
- computation/source validity；
- format compliance；
- tool-path validity；
- hard validity；
- effective success。

只有注册协议确实将这些条件定义为同一语义时，才允许复用字段。否则独立计算完整有效成功率。

随后重算：
- C0/C4 总体和 DEV/CONFIRM 分组指标；
- 24 个配对结果；
- C4 wins / C0 wins / both / both fail；
- exact McNemar 双侧 p；
- 效应量及适当的不确定性区间。

所有统计输出必须从原始逐单元数据计算，不得读取报告中的汇总值作为计算输入。

### A4. Ledger 与运行时账本

独立核对：
- 96 行 ledger 与 runtime actual_generations；
- call_id 唯一、单调；
- output-token delta 与 runtime token 总量；
- request/failure/retry 计数；
- model ID、revision、运行时参数；
- 每条 ledger 与 raw unit / execution 的关联；
- 不得把空记录、重试或缓存命中错误算成独立有效样本。

### A5. Fail-closed 测试

建立可控损坏 fixture，逐一验证非零退出：
1. 修改 raw 文件一个字节；
2. 修改 ledger 一个 token；
3. 删除一条 ledger；
4. 重复 call_id；
5. 删除或重复 unit；
6. 篡改 DEV/CONFIRM 归属；
7. 修改 C4 outcome；
8. 删除 manifest 文件；
9. 修改冻结源码文件；
10. 缺失必要 provenance 字段。

验证器不能只打印 FAIL 后仍以 exit code 0 结束。

## 3. Stage B — DAC 金标隔离的完整审计

不能再使用 `'gold' in content.lower()` 或 `'task_id ==' in content` 作为结论。

必须：
1. 从 R21 runner 的 DAC 调用入口追踪完整依赖闭包，覆盖 answer_binding、tasks、interpreter、tool outputs、contract construction 和相关 helper。
2. 用 AST/静态数据流检查定位 gold、answer key、checker、task_id、实验臂标签和确认集字段的所有读取点。
3. 区分评估器允许读取 gold 与 DAC 执行路径禁止读取 gold。
4. 检查任务契约是否只描述操作、依赖、类型和输出 schema，而不携带特定任务答案。
5. 对算术输入、字符串输入和工具返回值做 metamorphic perturbation：改变真实输入/工具输出，DAC 输出必须随之改变。
6. 只改变 gold/checker，DAC 输出必须保持不变。
7. 缺少契约、类型错误、工具失败、依赖缺失和异常输出必须 abstain 或显式失败，不能静默成功。
8. 检查答案是否真实来自执行轨迹中的工具输出，而不是从任务文本或 gold 重新构造。
9. 增加动态测试与反例测试，报告所有未覆盖路径。

交付 `research/R21_C1_INDEPENDENT_REVIEW_R23.md`，明确 ACCEPT / ACCEPT_WITH_LIMITATIONS / REQUEST_CHANGES。不得把静态 grep 写成完整 taint audit。

## 4. Stage C — PC1 历史 blocker 当前分支逐项复核

R22 没有完成这一阶段。必须阅读：
- `research/PC1_INDEPENDENT_REVIEW.md`
- `research/PC1_PROTOCOL_R4_PROPOSED.md`
- 全部相关 remediation/review 记录
- `gleppo/pc1.py`
- `gleppo/evaluator.py`
- `gleppo/reward.py`
- `gleppo/evolution.py`
- `gleppo/features.py`
- `gleppo/tasks.py`
- `docs/RUNTIME_LOCK_V2.md`
- 相关 tests、protocol hash、approval artifact 和 budget ledger 实现。

将每个历史 blocker 建立矩阵：
- finding ID；
- 原始问题；
- 当前代码位置；
- 当前测试位置；
- 独立复现结果；
- FIXED / OPEN / NOT_APPLICABLE；
- 证据；
- 是否阻止 PC1。

重点审计：
- evaluator correctness 和 gold isolation；
- 真正的 train/validation template split；
- 状态特征距离/相似度语义；
- 跨进程稳定 seed 与 CRN；
- cache、replica、CTX 和 planned slot 单位；
- Q rollout / extra immediate sample role；
- r_hat/Q_hat 使用同一 reward；
- 100 states、40 clusters、task/episode provenance；
- raw evidence replay 和哈希绑定；
- 注册 protocol 与代码版本/哈希一致；
- 可信审批 artifact 的认证与默认拒绝；
- 完整 PC1 collection/rollout orchestration，而不只是 accounting harness；
- 所有预算组件的原子更新与精确 reconcile。

修复所有可离线复现的缺陷，增加针对性回归测试和 clean-clone 复验。不得执行注册 PC1。

输出 `research/R23_PC1_BLOCKER_MATRIX.md`。

## 5. Stage D — 正式 G3 失败原因复核

正式 G3 仍为 FAIL。R21-C1 DAC 结果不能替代 G3。

使用现有 G3 证据和原始协议，区分：
- 工具链工程正确性；
- Agent 任务求解成功率；
- genotype/operator 是否真正改变可执行行为；
- 子代相对于父代是否有正向性能收益；
- 行为变化是否只是无效变化；
- DAC 是否可能掩盖或改变不同 genotype 的表现。

交付 `research/R23_G3_FAILURE_DECOMPOSITION.md`：
- 逐条列出当前 FAIL 判据；
- 对应历史实验和原始证据；
- 已证实根因与未证实假设；
- 不增加模型调用的诊断；
- 下一次正式 G3 的最小可证伪设计；
- 明确 G3 需要的授权和停止条件。

不要通过修改 G3 阈值、任务、种子或算子来“做成 PASS”。如果需要变更协议，必须提出 amendment 并独立复审。

## 6. Stage E — 控制器训练预注册（只准备，不启动）

研究主线仍是 M1：Evolution-Conditioned Operator Selection。M2_FMPS 保持冻结，除非有新的独立证据。

训练设计必须：
- 控制对象为演化控制器，不是 Qwen 基座模型；
- DAC 作为所有实验臂共享的固定执行组件，避免把 DAC 收益归因给 PPO；
- 不擅自把 DAC 加入动作空间；
- 明确 state/action/reward、episode、终止条件和 checkpoint 选择；
- 训练集、验证集、确认集按任务/模板/种子严格隔离；
- 固定策略、随机策略、规则策略、现有 bandit（若已实现）与 PPO 公平比较；
- 配对任务和 CRN 规则明确；
- 预注册训练种子、GPU 小时、模型调用、Token、墙钟、预算硬上限和停止规则；
- 报告任务级异质性、配对效应和置信区间；
- 不允许在确认集上调参。

交付：
- `research/R23_CONTROLLER_TRAINING_PREREGISTRATION.md`
- 机器可读 JSON；
- 预算表；
- runtime lock；
- task split manifest；
- checkpoint selection rule。

**本阶段不得启动训练。** 真实训练必须等待 R21-C1 复审、PC1 当前分支独立复审、可信 Planner 批准、正式 G3 通过和 PC1 批准/执行通过。

## 7. 审批边界

- 不得自己伪造 Planner approval、HMAC 或独立 reviewer 身份。
- R23 复审完成后，先提交准确 commit 和协议哈希给独立复审。
- 只有独立复审 ACCEPT 且获得可信 Planner 的明确审批，才可进入正式 G3/PC1。
- PC1 PASS 后再评估是否授权控制器训练。
- Family C 始终禁止访问。

## 8. 交付与状态

必须提交：
- R22 静态复核说明；
- R21-C1 完整独立复审报告；
- fail-closed verifier 和 tamper tests；
- PC1 blocker matrix；
- G3 failure decomposition；
- controller training preregistration；
- 更新 latest_plan、status 和 handoff；
- 定向测试、全量测试、clean-clone 复验；
- commit SHA、远端 HEAD 和 clean worktree 证据。

最终状态只能为：
- `R23_REAUDIT_COMPLETE_REQUIRES_INDEPENDENT_REVIEW`
- `BLOCKED_R21_C1_REAUDIT`
- `BLOCKED_PC1_REMEDIATION`
- `BLOCKED_PC1_APPROVAL`
- `BLOCKED_FORMAL_G3`
- `TRAINING_READY_FOR_USER_AUTHORIZATION`

不得使用 `TRAINING_COMPLETE`。R23 不授权任何真实训练。

## 9. 立即执行

不要只回复计划。现在先完成 Git 核验，然后实际实现 Stage A 的 fail-closed verifier 和 tamper tests；随后完成 Stage B/C/D/E 的离线工作。遇到门禁阻塞时，继续所有无需越权的工作，更新仓库并给出可执行的下一步。
