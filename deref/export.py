"""Export a level's demo run to the client-facing frame JSON.

    python -m deref.export [reference|brute|hashing] [out.json]

The output is the entire "movie" the client plays back: the input, the graded
verdict (with the n-vs-ops curve), the per-line frames, and the source so the
client can highlight the active line. Playback needs no engine at all.
"""

import json
import sys

from .level import verify
from .levels.rendezvous import BRUTE, HASHING, LEVEL, REFERENCE
from .tracer import run_traced

# The walkthrough board, so the demo matches THE RENDEZVOUS beat-for-beat.
CANONICAL_INPUT = ([2, 3, 5, 8, 11, 15, 19, 24], 17)

_SOLUTIONS = {"reference": REFERENCE, "brute": BRUTE, "hashing": HASHING}


def export_demo(label="reference", input_args=CANONICAL_INPUT):
    source = _SOLUTIONS[label]
    nums, target = input_args

    run = run_traced(
        source, LEVEL.func_name, input_args,
        bound_names=LEVEL.bound_names, input_names=LEVEL.input_names,
        capture_frames=True,
    )
    verdict, _ = verify(LEVEL, source)

    return {
        "id": LEVEL.id,
        "title": LEVEL.title,
        "pattern": LEVEL.pattern,
        "prompt": LEVEL.prompt,
        "targetClass": LEVEL.target_class,
        "solution": label,
        "input": {"nums": list(nums), "target": target},
        "result": run.result,
        "verdict": {
            "solved": verdict.solved,
            "correctnessPass": verdict.correctness_pass,
            "complexityPass": verdict.complexity_pass,
            "fittedClass": verdict.fitted_class,
            "spaceHi": verdict.space_hi,
            "curve": [[n, ops] for n, ops in verdict.curve],
            "messages": verdict.messages,
        },
        # Kept unstripped so frame.line (1-based into the traced source) maps
        # directly onto the client's line array for highlighting.
        "source": source,
        "frames": [f.to_dict() for f in run.frames],
    }


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    label = argv[0] if argv else "reference"
    out = argv[1] if len(argv) > 1 else "frames/rendezvous.json"

    data = export_demo(label)
    with open(out, "w") as fh:
        json.dump(data, fh, indent=2)
    print("wrote %s  (%s, %d frames, verdict=%s %s)" % (
        out, label, len(data["frames"]),
        "SOLVED" if data["verdict"]["solved"] else "NOT SOLVED",
        data["verdict"]["fittedClass"],
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
