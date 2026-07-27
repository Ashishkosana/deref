"""The frame protocol: the seam between the Python engine and any client.

A run of a user's solution is compiled down to a list of `Frame`s plus a
summary. The client (Flutter today, a JS canvas earlier, whatever next) is a
dumb player of these frames: it holds zero algorithm logic.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Frame:
    """One observable step of a solution's execution.

    tick     cumulative primitive-op count when this line was reached
             (this is what drains the power/step meter)
    line     1-based source line, for editor highlighting
    vars     snapshot of the bound (visualised) variables at this line
    space_hi peak auxiliary space seen so far (fills the space gauge)
    """

    tick: int
    line: int
    vars: Dict[str, Any]
    space_hi: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tick": self.tick,
            "line": self.line,
            "vars": self.vars,
            "space_hi": self.space_hi,
        }


@dataclass
class RunResult:
    """Everything a single traced execution produced."""

    result: Any
    ops: int
    space_hi: int
    frames: List[Frame] = field(default_factory=list)
