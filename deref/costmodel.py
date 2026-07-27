"""The cost model — published on purpose so the engine never teaches lies.

We count *primitive operations*, not source lines (line-counting undercounts
hidden library work like ``x in some_list`` or ``sum(xs)``). Constants are
ignored when we classify complexity, but shown to the player for intuition.

    subscript read  nums[i]        -> 1
    slice read      nums[a:b]      -> len(result)          (a copy costs O(k))
    arithmetic      a + b          -> 1   (numeric BinOp)
    seq concat      xs + ys        -> len(xs) + len(ys)    (list/str/tuple/bytes)
    seq repeat      xs * k         -> len(xs) * k
    augmented       xs += ys       -> len(xs) (+ len(ys))  (concat/ repeat)
    comparison      a < b          -> 1   (per comparator)
    membership      x in c         -> 1 if c is set/dict/range, else len(c)
    sorted / .sort                 -> n * log2(n)
    sum/min/max over an iterable   -> len
    .count/.index/.remove/.find    -> len(receiver)  (linear scan)
    .extend(ys) / str.join(ys)     -> total len added
    .insert(i,x) / .pop(i)         -> len(receiver) - i  (shift cost)
    len(x), .append, dict ops      -> 1   (amortized O(1))

Space is measured separately (see tracer): the peak total size of the
containers the solution itself creates, excluding the input.
"""

import math

from .errors import DerefOpLimit

# Receiver methods whose real cost is a linear scan of the receiver.
_LINEAR_METHODS = {
    "count", "index", "remove", "find", "rfind", "reverse", "copy",
    "split", "rsplit", "replace",
}


def make_helpers(counter, hard_cap):
    """Build the runtime helpers injected into instrumented user code.

    Every helper charges the cost model and returns the underlying value so
    instrumentation stays transparent to the algorithm's semantics.
    """

    def charge(k):
        counter["ops"] += k
        if counter["ops"] > hard_cap:
            raise DerefOpLimit(counter["ops"])

    def _seqlen(v):
        try:
            return len(v)
        except TypeError:
            return 1

    def tick(value, kind, n=1):
        charge(n)
        return value

    def contains(x, container, negate=False):
        # set/dict/frozenset are O(1); range membership is O(1) in Python 3.
        if isinstance(container, (set, dict, frozenset, range)):
            charge(1)
        else:
            charge(_seqlen(container))
        result = x in container
        return (not result) if negate else result

    def sized(value):
        # A slice read produced this sequence; the copy cost is its length.
        charge(max(1, _seqlen(value)))
        return value

    def binop(kind, left, right):
        if kind == "add":
            if isinstance(left, (str, list, tuple, bytes)) and isinstance(right, (str, list, tuple, bytes)):
                charge(_seqlen(left) + _seqlen(right))
            else:
                charge(1)
            return left + right
        # kind == "mult" (sequence repeat is O(len * count))
        if isinstance(left, (str, list, tuple, bytes)) and isinstance(right, int):
            charge(max(1, _seqlen(left) * max(right, 0)))
        elif isinstance(right, (str, list, tuple, bytes)) and isinstance(left, int):
            charge(max(1, _seqlen(right) * max(left, 0)))
        else:
            charge(1)
        return left * right

    def augcharge(kind, current, value):
        # Charges an augmented op (x += / x *=) by the receiver's current size,
        # then returns `value` unchanged so the real in-place op is preserved.
        if kind == "add":
            if isinstance(current, (str, list, tuple, bytes)):
                extra = _seqlen(value) if isinstance(value, (str, list, tuple, bytes)) else 0
                charge(_seqlen(current) + extra)
            else:
                charge(1)
        else:  # mult
            if isinstance(current, (str, list, tuple, bytes)) and isinstance(value, int):
                charge(max(1, _seqlen(current) * max(value, 0)))
            else:
                charge(1)
        return value

    def method(name, recv, *args, **kwargs):
        rlen = _seqlen(recv)
        if name == "sort":
            charge(int(rlen * math.log2(rlen)) if rlen > 1 else 1)
        elif name == "join":
            items = list(args[0]) if args else []
            charge(sum(_seqlen(x) for x in items) + len(items) + 1)
            return recv.join(items)
        elif name == "extend":
            charge(_seqlen(args[0]) if args else 1)
        elif name == "insert":
            idx = args[0] if args and isinstance(args[0], int) else 0
            charge(max(1, rlen - (idx if idx >= 0 else 0)))
        elif name == "pop" and args and isinstance(args[0], int):
            idx = args[0]
            charge(max(1, rlen - (idx if idx >= 0 else rlen)))
        elif name in _LINEAR_METHODS:
            charge(max(1, rlen))
        else:
            charge(1)
        return getattr(recv, name)(*args, **kwargs)

    def charged_sorted(iterable, key=None, reverse=False):
        seq = list(iterable)
        n = len(seq)
        charge(int(n * math.log2(n)) if n > 1 else 1)
        return sorted(seq, key=key, reverse=reverse)

    def charged_sum(iterable, start=0):
        seq = list(iterable)
        charge(len(seq))
        return sum(seq, start)

    def charged_min(*args, **kwargs):
        if len(args) == 1:
            seq = list(args[0])
            charge(len(seq))
            return min(seq, **kwargs)
        charge(len(args))
        return min(*args, **kwargs)

    def charged_max(*args, **kwargs):
        if len(args) == 1:
            seq = list(args[0])
            charge(len(seq))
            return max(seq, **kwargs)
        charge(len(args))
        return max(*args, **kwargs)

    helpers = {
        "tick": tick, "contains": contains, "sized": sized,
        "binop": binop, "augcharge": augcharge, "method": method,
    }
    charged_builtins = {
        "sorted": charged_sorted, "sum": charged_sum,
        "min": charged_min, "max": charged_max,
    }
    return helpers, charged_builtins


# The restricted sandbox: only these names are visible to user code. This is
# both a teaching constraint and a LIGHT security boundary (no open/import/eval/
# getattr). Combined with the AST-level dunder-attribute ban in tracer.py it
# blocks the common introspection escapes; a hardened process sandbox
# (subprocess + rlimits) is still required before this runs untrusted code
# server-side.
SAFE_BUILTINS = {
    "len": len, "range": range, "enumerate": enumerate, "abs": abs,
    "list": list, "dict": dict, "set": set, "tuple": tuple, "frozenset": frozenset,
    "str": str, "int": int, "float": float, "bool": bool, "bytes": bytes,
    "zip": zip, "reversed": reversed, "map": map, "filter": filter,
    "all": all, "any": any, "round": round, "divmod": divmod, "pow": pow,
    "ord": ord, "chr": chr,
    "True": True, "False": False, "None": None,
    # Exception classes so idiomatic try/except (EAFP) solutions run. These
    # carry no filesystem/network capability.
    "Exception": Exception, "ValueError": ValueError, "KeyError": KeyError,
    "IndexError": IndexError, "TypeError": TypeError, "StopIteration": StopIteration,
    "ZeroDivisionError": ZeroDivisionError, "ArithmeticError": ArithmeticError,
    "LookupError": LookupError, "RuntimeError": RuntimeError, "OverflowError": OverflowError,
    "AttributeError": AttributeError, "NameError": NameError, "AssertionError": AssertionError,
    "RecursionError": RecursionError,
}
