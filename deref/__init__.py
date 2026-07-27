"""DEREF engine — a Python execution tracer that turns real solutions into
replayable, complexity-annotated animation frames.

Public API:
    run_traced(source, func_name, args, ...) -> RunResult
    verify(level, source)                    -> (Verdict, frames)
"""

__version__ = "0.1.0"

from .frames import Frame, RunResult
from .level import Level, Verdict, verify
from .tracer import run_traced

__all__ = ["Frame", "RunResult", "Level", "Verdict", "verify", "run_traced", "__version__"]
