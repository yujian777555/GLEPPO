"""R26 Algorithm Pilot: Pilot context, RULE, LINUCB, QLEARN controllers.

Pilot-only code. NOT canonical 32-D state. NOT PC1. StubLLM only.
"""
import math
import random
from typing import Dict, List, Optional, Tuple

OPERATOR_NAMES = [
    "prompt_local_edit", "prompt_critique_rewrite", "tool_subset_edit",
    "workflow_step_edit", "crossover",
]

PILOT_CONTEXT_DIM = 15
PILOT_CONTEXT_VERSION = "pilot_context_v1"


def pilot_context_v1(best: float, mean: float, t: int, T: int,
                     stagnation: int, fail_rates: dict,
                     valid_rate: float, op_delta_mean: float,
                     rewards_last3: List[float],
                     tool_sets: List[List[str]], workflows: List[List[str]],
                     op_usage: Dict[str, int]) -> List[float]:
    """Deterministic pilot context from controller-visible data only.

    15 dims. NOT the canonical 32-D state. No gold/task answer/evaluator internals.
    """
    def c01(x): return max(0.0, min(1.0, float(x)))

    # Diversity (Jaccard distance)
    def jaccard_dist(a, b):
        sa, sb = set(a), set(b)
        if not sa and not sb: return 0.0
        return 1.0 - len(sa & sb) / max(1, len(sa | sb))

    div_tools = 0.0; div_wf = 0.0; pairs = 0
    for i in range(len(tool_sets)):
        for j in range(i + 1, len(tool_sets)):
            div_tools += jaccard_dist(tool_sets[i], tool_sets[j])
            div_wf += jaccard_dist(workflows[i], workflows[j])
            pairs += 1
    if pairs > 0:
        div_tools /= pairs; div_wf /= pairs

    # Operator entropy
    counts = list(op_usage.values()); total = sum(counts); ent = 0.0
    if total > 0:
        for c in counts:
            if c > 0:
                p = c / total; ent -= p * math.log(p)
        ent /= math.log(5.0)

    # Mean reward last 3
    mr3 = sum(rewards_last3[-3:]) / max(1, len(rewards_last3[-3:])) if rewards_last3 else 0.0

    return [
        c01(best),
        c01(mean),
        c01(best - mean),
        c01(t / max(1, T)),
        c01(stagnation / max(1, T)),
        c01(fail_rates.get("format_error", 0.0)),
        c01(fail_rates.get("tool_error", 0.0)),
        c01(fail_rates.get("wrong_answer", 0.0)),
        c01(fail_rates.get("timeout", 0.0)),
        c01(valid_rate),
        max(-1.0, min(1.0, op_delta_mean)),
        max(-1.0, min(1.0, mr3)),
        c01(div_tools),
        c01(div_wf),
        c01(ent),
    ]


class RuleController:
    """Phase 1 B2 hand rule, literally implemented."""

    def __init__(self):
        self.op_history: List[Tuple[str, float]] = []  # (op_name, op_delta_mean)
        self.stagnation = 0
        self.last_best = 0.0

    def select(self, t: int, best: float, mean: float, history: list) -> str:
        if history:
            last = history[-1]
            self.op_history.append((last["op"], last.get("op_delta_mean", 0.0)))
            if best <= self.last_best + 1e-9:
                self.stagnation += 1
            else:
                self.stagnation = 0
        self.last_best = best

        # Stagnation >= 4 -> tool_subset_edit
        if self.stagnation >= 4:
            return "tool_subset_edit"

        # Check last operator's last 5 uses
        if self.op_history:
            last_op = self.op_history[-1][0]
            recent = [(op, d) for op, d in self.op_history[-5:] if op == last_op]
            positive = sum(1 for _, d in recent if d > 0)
            if positive >= 2:
                return last_op

        return "crossover"

    def initial_fallback(self) -> str:
        return "prompt_critique_rewrite"


