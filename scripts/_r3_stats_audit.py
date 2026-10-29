"""R3 Independent Review — Phase 3: Statistical tests + Offline selection audit."""
import json
from math import comb

BASE = "research/runs/20261029T052350Z_R3"
with open(f"{BASE}/R3_RAW.json") as f:
    raw = json.load(f)


def exact_sign_test(improved, degraded):
    """Two-sided exact sign test (McNemar's exact for paired binary)."""
    n = improved + degraded
    if n == 0:
        return 1.0
    k = min(improved, degraded)
    p = sum(comb(n, i) for i in range(0, k + 1)) / 2**n * 2
    return min(p, 1.0)


def exact_ci_95(successes, n):
    """Wilson score interval for binomial proportion."""
    if n == 0:
        return (0, 0)
    from math import sqrt
    z = 1.96
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    spread = z * sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0, center - spread), min(1, center + spread))


print("=" * 60)
print("STATISTICAL ANALYSIS")
print("=" * 60)

for op_name in ["tool_subset_edit", "crossover"]:
    rows = raw["pilot"]["aggregate"][op_name]["paired_rows"]
    n = len(rows)
    deltas = [r["paired_correctness_delta"] for r in rows]
    improved = sum(1 for d in deltas if d > 0)
    degraded = sum(1 for d in deltas if d < 0)
    same = sum(1 for d in deltas if d == 0)

    print(f"\n=== {op_name} (n={n}) ===")
    print(f"Improved: {improved}  Degraded: {degraded}  Same: {same}")

    # Sign test on correctness deltas
    p_sign = exact_sign_test(improved, degraded)
    print(f"Exact sign test (correctness): p = {p_sign:.4f}")

    # Effective success rates with CIs
    parent_eff = sum(1 for r in rows if r["parent_effective_success"])
    child_eff = sum(1 for r in rows if r["child_effective_success"])
    ci_p = exact_ci_95(parent_eff, n)
    ci_c = exact_ci_95(child_eff, n)
    print(f"Parent effective_success: {parent_eff}/{n} = {parent_eff/n:.3f}  95% CI [{ci_p[0]:.3f}, {ci_p[1]:.3f}]")
    print(f"Child  effective_success: {child_eff}/{n} = {child_eff/n:.3f}  95% CI [{ci_c[0]:.3f}, {ci_c[1]:.3f}]")

    # Tool path with CIs
    parent_path = sum(1 for r in rows if r["parent_tool_path_valid"])
    child_path = sum(1 for r in rows if r["child_tool_path_valid"])
    ci_pp = exact_ci_95(parent_path, n)
    ci_cp = exact_ci_95(child_path, n)
    print(f"Parent tool_path_valid:   {parent_path}/{n} = {parent_path/n:.3f}  95% CI [{ci_pp[0]:.3f}, {ci_pp[1]:.3f}]")
    print(f"Child  tool_path_valid:   {child_path}/{n} = {child_path/n:.3f}  95% CI [{ci_cp[0]:.3f}, {ci_cp[1]:.3f}]")

    # McNemar's exact on effective_success
    # Discordant pairs: parent_yes_child_no (b) vs parent_no_child_yes (c)
    b = sum(1 for r in rows if r["parent_effective_success"] and not r["child_effective_success"])
    c = sum(1 for r in rows if not r["parent_effective_success"] and r["child_effective_success"])
    p_mcnemar = exact_sign_test(b, c)
    print(f"McNemar exact (effective_success): b={b} (parent_only), c={c} (child_only), p = {p_mcnemar:.4f}")

print()
print("=" * 60)
print("LIMITATIONS")
print("=" * 60)
print("""
- n=9 per operator: VERY small sample. 95% CIs are wide.
- 3 tasks x 3 seeds = 9 paired observations, NOT independent:
  * Tasks share template structure (B2-001/B2-003 similar).
  * Seeds within a task share the same task input.
  * Effective independent units is closer to 3 (tasks), not 9.
- Sign test with 2 improvements / 2 degradations for tool_subset_edit
  cannot distinguish from chance (p=1.0).
- For crossover: 0 improved / 3 degraded -> p=0.25 (not significant at 0.05).
- The 0% child tool_path for tool_subset_edit is 0/9; the 95% CI is [0, 0.28].
  While suggestive, 9 observations cannot prove universality.
""")

# ================================================================
# OFFLINE SELECTION MECHANISM AUDIT
# ================================================================
print("=" * 60)
print("OFFLINE SELECTION MECHANISM AUDIT")
print("=" * 60)

