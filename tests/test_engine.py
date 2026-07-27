"""Engine tests. Runs under pytest, or standalone: ``python3 tests/test_engine.py``.

The load-bearing assertions: the engine must tell O(n), O(n log n), and O(n^2)
apart, and must brown out a correct-but-quadratic solution.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deref.complexity import fit_class  # noqa: E402
from deref.errors import DerefError  # noqa: E402
from deref.level import verify  # noqa: E402
from deref.levels.rendezvous import BRUTE, HASHING, LEVEL, REFERENCE  # noqa: E402
from deref.tracer import run_traced  # noqa: E402


def test_two_pointer_solves_and_is_linear():
    verdict, frames = verify(LEVEL, REFERENCE)
    assert verdict.correctness_pass
    assert verdict.fitted_class == "O(n)"
    assert verdict.complexity_pass
    assert verdict.solved
    assert len(frames) > 0
    assert any("L" in f.vars and "R" in f.vars for f in frames)


def test_brute_is_quadratic_and_browns_out():
    verdict, _ = verify(LEVEL, BRUTE)
    assert verdict.correctness_pass          # brute is correct...
    assert verdict.fitted_class == "O(n^2)"  # ...but quadratic
    assert not verdict.complexity_pass       # so it browns out at scale
    assert not verdict.solved


def test_hashing_is_linear_but_costs_space():
    verdict, _ = verify(LEVEL, HASHING)
    assert verdict.correctness_pass
    assert verdict.fitted_class == "O(n)"
    assert verdict.complexity_pass
    assert verdict.space_hi > 0


def test_two_pointer_uses_no_aux_space():
    verdict, _ = verify(LEVEL, REFERENCE)
    assert verdict.space_hi == 0


def test_wrong_solution_fails_correctness():
    wrong = "def solve(nums, target):\n    return (1, 2)\n"
    verdict, _ = verify(LEVEL, wrong)
    assert not verdict.correctness_pass
    assert not verdict.solved


def test_runaway_solution_is_caught():
    runaway = (
        "def solve(nums, target):\n"
        "    L, R = 0, len(nums) - 1\n"
        "    while L < R:\n"
        "        pass\n"          # forgets to move a pointer -> infinite loop
        "    return None\n"
    )
    verdict, _ = verify(LEVEL, runaway)
    assert not verdict.complexity_pass
    assert not verdict.solved


def test_fit_class_basic():
    linear = [(n, 5 * n) for n in (50, 100, 200, 400, 800)]
    quad = [(n, 2 * n * n) for n in (50, 100, 200, 400, 800)]
    assert fit_class(linear)[0] == "O(n)"
    assert fit_class(quad)[0] == "O(n^2)"


def test_fit_ignores_large_additive_constant():
    # ops = 2n^2 + 60000: a big fixed setup cost must NOT flatten to O(n).
    padded_quad = [(n, 2 * n * n + 60000) for n in (50, 100, 200, 400, 800)]
    assert fit_class(padded_quad)[0] == "O(n^2)"


# ---- regression tests for the adversarial-review findings ----

def _grade(src):
    return verify(LEVEL, src)[0]


def test_slice_copy_quadratic_browns_out():
    # A per-iteration slice copy is genuinely O(n^2); it must not pass as O(n).
    src = (
        "def solve(nums, target):\n"
        "    seen = {}\n"
        "    for i in range(len(nums)):\n"
        "        c = target - nums[i]\n"
        "        if c in seen:\n"
        "            return (seen[c] + 1, i + 1)\n"
        "        seen[nums[i]] = i\n"
        "        _ = nums[i:]\n"
        "    return None\n"
    )
    assert not _grade(src).complexity_pass


def test_method_scan_quadratic_browns_out():
    # nums.index() is an O(n) scan; using it per element is O(n^2).
    src = (
        "def solve(nums, target):\n"
        "    n = len(nums)\n"
        "    for i in range(n):\n"
        "        c = target - nums[i]\n"
        "        try:\n"
        "            j = nums.index(c, i + 1)\n"
        "            return (i + 1, j + 1)\n"
        "        except ValueError:\n"
        "            pass\n"
        "    return None\n"
    )
    assert not _grade(src).complexity_pass


def test_concat_building_quadratic_browns_out():
    # Accumulating into a list with += is genuinely O(n^2).
    src = (
        "def solve(nums, target):\n"
        "    seen = {}\n"
        "    log = []\n"
        "    for i in range(len(nums)):\n"
        "        c = target - nums[i]\n"
        "        if c in seen:\n"
        "            return (seen[c] + 1, i + 1)\n"
        "        seen[nums[i]] = i\n"
        "        log += [nums[i]]\n"
        "    return None\n"
    )
    assert not _grade(src).complexity_pass


def test_sort_method_is_nlogn_not_linear():
    # Sorting via the .sort() method then two-pointering is O(n log n), which is
    # worse than the O(n) target and must fail.
    src = (
        "def solve(nums, target):\n"
        "    nums = list(nums)\n"
        "    nums.sort()\n"
        "    L, R = 0, len(nums) - 1\n"
        "    while L < R:\n"
        "        s = nums[L] + nums[R]\n"
        "        if s == target:\n"
        "            return (L + 1, R + 1)\n"
        "        if s > target:\n"
        "            R -= 1\n"
        "        else:\n"
        "            L += 1\n"
        "    return None\n"
    )
    assert not _grade(src).complexity_pass


def test_range_membership_not_overcharged():
    # `x in range(n)` is O(1); adding it must not flip a correct O(n) solution
    # into a quadratic false-fail.
    src = (
        "def solve(nums, target):\n"
        "    n = len(nums)\n"
        "    L, R = 0, n - 1\n"
        "    while L < R:\n"
        "        if L in range(n):\n"
        "            s = nums[L] + nums[R]\n"
        "            if s == target:\n"
        "                return (L + 1, R + 1)\n"
        "            if s > target:\n"
        "                R -= 1\n"
        "            else:\n"
        "                L += 1\n"
        "    return None\n"
    )
    v = _grade(src)
    assert v.solved and v.complexity_pass


def test_gamed_worstcase_still_quadratic():
    # A brute force that tries to detect the old fixed sweep signature must not
    # escape: the worst-case target is randomised, so this stays O(n^2).
    src = (
        "def solve(nums, target):\n"
        "    if target == 1:\n"
        "        return None\n"
        "    n = len(nums)\n"
        "    for i in range(n):\n"
        "        for j in range(i + 1, n):\n"
        "            if nums[i] + nums[j] == target:\n"
        "                return (i + 1, j + 1)\n"
        "    return None\n"
    )
    assert not _grade(src).complexity_pass


def test_eafp_exception_solution_runs():
    # An idiomatic try/except KeyError solution must run (exception classes are
    # in the sandbox) and grade as a correct O(n) solution.
    src = (
        "def solve(nums, target):\n"
        "    seen = {}\n"
        "    for i in range(len(nums)):\n"
        "        try:\n"
        "            j = seen[target - nums[i]]\n"
        "            return (j + 1, i + 1)\n"
        "        except KeyError:\n"
        "            seen[nums[i]] = i\n"
        "    return None\n"
    )
    v = _grade(src)
    assert v.correctness_pass and v.solved


def test_crashing_solution_does_not_crash_grader():
    # A solution that raises only at large n must yield a verdict, not an
    # unhandled exception out of verify().
    src = (
        "def solve(nums, target):\n"
        "    if len(nums) > 40:\n"
        "        return nums[10 ** 9]\n"
        "    return None\n"
    )
    v = _grade(src)  # must not raise
    assert not v.solved


def test_dunder_escape_is_blocked():
    # Dunder attribute access is banned at the AST level.
    escape = (
        "def solve(nums, target):\n"
        "    return ().__class__.__bases__[0].__subclasses__()\n"
    )
    raised = False
    try:
        run_traced(escape, "solve", ([1, 2], 3))
    except DerefError:
        raised = True
    assert raised
    assert not _grade(escape).solved


# ---- standalone runner (no pytest needed) ----
if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for t in tests:
        try:
            t()
        except AssertionError as exc:
            print("FAIL %s: %s" % (t.__name__, exc))
        except Exception as exc:  # noqa: BLE001
            print("ERROR %s: %r" % (t.__name__, exc))
        else:
            passed += 1
            print("ok   %s" % t.__name__)
    print("-" * 40)
    print("%d/%d passed" % (passed, len(tests)))
    raise SystemExit(0 if passed == len(tests) else 1)
