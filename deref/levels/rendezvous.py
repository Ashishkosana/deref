"""THE RENDEZVOUS — the two-pointer level (Two Sum II on a sorted array).

Also defines the three canonical solutions used by the tests to prove the
engine can tell the complexity classes apart:

    REFERENCE  two pointers   O(n) time,  O(1) space   <- the intended answer
    BRUTE      nested loops   O(n^2) time              <- correct but browns out
    HASHING    hash map       O(n) time,  O(n) space   <- passes, but costs space
"""

import random

from ..level import Level

REFERENCE = """
def solve(nums, target):
    L, R = 0, len(nums) - 1
    while L < R:
        s = nums[L] + nums[R]
        if s == target:
            return (L + 1, R + 1)
        if s > target:
            R -= 1
        else:
            L += 1
    return None
"""

BRUTE = """
def solve(nums, target):
    n = len(nums)
    for i in range(n):
        for j in range(i + 1, n):
            if nums[i] + nums[j] == target:
                return (i + 1, j + 1)
    return None
"""

HASHING = """
def solve(nums, target):
    seen = {}
    for i in range(len(nums)):
        c = target - nums[i]
        if c in seen:
            return (seen[c] + 1, i + 1)
        seen[nums[i]] = i
    return None
"""


def make_instance(n, seed):
    """Return ``(nums, target)`` with ``nums`` sorted and EXACTLY one valid pair.

    Uniqueness is guaranteed by construction: we build distinct values, look at
    every pairwise sum, and pick a target that occurs exactly once. O(n^2) to
    generate, which is fine because we only ever generate at sweep sizes
    (n <= 800), never at the huge extrapolated sizes.
    """
    rng = random.Random(seed * 1000 + n)
    if n < 2:
        # Degenerate sizes: no pair can exist; use a benign no-solution instance.
        return (list(range(1, n + 1)), 10 ** 9)

    values = sorted(rng.sample(range(1, 10 * n + 10), n))
    sums = {}
    for a in range(n):
        for b in range(a + 1, n):
            sums.setdefault(values[a] + values[b], []).append((a, b))
    unique_targets = [s for s, pairs in sums.items() if len(pairs) == 1]
    # With distinct spread-out values there is essentially always a unique sum;
    # fall back to a no-solution target if a pathological sample has none.
    target = rng.choice(unique_targets) if unique_targets else 10 ** 9
    return (values, target)


def make_worstcase(n, seed):
    """Return ``(nums, target)`` with NO valid pair, forcing full traversal.

    Values are strictly increasing and the target is chosen just below the
    smallest possible pair sum, so no solution returns early: two-pointer walks
    the whole array (O(n)), brute checks every pair (O(n^2)), hashing does a
    full pass (O(n)). Op-count then reflects true asymptotics, not answer
    position. The base offset and step are seed-randomised so the sweep input
    is not a fixed, detectable signature (e.g. no literal ``target == 1``).
    """
    rng = random.Random(1000 + seed)
    if n < 2:
        return ([rng.randrange(2, 50) for _ in range(n)], rng.randrange(1, 5))
    base = rng.randrange(1, 100)
    step = rng.choice([2, 3, 4])
    values = [base + step * k for k in range(n)]
    target = values[0] + values[1] - 1  # below the minimum pair sum -> no solution
    return (values, target)


LEVEL = Level(
    id="two-pointers/rendezvous",
    pattern="two_pointers",
    title="THE RENDEZVOUS",
    prompt=(
        "Given a 1-indexed array of integers `nums` sorted ascending, return "
        "the 1-based indices (i, j) of the two numbers that add up to `target`, "
        "or None if there is no such pair."
    ),
    func_name="solve",
    reference_solution=REFERENCE,
    target_class="O(n)",
    bound_names=("L", "R", "s", "i", "j"),
    input_names=("nums", "target"),
    make_instance=make_instance,
    make_worstcase=make_worstcase,
    edge_cases=[
        ([], 5),                 # empty
        ([3], 3),                # single element (no pair)
        ([4, 4], 8),             # duplicate pair at the boundary
        ([1, 2, 3], 100),        # no solution
        ([1, 2, 3, 4], 7),       # answer at the far end
        ([2, 3, 5, 8, 11, 15, 19, 24], 17),  # the canonical demo board
    ],
)
