# Literature Ledger

This is a starting ledger, not a completed novelty review. Every entry must be read and compared at the mechanism level before a novelty claim is made.

| Key | Work | Stable link | Current relevance | Review status |
|---|---|---|---|---|
| GLEET-2024 | Z. Ma et al., “Auto-configuring Exploration-Exploitation Tradeoff in Evolutionary Computation via Deep Reinforcement Learning,” GECCO 2024, pp. 1497–1505 | [Official implementation](https://github.com/MetaEvo/GLEET) | Primary reference for PPO-trained control of evolutionary search; must audit the paper and code, not only adapt the interface | Pending source audit |
| RL-EA-SURVEY-2023 | “Reinforcement Learning-assisted Evolutionary Algorithm: A Survey and Research Opportunities” | [arXiv:2308.13420](https://arxiv.org/abs/2308.13420) | Taxonomy and related work for RL-based operator selection, parameter adaptation, and other EA control decisions | Pending full-text review |
| PROMPTBREEDER-2023 | “Promptbreeder: Self-Referential Self-Improvement via Prompt Evolution” | [arXiv:2309.16797](https://arxiv.org/abs/2309.16797) | Relevant neighboring line for evolutionary improvement of prompts; compare actual genotype, variation, fitness, and adaptation mechanism | Pending full-text review |

## Required fields for every new paper

- Full title, authors, venue/year, DOI or arXiv ID.
- Official paper URL and code URL (if any).
- Search/evolution object and representation.
- Controller architecture and training procedure.
- State, action, reward/fitness and feedback source.
- Baselines, tasks, seeds, metrics, and generalization setup.
- What is genuinely different from GLEPPO's current hypothesis.
- Overlap risk: high / medium / low, with an evidence-based explanation.
- Review date and reviewer notes.

Do not mark a paper as “no overlap” from title or abstract alone.