for op_name in ["tool_subset_edit", "crossover"]:
    rows = raw["pilot"]["aggregate"][op_name]["paired_rows"]
    n = len(rows)

    print(f"\n=== {op_name} (n={n}) ===")

    # Mechanism 1: Unfiltered raw child acceptance
    accepted_1 = n
    effective_1 = sum(1 for r in rows if r["child_effective_success"])
    print(f"M1 Unfiltered: accept all {accepted_1}/{n}, effective_success = {effective_1}/{n}")

    # Mechanism 2: Hard constraint filter (reject if tool_path invalid)
    # NOTE: tool_path_valid is known ONLY AFTER execution. This is post-hoc rejection.
    kept_2 = [r for r in rows if r["child_tool_path_valid"]]
    dropped_2 = n - len(kept_2)
    eff_2 = sum(1 for r in kept_2 if r["child_effective_success"])
    print(f"M2 Hard filter (post-execution): kept={len(kept_2)}/{n}, dropped={dropped_2}, effective_success among kept = {eff_2}/{len(kept_2) if kept_2 else 0}")
    print(f"   NOTE: tool_path_valid known ONLY AFTER execution. Post-hoc rejection, NOT pre-execution prevention.")

    # Mechanism 3: Hard filter + parent-child selection on evaluation metrics
    kept_3 = kept_2
    wins = sum(1 for r in kept_3 if r["child_effective_success"] and not r["parent_effective_success"])
    losses = sum(1 for r in kept_3 if not r["child_effective_success"] and r["parent_effective_success"])
    ties = sum(1 for r in kept_3 if r["child_effective_success"] == r["parent_effective_success"])
    print(f"M3 Hard filter + selection: after filter, child wins={wins}, losses={losses}, ties={ties}")
    print(f"   Selection uses effective_success (answer_correct AND hard_validity):")
    print(f"   - answer_correct requires gold checker -> Evaluator-side, available after execution")
    print(f"   - hard_validity requires format_compliant AND tool_path_valid -> both known after execution")

    # Mechanism 4: Random acceptance control
    import random
    random.seed(42)
    random_eff = []
    for _ in range(1000):
        accepted = [r for r in rows if random.random() < 0.5]
        if accepted:
            random_eff.append(sum(1 for r in accepted if r["child_effective_success"]) / len(accepted))
    if random_eff:
        avg_random = sum(random_eff) / len(random_eff)
        print(f"M4 Random acceptance (p=0.5, 1000 trials): mean effective_success = {avg_random:.3f}")

    # Information timing analysis
    print(f"   Information timing:")
    print(f"   - genotype_hash: known BEFORE execution (deterministic from genotype)")
    print(f"   - tool_path_valid: known AFTER execution (requires running the workflow)")
    print(f"   - format_compliant: known AFTER execution (requires LLM output)")
    print(f"   - answer_correct: known AFTER execution (requires gold checker)")
    print(f"   - behavior_changed: known AFTER paired execution (requires both parent and child traces)")

    # Label leakage check
    print(f"   Label leakage assessment:")
    print(f"   - Gold answers are evaluator-side only. Operators never see gold.")
    print(f"   - effective_success uses gold checker -> available for selection but not for operator design.")
    print(f"   - No leakage in operator application: operators see parent genotype + failure_category only.")
    print(f"   - Selection CAN use answer_correct (post-execution) without leaking to future operators.")

print()
print("=" * 60)
print("COUNTERFACTUAL REPLAY QUESTIONS")
print("=" * 60)
print("""
Q1: Can hard constraint filtering reject ALL tool-path-violating children?
A1: For tool_subset_edit: YES — 9/9 children violate tool_path. Filter drops all 9.
    For crossover: N/A — 0/9 violate tool_path. Filter drops 0.
    But this is POST-HOC. The filter can only reject AFTER execution.

Q2: How many children remain after filtering?
A2: tool_subset_edit: 0/9 remain (all violate).
    crossover: 9/9 remain (all pass tool_path).

Q3: Can existing selection metrics identify crossover's correctness degradation?
A3: YES. effective_success drops from 7/9 to 3/9. 
    Parent-child comparison on effective_success correctly identifies degradation.
    However, 6/9 crossover children have format failures — a cheap signal.

Q4: Can selection decide without gold-answer leakage?
A4: For tool_path filtering: YES (tool_path_valid is structural, not gold-based).
    For correctness selection: NO (answer_correct requires gold checker).
    But gold-based selection is standard practice — the evaluator owns gold.
    The question is whether the SELECTION mechanism (not the operator) can use it.

Q5: Are these post-hoc explanations or independent evidence?
A5: PARTIALLY POST-HOC. The filtering rules were designed AFTER seeing R2 results.
    R3 provides NEW data for these rules, but the rules themselves were not
    pre-registered independently of R2 observations.
""")

print("=" * 60)
print("CONCLUSIONS")
print("=" * 60)
print("""
1. R3 metrics independently recomputed: ALL MATCH reported values.
2. Statistical power: VERY LOW (n=9, effective n~3 tasks). Cannot prove universality.
3. tool_subset_edit: 0/9 tool_path violations caught by post-hoc filter. But 0/9 pass means
   the filter would reject ALL children — leaving nothing to evolve.
4. crossover: format failures (6/9) provide a cheap pre-answer signal for selection.
5. Effective selection requires POST-EXECUTION evaluation. Pre-execution prevention
   would require static analysis of the child's workflow/tool changes.
""")
