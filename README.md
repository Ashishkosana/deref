# DEREF

**A Python execution tracer that turns real DSA solutions into replayable, complexity-annotated animation frames — the engine behind a Zachtronics-style game for learning coding-interview algorithms.**

You don't arrange cards or drag blocks. You write the actual Python you'd write in an interview. The engine instruments and runs it, then hands a client a list of *frames* — a movie of your algorithm walking a data structure, with a power meter that **browns out if your solution is too slow**. The point isn't to be told your approach is O(n²); it's to *watch* it run out of power and freeze, red, halfway across the array.

This repo is the **engine** (pure Python, standard library only). A separate Flutter client plays the frames back.

---

## Why it's built this way

```
  user's real Python  ──▶  DEREF engine (this repo)  ──▶  JSON frames + verdict  ──▶  client
     (a solution)          AST-instrument · run ·           (a replayable movie)      (Flutter:
                           count ops · fit complexity ·                                 plays frames,
                           measure space · grade                                        holds zero logic)
```

The **frame protocol** is the seam. All the interesting, teachable, testable work lives in this Python package; the client is a dumb player. That means:

- The engine is unit-tested in CPython in CI — correctness never depends on the client.
- It can run **as an AWS Lambda** (author-and-run-your-code), **on-device** (offline), or from a CLI, unchanged.
- **Playback needs no engine at all** — a client can replay pre-baked frame JSON offline. The engine is only needed to run *your own* new code.

## What the engine does

1. **Instruments** the user's source with an AST transform, wrapping counted expressions (subscript reads, arithmetic, comparisons, membership) in a charging helper — *in place*, so source line numbers survive.
2. **Runs** it in a restricted namespace, counting primitive ops against a published cost model.
3. **Captures frames** (variable snapshots + peak space, per line) via `sys.settrace` — only at small n, for the animation.
4. **Grades** with two gates.

### The two gates

- **Gate 1 — Correctness (the grade).** The solution must match the reference solution on edge cases + generated instances. The animation is *never* the grade.
- **Gate 2 — Complexity (the spine).** We fit the solution's complexity class from a **worst-case** sweep (n ≤ 800) and fail it if the class is worse than the level's target — i.e. it would brown out at scale. This also makes a lucky/degenerate solution un-winnable: a wrong complexity class cannot pass.

Complexity is measured on **worst-case** inputs on purpose (no early return) so op-count reflects true asymptotics — exactly what interviews care about — and huge n is *extrapolated from the fitted class*, never executed.

### The cost model (published, so it can't teach lies)

| Operation | Charge |
|---|---|
| subscript read `nums[i]` | 1 |
| arithmetic `a + b` | 1 per `BinOp` |
| comparison `a < b` | 1 per comparator |
| membership `x in c` | 1 if `c` is set/dict, else `len(c)` |
| `sorted(x)` | n·log₂n |
| `sum` / `min` / `max` over an iterable | `len` |
| `len(x)` | 1 |

Constants are ignored when classifying the class, shown to the player for intuition. Space is measured separately: the peak total size of containers the solution creates, excluding the input.

## Run it

```bash
# no dependencies — standard library only, Python 3.9+
python3 -m deref.run reference   # the intended two-pointer answer  -> SOLVED, O(n)
python3 -m deref.run brute       # correct but O(n^2)               -> BROWN-OUT
python3 -m deref.run hashing     # O(n) time, but the space gauge catches its O(n) memory
python3 -m deref.run path/to/your_solution.py

python3 tests/test_engine.py     # 17 tests, no pytest required (also runs under pytest)
```

Example — the engine reading three solutions to *Two Sum II* straight from source:

| Solution | ops at n = 50 → 800 | fitted | verdict | aux space |
|---|---|---|---|---|
| two-pointer | 296 → 596 → 1196 → 2396 → 4796 | O(n) | ✅ SOLVED | 0 |
| brute force | 4950 → 19900 → 79800 → 319600 → 1279200 | O(n²) | ⚠️ BROWN-OUT | 0 |
| hashing | 200 → 400 → 800 → 1600 → 3200 | O(n) | ✅ SOLVED | grows with n |

## Layout

```
deref/
  tracer.py       AST instrumentation + settrace runner  (run_traced -> RunResult)
  costmodel.py    op charges + charged builtins + restricted sandbox
  complexity.py   fit (n, ops) points to a complexity class
  frames.py       the frame protocol (Frame, RunResult)
  level.py        Level (data) + the two-gate verifier
  levels/
    rendezvous.py THE RENDEZVOUS — the two-pointer level + 3 reference solutions
  run.py          CLI
tests/
  test_engine.py  proves the engine tells O(n) / O(n log n) / O(n^2) apart
```

## Roadmap

- **Now (done):** engine — tracer, cost model, complexity fit, two-gate verifier, one level. Hardened after an adversarial review (14 findings fixed: slice/method/concat cost gaps that let quadratic solutions pass, additive-constant blindness in the fit, grader crash-hardening, EAFP exception support, and an AST-level ban on dunder-attribute escapes).
- **Next:** frame-JSON export + a Flutter client (`CustomPainter`) that plays the demo frames — the "watch your algorithm walk" hook, on a phone.
- **Then:** a serverless Python tracer endpoint (AWS Lambda + API Gateway) for author-and-run-your-code; spaced-repetition scheduler; more patterns (hashing, then the graph frontier-swap BFS/DFS level).
- **Before public Lambda:** harden the sandbox (the current restricted-builtins boundary is a light MVP boundary, not a hardened one).

## Honest positioning

DEREF is a **learning tool that demos well** and a clean **backend/systems + first-Flutter** portfolio artifact. It is not a React/TypeScript credential. The go/no-go test is transfer: after playing the two-pointer level, can you cold-write Two Sum II in a blank editor and state its complexity? If not, the mechanic doesn't transfer and no extra levels fix it.
