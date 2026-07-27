"""Engine exceptions."""


class DerefError(Exception):
    """Base class for all engine errors."""


class DerefOpLimit(DerefError):
    """Raised when a run exceeds the hard op cap (runaway loop / no brown-out gate).

    This is a safety backstop so a user solution that never terminates (e.g. a
    two-pointer loop that forgets to move a pointer) cannot hang the engine.
    """

    def __init__(self, ops):
        super().__init__("op limit exceeded at %d ops" % ops)
        self.ops = ops
