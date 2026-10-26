# Literature Ledger

**Last updated:** 2026-10-26 (P0.1 audit, post related-work pass)  
**Policy:** mechanism-level entries only. Title/abstract similarity is not evidence. **V** = page opened at source during this audit; **U** = from survey citation / search snippet / memory only — do not treat as verified.

Required fields: title, authors, venue/year, DOI/arXiv; paper + code URLs; evolution object; controller; state/action/reward or fitness; training distribution & generalization; baselines; difference vs GLEPPO; overlap risk + evidence; review date.

---

## Summary table

| Key | Work | Link | Evolution object | Controller | Overlap vs GLEPPO | Status |
|---|---|---|---|---|---|---|
| GLEET-2024 | Ma et al., GECCO 2024 | [arXiv:2404.08239](https://arxiv.org/abs/2404.08239) · [code](https://github.com/MetaEvo/GLEET) | Numeric EC hyper-params (c1/c2 split) | PPO-style DRL (Transformer policy) | **High (method parent)** | V · code audited |
| RL-EA-SURVEY-2023 | Song et al., SWEVO / arXiv 2308.13420 | [arXiv:2308.13420](https://arxiv.org/abs/2308.13420) | Taxonomy (operators, params, solution gen) | Survey (mostly Q-learning for operator selection) | **High (novelty fence)** | V |
| DRL-PSO-2022 | Wu & Wang, IEEE TEVC 2022 | paywalled (no arXiv found) | PSO hyper-params | DRL (per memory/survey) | Medium | **U** |
| RLEPSO-2022 | Yin, arXiv:2206.00835 | [arXiv:2206.00835](https://arxiv.org/abs/2206.00835) | PSO parameters | DDPG (per survey) | Medium | **U** (ID from survey) |
| META-ES-2023 | Lange et al., ICLR 2023 | [arXiv:2211.11260](https://arxiv.org/abs/2211.11260) | ES update rule (NN) | Meta-evolution (not PPO) | Medium | V |
| LEARNED-GA-2023 | Lange et al., arXiv 2304.03995 | [arXiv:2304.03995](https://arxiv.org/abs/2304.03995) | GA selection + mutation-rate modules | Meta-BBO (not PPO) | **Medium-High** | V |
| PROMPTBREEDER-2023 | Fernando et al. | [arXiv:2309.16797](https://arxiv.org/abs/2309.16797) | Task-prompts + mutation-prompts | None (LLM mutate; train-set fitness) | Low-Medium | V |
| FUNSEARCH-2024 | Romera-Paredes et al., Nature 625:468–475 | [DOI 10.1038/s41586-023-06924-6](https://doi.org/10.1038/s41586-023-06924-6) | Programs (priority/heuristic fns) | Frozen LLM + evaluator, islands EA | Low | V |
| EOH-2024 | Liu et al. | [arXiv:2401.02051](https://arxiv.org/abs/2401.02051) | Heuristics (thoughts + code) | LLM + EC ops | Low | V |
| REEVO-2024 | Ye et al., NeurIPS 2024 | [arXiv:2402.01145](https://arxiv.org/abs/2402.01145) | Heuristics / meta-heuristics | LLM reflection ("verbal gradient") | Low | V |
| ADAS-2024 | Hu, Lu, Clune | [arXiv:2408.08435](https://arxiv.org/abs/2408.08435) | Agentic systems as code | Meta agent programs; archive | **Medium-High** | V |
| ALPHAEVOLVE-2025 | Novikov et al., DeepMind | [arXiv:2506.13131](https://arxiv.org/abs/2506.13131) | Algorithm code | LLM pipeline + evaluators | Medium | V |
| DGM-2025 | Zhang et al. | [arXiv:2505.22954](https://arxiv.org/abs/2505.22954) · [code](https://github.com/jennyzzt/dgm) | Self-modifying agent code | FM rewrite + archive | **Medium-High** | V |
| SHINKAEVOLVE-2025 | Lange, Imajuku, Cetin | [arXiv:2509.19349](https://arxiv.org/abs/2509.19349) | Programs / agentic harnesses | LLM mutator + **bandit ensemble selection** | **Medium** | V |
| HELIOS-2026 | (listed via search) | arXiv 2609.09164 | LLM-evolved policies | LLM evolver; **DQN as baseline meta-controller** | Medium | **U** (listing only) |
| SYMBOL / RL-DAS / EVOTF | cited by GLEET paper | IDs unresolved | (presumed optimizer/algorithm search) | — | Low | **U — do not cite as verified** |

---

## Verified entries (mechanism level)

### GLEET-2024 (methodological parent — full audit in `research/GLEET_BASELINE_AUDIT.md`)

- Ma, Chen, Guo, Ma, Gong. GECCO 2024, pp. 1497–1505. DOI 10.1145/3638529.3653996. arXiv:2404.08239.
- Object: positions of PSO/DMSPSO/DE population on numeric black-box functions (augmented CEC 2021).
- Controller: PPO; Transformer-set actor (encoder + EET decoder), MLP critic.
- State: 9 features/individual × (population, exploration, exploitation).
- Action: Gaussian in [0,1] splitting c1+c2 (M=1) or DE params (M=3).
- Reward: r = (f(gBest^{t-1})−f(gBest^t))/f(gBest^0), oracle fitness, dense.
- Train/test: distributional instances; paper 128:1024 train/test per class; code defaults inverted. Generalizes across classes, dims, pop sizes, horizons, protein docking.
- **No LICENSE in code repo — do not copy.**
- **Difference vs GLEPPO:** numeric optimizer under oracle fitness; no agents, no execution traces, no operator/parent decisions.
- **Overlap risk: High (mechanics), Low (problem).**

### RL-EA-SURVEY-2023 — novelty fence

- Song et al. arXiv:2308.13420 (v3, 2024). SWEVO.
- Taxonomy: RL assists EA via **solution generation, learnable objective, algorithm/operator/sub-population selection, parameter adaptation**.
- **Verified fact for positioning:** operator-selection RL-EAs are almost all **value-based (Q-learning)**, not policy-gradient/PPO.
- **Difference vs GLEPPO:** fence, not a competitor. "RL selects operators / adapts parameters" is already a known category; "PPO for agent evolution" alone is not a contribution. The survey's Q-learning dominance slightly supports a *PPO-vs-Q-learning* methodological contrast but does **not** by itself create an application-level novelty.
- **Overlap risk: High (fence).**

### META-ES-2023 and LEARNED-GA-2023 — learned controllers of evolution without PPO

- Meta-ES: Lange et al., ICLR 2023, arXiv:2211.11260. Self-attention ES update rule discovered by meta-evolution; train on small analytic problems → transfer to unseen problems/dims/horizons/control.
- Learned GA: Lange et al., arXiv:2304.03995. Cross-/self-attention modules for **selection + mutation-rate adaptation**, trained by meta-BBO; transfers to unseen problems/dims/budgets and plugs into conventional GAs.
- **Difference vs GLEPPO:** controller is meta-evolved NN, object is black-box functions, fitness is optimizer performance — not agent execution. But they already "learn how evolution should make operator/selection decisions".
- **Overlap risk: Medium-High (Learned GA).** Any GLEPPO operator/parent-selection claim must distinguish from 2304.03995 at the mechanism level (execution-feedback state, LLM agents, PPO training across task families).

### LLM evolution line (Promptbreeder, FunSearch, EoH, ReEvo, AlphaEvolve, ADAS, DGM, ShinkaEvolve)

| Work | Object | How variation happens | How selection happens | Learned controller? |
|---|---|---|---|---|
| Promptbreeder 2309.16797 | task- + mutation-prompts | LLM self-referential mutation | train-set fitness | No |
| FunSearch (Nature 2024) | programs | frozen LLM samples | evaluator score, islands, best-shot | No |
| EoH 2401.02051 | heuristics (NL+code) | LLM mutate/crossover | COP quality | No |
| ReEvo 2402.01145 (NeurIPS 2024) | heuristics | LLM "verbal gradient" reflection | COP score | No |
| AlphaEvolve 2506.13131 | algorithm code | LLM pipeline | evaluators | No |
| ADAS 2408.08435 | agentic systems (code) | meta agent programs from archive | task reward | No (LLM is the designer) |
| DGM 2505.22954 | self-modifying agent code | FM rewrites sampled archived agent | empirical benchmark validation | No (archive sampling) |
| ShinkaEvolve 2509.19349 | programs / harnesses | LLM mutator | **bandit ensemble selection** + novelty reject | Partial (bandit, not PPO) |

- **Difference vs GLEPPO:** this line already does "evolve LLM agents/programs with real evaluation feedback". What none of the **verified** set does: a **trained PPO policy** over a **restricted evolutionary-decision family**, whose state includes **agent task-execution outcomes**, trained on task instances and tested on **held-out task families**.
- **ShinkaEvolve is the closest adaptive non-RL selection mechanism (bandit).** It makes GLEPPO's B3 (bandit) baseline *mandatory*, not optional: if a bandit matches PPO, the "trained controller" claim dies.
- **ADAS/DGM are the closest agent-level systems.** They make an LLM-as-operator baseline (B5) mandatory under equal evaluation budget.
- **Overlap risk: Medium to Medium-High** depending on how narrow GLEPPO's claim is. A broad claim ("we evolve agents with feedback") collides; a narrow claim ("a small PPO policy conditioned on execution failure signals chooses among restricted variation operators and transfers across task families") does not collide with the verified set.

### HELIOS / other 2026 listings (U)

- HELIOS (arXiv 2609.09164, listing only): LLM-evolved policies with DQN as a *baseline* meta-controller — direction inverted (LLM evolves, RL is baseline). Not verified at source.
- CosmoCore-Evo 2512.21351 (listing): dream-replay RL *with* evolutionary mutation of trajectories — EA inside RL, not RL controlling agent evolution.
- HARNESSEVO 2609.02889, MECo 2610.03316 (listings): reflective harness evolution / multi-task LLM heuristic evolution without RL controllers.

---

## Gap statement (P0.1, search-bounded)

**Claim to be tested, not a literature-proof:**

> No *verified* work trains a **PPO policy** whose state includes **real agent task-execution feedback**, whose actions are **population-level evolutionary decisions for LLM agents** (operator / mutation intensity / parent pair), trained across task instances and evaluated on **held-out task families** against bandit and adaptive baselines.

**Evidence strength:** 14 papers opened at mechanism level; arXiv title/abstract searches for the conjunction returned no collision (one inverted-direction hit). **Bounded by:** arXiv-centric search; DRL-PSO/RLEPSO primary sources not opened (IEEE); Symbol/RL-DAS/EvoTF IDs unresolved; websearch tool was unavailable so no Google Scholar / Semantic Scholar sweep. **Re-check required before any publication-level novelty claim** (Phase 0.2 depth or as a pre-submission step).

**If the conjunction is empty in 2026, it is still not a paper.** The contribution lives or dies on beating B2/B3/B5 under held-out transfer (see `research/CANDIDATE_MECHANISMS.md`).

---

## Unverified / pending (do not cite as fact)

| Key | Why it matters | What is missing |
|---|---|---|
| DRL-PSO (Wu & Wang, TEVC 2022) | GLEET's main learning-based baseline | IEEE paywall; no arXiv copy found |
| RLEPSO-2021 / Yin line | policy-gradient EET control | full abs not opened; DDPG claim via survey |
| Symbol (Lion?), RL-DAS, EvoTF | GLEET related-work mentions | arXiv IDs unresolved; EvoTF zero hits |
| HELIOS 2609.09164 | recent RL-baseline + LLM-evolver | listing only |
| FunSearch code license / EoH-ReEvo code licenses | if ever used as baseline code | not checked (Phase 2 task) |

---

## Entry template

```
## Entry: KEY-YEAR
- Citation: ...
- Code: ... (license if any)
- Evolution object: ...
- Controller: ...
- State / action / reward or fitness: ...
- Training distribution & generalization: ...
- Baselines: ...
- What is different from GLEPPO: ...
- Overlap risk: High | Medium | Low — evidence
- Review date:
```
