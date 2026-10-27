"""GLEPPO ECOS environment core (Phase 2A).

Independent implementation. No GLEET code is used or referenced.
"""
from .genotype import Genotype, canonical_serialize, behavior_hash, validate_genotype
from .operators import OPERATORS, apply_operator, OPERATOR_NAMES
from .tasks import build_task, FAMILY_A, FAMILY_B, FAMILY_C
from .evaluator import Evaluator, EvalResult
from .evolution import EvolutionConfig, evolve, evolve_generation
from .features import STATE_DIM, state_vector
from .llm import StubLLM

__all__ = [
    "Genotype", "canonical_serialize", "behavior_hash", "validate_genotype",
    "OPERATORS", "apply_operator", "OPERATOR_NAMES",
    "build_task", "FAMILY_A", "FAMILY_B", "FAMILY_C",
    "Evaluator", "EvalResult",
    "EvolutionConfig", "evolve", "evolve_generation",
    "STATE_DIM", "state_vector",
    "StubLLM",
]
