"""R21 Phase 1: R20 audit."""
import re

content = open("gleppo/answer_binding.py").read()

print("=== R20 Audit ===")

# Check for task_id branching in computation logic
if "if task_id ==" in content or "task_id ==" in content:
    print("WARNING: task_id branching found")
else:
    print("OK: no task_id branching in computation")

# Check for gold/expected reading
if "gold" in content.lower() or "expected_answer" in content.lower():
    print("WARNING: gold/expected reading found")
else:
    print("OK: no gold/expected reading")

# Check for DONE-33 hardcoding
if "DONE-33" in content:
    print("WARNING: DONE-33 hardcoding found")
else:
    print("OK: no DONE-33 hardcoding")

# Check abstain logic
if "abstain" in content.lower() or "AbstainReason" in content:
    print("OK: abstain logic present")
else:
    print("WARNING: no abstain logic")

# Check type checking
if "TYPE_MISMATCH" in content:
    print("OK: type checking present")
else:
    print("WARNING: no type checking")

# Check dependency checking
if "INCOMPLETE_DEPENDENCY" in content:
    print("OK: dependency checking present")
else:
    print("WARNING: no dependency checking")

print()
print("=== Test Count ===")
print("R19: 451 tests (included test_r19_answer_binding.py)")
print("R20: 450 tests (removed test_r19_answer_binding.py, added test_r20_dac.py)")
print("Difference: -1 test (old R19 test removed as API changed)")
print("R20 DAC tests: 14 tests")
