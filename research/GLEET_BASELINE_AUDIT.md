# GLEET Baseline Audit (P0.1)

**Audit date:** 2026-10-26  
**Paper:** Z. Ma, J. Chen, H. Guo, Y. Ma, Y.-J. Gong, "Auto-configuring Exploration-Exploitation Tradeoff in Evolutionary Computation via Deep Reinforcement Learning", GECCO 2024, pp. 1497-1505. DOI: [10.1145/3638529.3653996](https://doi.org/10.1145/3638529.3653996). arXiv: [2404.08239](https://arxiv.org/abs/2404.08239).  
**Official code:** [MetaEvo/GLEET](https://github.com/MetaEvo/GLEET), inspected at commit `e7159273d4dc7ea78ef3ae3a701069cfd4d61191` (2024-10-30).  
**Audit scope:** read-only. No GLEET code was copied into GLEPPO. No GLEET training or test run was executed in this phase.

Source labels used below:

- **[P]** — stated in the paper (arXiv HTML v1 / GECCO version).
- **[C]** — verified in the official code at the commit above (exact path / symbol).
- **[A]** — assumption or inference; not yet reproduced.

---

## 1. License and reuse constraints

| Item | Finding | Evidence |
|---|---|---|
| LICENSE / COPYING / NOTICE file | **Absent** in the working tree and in full git history (`git log --all --name-only` finds no license path) | Local clone of `MetaEvo/GLEET` @ `e715927` |
| GitHub "Resources" sidebar | Lists `Readme` only; no license badge | [Repo page](https://github.com/MetaEvo/GLEET) read 2026-10-26 |
| README license section | None. Only citation block (`@inproceedings{ma2024auto,...}`) | `README.md` |
| Paper license | ACM rights (`© acmlicensed`); arXiv preprint under arXiv perpetual non-exclusive license | arXiv:2404.08239v1 |

**Reuse conclusion (binding for GLEPPO):**

1. The GLEET **code has no open-source license**. Default copyright applies. Copying, redistributing, or creating derivative works of that code is **not permitted** without an explicit grant from the copyright holders (SCUT / MetaEvo authors).
2. GLEPPO **must implement its own controller and environments from scratch**. The GLEET repo may be inspected as a research source (this audit) and cited; it must not be vendored, forked, or transplanted.
3. If a future design is a near-transcription of GLEET's network or PPO loop, that is a legal and scientific risk. Prefer independent implementation of independently specified mechanisms.
4. Optional follow-up (not blocking this audit): contact the corresponding author (`gongyuejiao@gmail.com` per paper) to ask for a license if reuse becomes essential. Do not proceed on a "code is on GitHub so it is free" assumption.

---

## 2. Problem GLEET actually solves

**[P]** GLEET is *not* an agent-evolution method. It is a **meta black-box optimization** framework: a DRL agent tunes **exploration-exploitation hyper-parameters** of a *backbone EC algorithm* (PSO / DMSPSO; DE in appendix) while that algorithm minimizes a continuous numerical objective.

- Search object: a real-valued vector `x ∈ [-100,100]^dim` (CEC2021 functions). **[C]** `problems/dmspso.py`, `problems/gpso_np.py`.
- Fitness: deterministic black-box `problem.func(position)` (shifted/rotated CEC2021). **[C]** `problems/cec_dataset.py`.
- Episode: one optimization run, terminated at `max_fes` budget (10D: 2e5 FEs; 30D: 1e6 FEs) or when `gbest_val <= 1e-8`. **[C]** `run.py` (`opts.max_fes`), `dmspso.py:step`.
- The trained policy is expected to generalize to *other instances of the same function class* (new shift/rotate), other dimensions, other population sizes, and a protein-docking application. **[P]** Sec. 5.3.

**Implication for GLEPPO:** GLEET controls a *numeric optimizer's* hyper-parameters under an *oracle fitness*. It does not evolve LLM agents, does not see task-execution traces, and does not choose evolutionary operators. Porting its interface is a transfer of machinery, not of a research claim.

---

## 3. MDP formulation (paper) vs implementation (code)

### 3.1 State

**[P] Sec. 4.1.1 / Eq. 6.** Per-individual state `s_i ∈ R^9`:

| Dim | Meaning |
|---|---|
| `s1` | `f(gBest) / f(gBest^(0))` — search progress on best value |
| `s2` | `(FE_max - FE) / FE_max` — remaining budget |
| `s3` | `z(gBest)/T_max` — stagnation rounds of global best |
| `s4` | `z(pBest_i)/T_max` — stagnation rounds of personal best |
| `s5` | `(f(x_i)-f(gBest)) / f(gBest^(0))` |
| `s6` | `(f(x_i)-f(pBest_i)) / f(pBest_i^(0))` |
| `s7` | `‖x_i - gBest‖ / diameter` |
| `s8` | `‖x_i - pBest_i‖ / diameter` |
| `s9` | `cos∠(gBest-x_i, pBest_i-x_i)` |

These 9 features are also computed for *pBest* (exploration features) and *gBest/lBest* (exploitation features). Total observation: population features + exploration features + exploitation features → shape `(ps, 27)` for DMSPSO. **[C]** `dmspso.py:input_feature_encoding` / `get_state` / `update_pbest_feature` / `update_lbest_feature`; `observation_space=Box(..., (self.ps,27))`.

Paper notation uses `gBest` as the exploitation exemplar. **[C]** DMSPSO actually uses **lBest** (sub-swarm best) as the exploitation target for most of the run, and switches to global search mode only when `origin=True` and `fes >= 0.9*max_fes`. When RL-controlled (`origin=False`), it stays in local-search mode with RL-split `c1/c2`. GPSO uses `gBest`. This is a code-level detail not spelled out in the paper body.

### 3.2 Action

**[P] Sec. 4.1.2 / Eq. 7.** Continuous joint action: for each individual `i` and each of `M` controlled hyper-parameters, a Gaussian `N(μ_im, σ_im)` is sampled; the policy network outputs the `(μ, σ)` pairs.

**[C] Concrete instantiation (the only one in code):**

- `M = 1` scalar per individual in `[0,1]` for PSO/DMSPSO (paper: `c_{1,i}` sampled, `c_{2,i} = 4 − c_{1,i}`; DE appendix uses `M=3`: F1, F2, Cr). **[P]**
- **[C]** `options.py: output_dim_actor=1`; `dmspso.py:step` maps `action` to
  - `c_sum = self.c1 + self.c2` (DMSPSO default `1.49445+1.49445≈2.99`; GPSO `c=4.1`),
  - `c1 = action * c_sum`, `c2 = c_sum - c1`.
- So GLEET **only splits the exploration/exploitation budget** between the pBest term and the (l/g)Best term; it does not select operators, mutation scales, population size, or restart decisions.
- Policy: `Normal(μ, σ)` with `μ = (tanh(μ_net)+1)/2 ∈ [0,1]`, `σ = (tanh(σ_net)+1)/2 * (max_sigma-min_sigma) + min_sigma`, clipped action in `[0,1]`; log-prob of the joint action is the **sum over individuals**. **[C]** `nets/actor_network.py:forward`.

### 3.3 Reward

**[P] Sec. 4.1.3 / Eq. 8** (paper formula):

```
r^(t) = [ f(gBest^(t-1)) - f(gBest^(t)) ] / f(gBest^(0))
```

i.e. **relative improvement of the global best, normalized by the initial gBest value**. Non-negative; positive iff a better incumbent is found. No penalty term.

**[C] `dmspso.py:cal_reward_direct`:**

```
r = (pre_gbest - new_gbest) / self.max_cost * self.reward_scale
```

where `max_cost = min(initial costs) = f(gBest^(0))` and `reward_scale` default 100 (`options.py`). Code matches the paper formula up to the extra `reward_scale` (training convenience; does not change the optimum policy under a fixed scale).

Alternatives implemented for ablation: `relative` (r2, Sun et al.), `triangle` (r3, Xue et al.), `11` (r1, Yin et al.). **[P] App. B.7 / [C]** verdict: r1 poor on all problems; r2/r3 acceptable on simple problems; Eq. (8) best especially on complex problems.

Reward is therefore **optimization-progress shaped**, dense, and computed from an exact fitness oracle. There is no noisy execution channel, no validity constraint on "offspring", and no sparse task success.

### 3.4 Transition

**[C] `step()`:** apply velocity update with RL-split `c1/c2` → boundary handling (`periodic` default) → evaluate costs → update pBest/gBest/lBest → update stagnation counters → optional regroup every `R=10` generations (DMSPSO) → recompute state → return `(next_state, reward, is_end, info)` with `info['gbest_val']`.

---

## 4. Network design

**[P] Sec. 4.2 / [C] `nets/actor_network.py`, `nets/critic_network.py`, `nets/graph_layers.py`.**

- Transformer-styled, population-invariant: feature embedding → fully-informed encoder (self-attention over individuals) → exploration-exploitation decoder (cross-attention: Q from EET embeddings, K/V from encoder output).
- **[P] Paper architecture:** 128-d embeddings; EET pair concat 256-d → MLP 128×256×128; **2 stacked encoder layers**, FF 128×256×128; decoder FF 128×128 → logits; linear 128 → 2M scalars per individual → Tanh → `μ∈[0,1]`, `σ∈[0.01,0.7]`; critic MLP 128×64×32×1 on mean-pooled logits. LayerNorm, no positional encoding.
- **[C] Released-code architecture (materially smaller):** `embedding_dim=16`, `hidden_dim=16`, `n_heads=4`, **`n_encode_layers=1`**, actor MLPs 32→8→1, critic MLP 32→16→1. **[C]** `options.py`, `actor_network.py`.
- **[P]–[C] discrepancy:** the public default config is a **leaner network than the paper describes** (16-d / 1 layer vs 128-d / 2 layers). Reproducing paper tables from the repo defaults is therefore **not guaranteed**; treat paper numbers as paper claims only. GLEPPO must not assume either config without an explicit choice and justification.
- Action heads: `μ = (tanh(μ_net)+1)/2`, `σ = (tanh(σ_net)+1)/2*(max_sigma-min_sigma)+min_sigma`. **[C]**
- Ablations: `--no_attn` (MLP on features), `--no_eef` (drop exploration/exploitation features). Paper Sec. 5.5: both EET embeddings and full MHA are critical. Paper App. B.6: removing any state group hurts; s1–4 (progress) contributes most.

This is an application of set-attention policy networks (cf. neural combinatorial optimization) to EC hyper-parameter control — the novelty of GLEET is the EET-decision problem framing + generalization protocol, not the attention block itself.

---

## 5. PPO training loop (code-level)

**[C] `agent/ppo.py`, `run.py`, `rollout.py`, `options.py`.** Key verified parameters:

| Symbol / option | Paper [P] | Code default [C] | Notes |
|---|---|---|---|
| `gamma` | not reported numerically | 0.999 | paper only uses symbolic γ |
| `K_epochs` (κ) | 3 | 3 | mini-epochs per T-step segment |
| `eps_clip` | not reported | 0.1 | policy + value clip |
| `n_step` / T | 10 | 10 | trajectory segment; paper ablates 5/10/20, moderate best |
| `batch_size` | 16 instances, randomly sampled on the fly | 16 | parallel env instances per batch |
| `epoch_size` | — | 1024 | instances drawn per epoch in code |
| epochs | MaxEpoch = 100 | `epoch_end=100`, also `max_learning_step=4e6` | |
| `lr_model` | 4e-5 → 1e-5 decay | 4e-5 (attn) / 1e-4 (no attn), exp decay 0.9862327/epoch | Adam |
| `max_grad_norm` | not reported | 0.1 | gradient clip |
| `population_size` N | 100 | 100 (PSO) / 99 (DMSPSO) | fixed; not controlled |
| `σ` range | [0.01, 0.7] | same (`min_sigma/max_sigma`) | |
| `reward_scale` | — | 100 | code-only multiplier |

Paper reports test as 10 independent runs with mean/std/rank; hardware i9-10980XE + RTX 3090. Learning-based baselines updated with equal steps. **[P]**

**Not in the paper (code-only):** γ, eps_clip, exact Adam/grad settings, `max_learning_step`, `reward_scale`, train/val seeds.

Training procedure (verified in `train` / `train_batch`):

1. Build `training_dataloader` (seed `train_dataset_seed=42`) and `test_dataloader` (seed `test_dataset_seed=999`). **[C] See §6 for the train/val size discrepancy vs paper.**
2. Each batch: instantiate `batch_size` vectorized backbones, reset, then roll `n_step` segments until episode end; store transitions in a plain `Memory`.
3. Returns are computed by **backward discounted accumulation** `R ← γR + r` from a bootstrap value of the final state (not full GAE). Advantage = return − critic value. Surrogate = clipped ratio; value loss = clipped MSE. **[C]**
4. Every `update_best_model_epochs=3` epochs, run `rollout()` on the validation set with `per_eval_time=10` repeats; track best mean gBest. **[C]** `rollout.py` sets `set_seed(42)` before eval for fairness.
5. Checkpoints `epoch-{e}.pt` (actor+critic+optimizer+rng) under `outputs/<backbone>/function{id}_{dim}/<run_name>/`. **[C]**

**Action selection at test time:** `rollout` calls `agent.actor(state, to_critic=True)` which **samples** from `Normal(μ,σ)` (deterministic mean is not used). Evaluation is stochastic. **[C]**

---

## 6. Training-data distribution and generalization protocol

**[P] App. A.2 / [C] `utils/make_dataset.py`, `problems/cec_dataset.py`.**

- Dataset: **augmented CEC 2021** (f1–f10: single / hybrid / composition). Each instance is `F(x)=f(Mᵀ(x−o))` with random **shift** `o` and random **orthogonal rotation** `M`. **[P][C]**
- **[P] Paper protocol:** per problem class **1152 instances**, split **128 train : 1024 test** ("small training but large testing"); one agent per class; plus a mixed-class agent `f_mix` over all 10 classes.
- **[C] Code defaults (`options.py`):** `epoch_size=1024` (training instances per epoch), `val_size=128` (validation), seeds 42 / 999. This is the **inverse** of the paper's 128-train / 1024-test split sizes. **[P–C discrepancy]** Do not assume the public defaults reproduce the paper protocol; if GLEPPO ever needs to cite GLEET numbers, use the paper's split description, and if it needs to run GLEET, decide explicitly which split to use.
- Paper training-size ablation (App. B.5): sets 1/16/64/256/1024 — larger training sets help (supports distributional training).
- Generalization axes claimed **[P] Sec. 5.3 / App. B.3–B.4:** (a) zero-shot across function classes (e.g. Ag-f2→f5); (b) protein docking: 280 protein–protein complexes, 12D, 1000 maxFEs, zero-shot from 10D f_mix, GLEET-DMSPSO rank 1; (c) 10D→30D transfer; (d) pop-size transfer (trained at 100, tested at 500); (e) longer horizon (trained 2e5 FEs, run to 1e6).

**[A] Not verified in code:** the CEC 2021 dataset code license inside `problems/cec_dataset.py` / `cec_test_func.py` (embedded benchmark code of unclear provenance) and the protein-docking scripts (not present in the public repo file list). Treat docking generalization as paper-claim only.

---

## 7. Experimental baselines (paper)

**[P] Sec. 5.1 / B.2.** (Not re-run in this audit; GLEPPO does not treat these numbers as reproduced.)

- **Static:** vanilla PSO; vanilla DE/current-to-pbest/1 (B.2).
- **Adaptive:** DMSPSO, sDMSPSO, GLPSO; MadDE, NL-SHADE-LBC (B.2).
- **Learning-based:** DRL-PSO (Wu & Wang 2022), RLEPSO (Yin et al. 2021); DE-DDQN, DEDQN, LDE, RLDMDE, RLHPSDE (B.2).
- **Metrics:** mean / std / rank over 10 runs; average improvement vs backbone (paper claims GLEET-PSO ↑35% over PSO on their suite); Gap metric for generalization.
- Claimed outcome: GLEET backbones beat adaptive and prior learning-based baselines on augmented CEC 2021, with favorable cross-class, cross-dimension, cross-pop-size, and protein-docking transfer. **[P]**

---

## 8. What transfers to GLEPPO and what does not

| GLEET element | Transferable idea? | Why |
|---|---|---|
| Train once on a *distribution* of tasks, test on held-out instances | **Yes — as a protocol requirement** | Directly supports the "generalize to held-out task families" claim in GLEPPO's charter |
| Per-individual state with stagnation / progress / distance features | **Partially** | Population-level status features are useful; agent evolution needs *execution* signals (success rate, tool errors, cost) that GLEET never sees |
| Attention over population (set encoder) | **Yes, as architecture option** | Population-size invariance is desirable; must be justified on ablations |
| Continuous action = split of exploration/exploitation weights | **No** | GLEPPO's action should be a real *evolution decision* (operator / mutation intensity / parent pair), not a c1/c2 split of a PSO |
| Reward = relative gBest improvement | **No, not as-is** | Agent evolution reward must be grounded in real task execution outcomes (success, quality), not a numeric oracle |
| PPO + n-step returns + clipped value | **Yes, as training baseline to beat / reuse as algorithm** | PPO is GLEPPO's chosen trainer; the loop is standard and independently reimplementable |
| CEC2021 / PSO / DMSPSO | **No** | Wrong domain; GLEPPO needs LLM-agent genotypes and task environments |

**Adaptation gap (central):** GLEET's MDP is "tune numeric-optimizer hyper-parameters under oracle fitness". GLEPPO's MDP is "choose evolution decisions that modify LLM-agent genotypes, under sparse/noisy real execution feedback, across task families". Only the *training-protocol DNA* (distributional training, population state, PPO) is shared. Any contribution must live in the agent-evolution-specific decision problem, feedback, and generalization claim.

---

## 9. Facts vs assumptions

**Verified (code @ e715927):** state layout `(ps,9)` or `(ps,27)`, action→c1/c2 split via `c_sum`, four reward functions with `reward_scale=100`, PPO hyper-parameters in `options.py`, train/val instance seeds (42/999), `rollout.py` stochastic evaluation, no LICENSE file, no agent-evolution code in repo.

**Verified (paper arXiv HTML v1):** MDP equations (state 9 features, Gaussian joint action, Eq. 8 reward), transformer encoder/decoder design (128-d, 2 layers), CEC 2021 augmentation (1152 instances/class, 128 train : 1024 test), claimed baselines and generalization axes, ablations on state/reward/network/hyper-params, limitations (high-dimensional vulnerability, population size not dynamic during training).

**Paper vs code discrepancies (material for anyone citing or reusing GLEET):**

| Topic | Paper | Public code default |
|---|---|---|
| Network width / depth | 128-d, 2 encoder layers, MLP 128×256×128 | 16-d, 1 encoder layer, MLPs 32→8→1 |
| Train : test instance split | 128 : 1024 per class ("small train, large test") | `epoch_size=1024`, `val_size=128` (opposite sizes) |
| c1+c2 sum (PSO family) | c2 = 4 − c1 (sum 4) | DMSPSO `c1=c2=1.49445` (sum ≈ 2.99); GPSO `c=4.1` |
| γ, eps_clip, entropy/GAE coefs | not reported | `gamma=0.999`, `eps_clip=0.1` (code-only) |

Anyone who wants a GLEET reproduction must resolve these explicitly; GLEPPO will not rely on unqualified "GLEET achieves X" claims.

**Not verified:** reproduction of any paper number; protein-docking setup; exact CEC 2021 dataset license; DE appendix implementation (not in the public repo file list).

---

## 10. Implications for GLEPPO design (constraints, not decisions)

1. **Independence:** implement controller, environment, and PPO loop from scratch in GLEPPO; cite GLEET as the methodological reference only. No code copy (license + project isolation).
2. **Innovation bar:** "PPO controls an evolutionary process" is already GLEET's contribution in numeric EC. GLEPPO must contribute an *agent-evolution-specific* mechanism (see `research/CANDIDATE_MECHANISMS.md`).
3. **Reward integrity:** if reward is noisy real execution, it is unlike GLEET's oracle improvement reward — that difference must be handled explicitly (variance, multi-seed, reward normalization) and is itself a research question.
4. **Generalization protocol:** inherit GLEET's discipline — train on a distribution of task instances, freeze the controller, test on held-out families — but define "task family" for agents, not for CEC functions.
5. **Baseline suite:** a GLEET-style "PPO splits one continuous knob" control is a useful *weak* baseline; it must not be the only baseline (charter requires fixed / random / hand-designed adaptive / non-RL learned).

---

## 11. License checklist for future phases

- [x] Confirm GLEET code license before any reuse decision — **result: no license; no reuse**.
- [ ] If any GLEET algorithmic idea is implemented, write an independent specification first; implement without consulting GLEET source line-by-line during coding.
- [ ] Record provenance of any third-party benchmark (CEC, agent benchmarks) used in GLEPPO itself.
- [ ] Paper text of GLEET may be cited under ACM/arXiv terms; do not redistribute the PDF inside the GLEPPO repo without checking ACM terms.
