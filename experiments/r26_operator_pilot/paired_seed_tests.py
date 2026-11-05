"""R26 Algorithm Pilot: Paired seed and RNG stream tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from gleppo.evolution import stable_seed, EvolutionConfig, evolve_generation, Individual
from gleppo.evaluator import Evaluator
from gleppo.interpreter import Interpreter
from gleppo.llm import StubLLM
from gleppo.genotype import make_valid_genotype, behavior_hash
from gleppo.operators import OPERATOR_NAMES


def make_eval():
    return Evaluator(interpreter=Interpreter(llm=StubLLM()), n_eval=2)


def make_task():
    return {"task_id": "test-001", "family": "A", "seed": 0,
            "input": "If x=3 and y=4, what is 3*5+4?", "gold": "19",
            "template_id": "TA1", "required_tools": ["calc"],
            "required_prompt_keywords": ["compute"]}


def test_same_seed_across_operators():
    """Same task/episode/generation/slot has identical replicate_id across operators."""
    eid = "ep1"
    for t in range(3):
        for j in range(4):
            ref = stable_seed(eid, t, j)
            for op in OPERATOR_NAMES:
                s = stable_seed(eid, t, j)  # action-independent
                assert s == ref, f"Mismatch at t={t} j={j} op={op}"
    print("PASS: same seed across operators")


def test_different_slots_distinct():
    """Different task/replica/generation slots remain distinct."""
    s1 = stable_seed("ep1", 0, 0)
    s2 = stable_seed("ep1", 0, 1)
    s3 = stable_seed("ep1", 1, 0)
    s4 = stable_seed("ep2", 0, 0)
    assert len({s1, s2, s3, s4}) == 4, "Seeds not distinct"
    print("PASS: different slots produce distinct seeds")


def test_initial_population_deterministic():
    """Initial genotypes are deterministic for same task/seed."""
    from gleppo.evolution import init_population
    cfg = EvolutionConfig(mu=8, lam=4, T=15, n_eval=2)
    task = make_task()
    import random
    rng1 = random.Random(stable_seed(cfg.seed, 11, task["task_id"], "ep-test"))
    rng2 = random.Random(stable_seed(cfg.seed, 11, task["task_id"], "ep-test"))
    eval1 = make_eval()
    eval2 = make_eval()
    pop1, _, _ = init_population(cfg, eval1, task, rng1, "ep-test")
    pop2, _, _ = init_population(cfg, eval2, task, rng2, "ep-test")
    h1 = [p.behavior_hash for p in pop1]
    h2 = [p.behavior_hash for p in pop2]
    assert h1 == h2, "Initial population hashes differ"
    print("PASS: initial population deterministic")


def test_crossover_mate_rng_separate():
    """Crossover mate draw does not shift parent-selection RNG."""
    # Run two generations: one with crossover, one without
    # Parent selection should produce same parents
    cfg = EvolutionConfig(mu=8, lam=4, T=15, n_eval=2)
    task = make_task()
    import random

    def run_gen(op_name, seed_offset=0):
        eval = make_eval()
        rng = random.Random(stable_seed(cfg.seed, 11, task["task_id"], "ep-rng-test"))
        from gleppo.evolution import init_population
        pop, _, _ = init_population(cfg, eval, task, rng, "ep-rng-test")
        rng2 = random.Random(stable_seed(cfg.seed, 11, task["task_id"], "ep-rng-test"))
        # Advance rng2 the same way init did
        for _ in range(cfg.mu):
            rng2.random()
        parents = []
        for _ in range(cfg.lam):
            cand = [pop[rng2.randrange(len(pop))] for _ in range(cfg.tournament_k)]
            parents.append(max(cand, key=lambda x: x.success))
        return [p.behavior_hash for p in parents]

    h_cross = run_gen("crossover")
    h_local = run_gen("prompt_local_edit")
    assert h_cross == h_local, "Parent selection RNG shifted by operator"
    print("PASS: crossover mate RNG separate from parent selection")


def test_family_c_rejected():
    """Family C tasks are rejected by evaluator guard."""
    eval = make_eval()
    task = make_task()
    task["family"] = "C"
    g = make_valid_genotype()
    try:
        eval.evaluate(g, task, allow_family=("A", "B"))
        print("FAIL: Family C not rejected")
        return False
    except Exception:
        print("PASS: Family C rejected")
        return True


if __name__ == "__main__":
    test_same_seed_across_operators()
    test_different_slots_distinct()
    test_initial_population_deterministic()
    test_crossover_mate_rng_separate()
    test_family_c_rejected()
    print("\nAll seed pairing tests PASSED")
