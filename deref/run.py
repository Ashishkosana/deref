"""CLI: grade a solution against THE RENDEZVOUS and print the verdict + frames.

    python -m deref.run reference     # the intended two-pointer answer
    python -m deref.run brute         # correct but O(n^2) -> browns out
    python -m deref.run hashing       # O(n) but costs space
    python -m deref.run path/to/solution.py
"""

import sys

from .level import verify
from .levels.rendezvous import BRUTE, HASHING, LEVEL, REFERENCE

_BUILTIN = {"reference": REFERENCE, "brute": BRUTE, "hashing": HASHING}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    which = argv[0] if argv else "reference"

    if which in _BUILTIN:
        source = _BUILTIN[which]
        label = which
    else:
        with open(which) as fh:
            source = fh.read()
        label = which

    verdict, frames = verify(LEVEL, source)

    print("LEVEL   : %s  (target %s)" % (LEVEL.title, LEVEL.target_class))
    print("SOLUTION: %s" % label)
    print("-" * 56)
    print("correctness : %s %s" % (
        "PASS" if verdict.correctness_pass else "FAIL",
        "" if verdict.correctness_pass else verdict.failing_case,
    ))
    print("complexity  : %s  ->  %s" % (
        verdict.fitted_class,
        "PASS" if verdict.complexity_pass else "BROWN-OUT",
    ))
    print("curve (n,ops): %s" % verdict.curve)
    print("aux space @n=%d: %d" % (8, verdict.space_hi))
    for msg in verdict.messages:
        print("  ! %s" % msg)
    print("-" * 56)
    print(">>> %s" % ("SOLVED" if verdict.solved else "NOT SOLVED"))
    print("frames captured @n=8: %d" % len(frames))
    if frames:
        print("  first: %s" % frames[0].to_dict())
        print("  last : %s" % frames[-1].to_dict())

    return 0 if verdict.solved else 1


if __name__ == "__main__":
    raise SystemExit(main())
