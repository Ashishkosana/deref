"""Levels are data, and the two-gate verifier that grades a solution.

Gate 1 (correctness) is the *grade*: the solution must match the reference
solution on edge cases + generated instances. The animation is never the grade.

Gate 2 (complexity) is the *spine*: we fit the solution's complexity class from
a modest-n sweep and fail it if that class is worse than the level's target —
i.e. it would brown out at scale. This also guarantees a degenerate/lucky
solution can never "win", because a wrong complexity class cannot pass.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, List, Tuple

from .complexity import fit_class, worse_than
from .errors import DerefOpLimit
from .tracer import run_traced

# n's used for the correctness spot-check and the complexity sweep.
CORRECTNESS_NS = (10, 25)
SWEEP_NS = (50, 100, 200, 400, 800)
# The sweep runs each size under several worst-case seeds and takes the max op
# count, so a solution cannot special-case a single predictable sweep input.
WORSTCASE_SEEDS = (1, 2)
DEMO_N = 8


@dataclass
class Level:
    id: str
    pattern: str
    title: str
    prompt: str
    func_name: str
    reference_solution: str
    target_class: str
    bound_names: Tuple[str, ...]
    input_names: Tuple[str, ...]
    # make_instance(n, seed) -> args with a (unique) solution; for correctness + demo.
    make_instance: Callable[[int, int], tuple]
    # make_worstcase(n, seed) -> args that force full traversal; for the complexity
    # sweep, so op-count reflects true asymptotics, not where the answer happens to sit.
    make_worstcase: Callable[[int, int], tuple] = None
    # Explicit edge cases as args tuples; expected output comes from the reference.
    edge_cases: List[tuple] = field(default_factory=list)


@dataclass
class Verdict:
    solved: bool
    correctness_pass: bool
    complexity_pass: bool
    fitted_class: str
    target_class: str
    failing_case: Any = None
    predicted_brownout_n: Any = None
    curve: List[Tuple[int, int]] = field(default_factory=list)
    space_hi: int = 0
    messages: List[str] = field(default_factory=list)


def _equal(a, b):
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return list(a) == list(b)
    return a == b


def _short(args):
    out = []
    for a in args:
        if isinstance(a, (list, tuple)) and len(a) > 8:
            out.append(list(a[:8]) + ["...(%d)" % len(a)])
        else:
            out.append(a)
    return out


def verify(level, source):
    """Grade ``source`` against ``level``. Returns ``(Verdict, demo_frames)``."""
    messages = []

    # ---- Gate 1: correctness (expected derived from the reference solution) ----
    case_args = list(level.edge_cases)
    for n in CORRECTNESS_NS:
        case_args.append(level.make_instance(n, n))

    correctness_pass = True
    failing = None
    for args in case_args:
        try:
            expected = run_traced(
                level.reference_solution, level.func_name, args,
                input_names=level.input_names,
            ).result
            got = run_traced(
                source, level.func_name, args, input_names=level.input_names,
            ).result
        except DerefOpLimit:
            correctness_pass = False
            failing = {"args": _short(args), "error": "ran away (hit op limit)"}
            break
        except Exception as exc:  # noqa: BLE001 - surface any user-code error as a failing case
            correctness_pass = False
            failing = {"args": _short(args), "error": repr(exc)}
            break
        if not _equal(got, expected):
            correctness_pass = False
            failing = {"args": _short(args), "expected": expected, "got": got}
            break

    # ---- Gate 2: complexity sweep + class fit (on worst-case inputs) ----
    # Each size is run under several worst-case seeds; we take the max op count
    # so a solution can't cheaply detect and short-circuit a fixed sweep input.
    worst = level.make_worstcase or level.make_instance
    curve = []
    ran_away = False
    crashed = None
    for n in SWEEP_NS:
        ops_at_n = []
        for seed in WORSTCASE_SEEDS:
            try:
                r = run_traced(source, level.func_name, worst(n, seed), input_names=level.input_names)
                ops_at_n.append(r.ops)
            except DerefOpLimit as exc:
                ran_away = True
                ops_at_n.append(exc.ops)
            except Exception as exc:  # noqa: BLE001 - a raising solution fails, never crashes the grader
                crashed = repr(exc)
                break
        if ops_at_n:
            curve.append((n, max(ops_at_n)))
        if ran_away or crashed:
            break

    if crashed:
        fitted, complexity_pass = "crash", False
        messages.append("Solution raised an exception during the complexity sweep: %s" % crashed)
    elif ran_away:
        fitted, complexity_pass = "O(n^2)+", False
    else:
        fitted, _scores = fit_class(curve)
        complexity_pass = not worse_than(fitted, level.target_class)

    predicted_brownout_n = None
    if not complexity_pass and not crashed:
        predicted_brownout_n = 100_000
        messages.append(
            "Fitted %s is worse than target %s — this BROWNS OUT at scale (n=%s)."
            % (fitted, level.target_class, predicted_brownout_n)
        )

    # ---- Demo run (small n): frames + space for the animation ----
    # A broken/runaway solution simply yields no frames; it must not crash grading.
    demo_frames = []
    demo_space = 0
    try:
        demo = run_traced(
            source, level.func_name, level.make_instance(DEMO_N, 1),
            bound_names=level.bound_names, input_names=level.input_names,
            capture_frames=True,
        )
        demo_frames = demo.frames
        demo_space = demo.space_hi
    except Exception:  # noqa: BLE001 - demo animation is best-effort, never the grade
        pass

    solved = correctness_pass and complexity_pass
    verdict = Verdict(
        solved=solved,
        correctness_pass=correctness_pass,
        complexity_pass=complexity_pass,
        fitted_class=fitted,
        target_class=level.target_class,
        failing_case=failing,
        predicted_brownout_n=predicted_brownout_n,
        curve=curve,
        space_hi=demo_space,
        messages=messages,
    )
    return verdict, demo_frames