class LinUCBController:
    """One linear model per action. A_a=I, b_a=0. alpha=1."""

    def __init__(self, dim: int = PILOT_CONTEXT_DIM, alpha: float = 1.0):
        self.dim = dim
        self.alpha = alpha
        self.A = {op: [[1.0 if i == j else 0.0 for j in range(dim)] for i in range(dim)]
                  for op in OPERATOR_NAMES}
        self.b = {op: [0.0] * dim for op in OPERATOR_NAMES}
        self.frozen = False

    def _solve(self, op: str, x: List[float]) -> Tuple[float, float]:
        """Return (theta^T x, uncertainty). Simple conjugate gradient-free solve."""
        A = self.A[op]; b = self.b[op]
        # Solve A theta = b via Gaussian elimination (dim=15, fine for pilot)
        n = self.dim
        M = [row[:] + [b[i]] for i, row in enumerate(A)]
        for col in range(n):
            pivot = max(range(col, n), key=lambda r: abs(M[r][col]))
            M[col], M[pivot] = M[pivot], M[col]
            if abs(M[col][col]) < 1e-12: continue
            for r in range(n):
                if r != col:
                    f = M[r][col] / M[col][col]
                    for c in range(col, n + 1):
                        M[r][c] -= f * M[col][c]
        theta = [M[i][n] / M[i][i] if abs(M[i][i]) > 1e-12 else 0.0 for i in range(n)]
        pred = sum(t * xi for t, xi in zip(theta, x))
        # Uncertainty: x^T A^{-1} x (approximate via solving A y = x)
        My = [row[:] + [x[i]] for i, row in enumerate(A)]
        for col in range(n):
            pivot = max(range(col, n), key=lambda r: abs(My[r][col]))
            My[col], My[pivot] = My[pivot], My[col]
            if abs(My[col][col]) < 1e-12: continue
            for r in range(n):
                if r != col:
                    f = My[r][col] / My[col][col]
                    for c in range(col, n + 1):
                        My[r][c] -= f * My[col][c]
        y = [My[i][n] / My[i][i] if abs(My[i][i]) > 1e-12 else 0.0 for i in range(n)]
        unc = sum(xi * yi for xi, yi in zip(x, y))
        return pred, math.sqrt(max(0.0, unc))

    def select(self, x: List[float]) -> str:
        best_op = OPERATOR_NAMES[0]; best_val = -1e18
        for op in OPERATOR_NAMES:
            pred, unc = self._solve(op, x)
            val = pred + self.alpha * unc
            if val > best_val:
                best_val = val; best_op = op
        return best_op

    def update(self, op: str, x: List[float], reward: float):
        if self.frozen: return
        for i in range(self.dim):
            for j in range(self.dim):
                self.A[op][i][j] += x[i] * x[j]
            self.b[op][i] += reward * x[i]

    def freeze(self):
        self.frozen = True


class QLearnController:
    """Tabular Q-learning over discretized pilot context."""

    def __init__(self, gamma=0.95, alpha=0.1, eps_start=0.20, eps_end=0.05):
        self.gamma = gamma; self.alpha = alpha
        self.eps_start = eps_start; self.eps_end = eps_end
        self.Q: Dict[Tuple, Dict[str, float]] = {}
        self.n_decisions = 0
        self.total_train_decisions = 12 * 2 * 15  # estimate for decay
        self.frozen = False
        self._last_state = None
        self._last_op = None

    def _discretize(self, x: List[float]) -> Tuple:
        """Discretize each dim to 3 bins: low/mid/high."""
        bins = []
        for v in x:
            if v < 0.33: bins.append(0)
            elif v < 0.67: bins.append(1)
            else: bins.append(2)
        return tuple(bins)

    def _get_q(self, state: Tuple) -> Dict[str, float]:
        if state not in self.Q:
            self.Q[state] = {op: 0.0 for op in OPERATOR_NAMES}
        return self.Q[state]

    def select(self, x: List[float], training: bool = True) -> str:
        state = self._discretize(x)
        eps = self.eps_end + (self.eps_start - self.eps_end) * max(0, 1 - self.n_decisions / max(1, self.total_train_decisions))
        if training and random.random() < eps:
            op = random.choice(OPERATOR_NAMES)
        else:
            q = self._get_q(state)
            best_val = max(q.values())
            best_ops = [k for k, v in q.items() if v == best_val]
            op = best_ops[0]
        self._last_state = state
        self._last_op = op
        self.n_decisions += 1
        return op

    def update(self, reward: float, next_x: Optional[List[float]] = None, terminal: bool = False):
        if self.frozen or self._last_state is None or self._last_op is None: return
        q = self._get_q(self._last_state)
        if terminal or next_x is None:
            target = reward
        else:
            next_state = self._discretize(next_x)
            next_q = self._get_q(next_state)
            target = reward + self.gamma * max(next_q.values())
        q[self._last_op] += self.alpha * (target - q[self._last_op])

    def finalize_episode(self, final_reward: float):
        """Apply final generation reward to final action."""
        self.update(final_reward, terminal=True)

    def freeze(self):
        self.frozen = True
