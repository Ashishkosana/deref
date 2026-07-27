"""The tracer: run a user's Python solution and observe it two ways.

1. Op counting via AST instrumentation. We rewrite the source so counted
   expressions (subscript/slice reads, arithmetic, sequence concat/repeat,
   comparisons, membership, receiver-method calls, augmented assignments) route
   through charging helpers that return their value unchanged. Wrapping happens
   *in place* at the expression level, so source line numbers are preserved.
   The transform also bans dunder attribute access, which closes the common
   introspection sandbox escape (e.g. ``().__class__.__subclasses__()``).

2. Frame capture + space measurement via ``sys.settrace``. On each line event
   inside the user function we snapshot the bound variables and peak auxiliary
   space. Tracing is slow, so it is only enabled for the small-n "demo" run.
"""

import ast
import copy
import sys

from .costmodel import SAFE_BUILTINS, make_helpers
from .errors import DerefError
from .frames import Frame, RunResult

# Injected helper global names.
TICK = "__deref_tick__"
CONTAINS = "__deref_contains__"
SIZED = "__deref_sized__"
BINOP = "__deref_binop__"
AUGCHARGE = "__deref_augcharge__"
METHOD = "__deref_method__"

DEFAULT_HARD_CAP = 3_000_000
_SNAPSHOT_CAP = 64  # max elements copied into a frame's variable snapshot


def _call(name, args, loc):
    node = ast.Call(func=ast.Name(id=name, ctx=ast.Load()), args=args, keywords=[])
    return ast.copy_location(node, loc)


def _wrap(node, kind, n):
    return _call(TICK, [node, ast.Constant(kind), ast.Constant(n)], node)


def _as_load(target):
    """A read-only (ctx=Load) copy of an assignment target."""
    node = copy.deepcopy(target)
    node.ctx = ast.Load()
    return node


class OpInstrumenter(ast.NodeTransformer):
    """Wrap counted expressions in charging helpers, preserving line numbers."""

    def visit_Attribute(self, node):
        self.generic_visit(node)
        if node.attr.startswith("__") and node.attr.endswith("__"):
            raise DerefError("access to dunder attribute %r is not allowed" % node.attr)
        return node

    def visit_Subscript(self, node):
        self.generic_visit(node)
        if isinstance(node.ctx, ast.Load):
            if isinstance(node.slice, ast.Slice):
                return _call(SIZED, [node], node)  # slice copy costs O(len)
            return _wrap(node, "index", 1)
        return node

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.Add):
            return _call(BINOP, [ast.Constant("add"), node.left, node.right], node)
        if isinstance(node.op, ast.Mult):
            return _call(BINOP, [ast.Constant("mult"), node.left, node.right], node)
        return _wrap(node, "arith", 1)

    def visit_Compare(self, node):
        self.generic_visit(node)
        if len(node.ops) == 1 and isinstance(node.ops[0], (ast.In, ast.NotIn)):
            negate = isinstance(node.ops[0], ast.NotIn)
            return _call(CONTAINS, [node.left, node.comparators[0], ast.Constant(negate)], node)
        return _wrap(node, "compare", len(node.ops))

    def visit_Call(self, node):
        self.generic_visit(node)
        # Receiver-method calls (recv.meth(args)) are size-costed at runtime.
        # (Dunder method names are already rejected by visit_Attribute.)
        if isinstance(node.func, ast.Attribute):
            new = ast.Call(
                func=ast.Name(id=METHOD, ctx=ast.Load()),
                args=[ast.Constant(node.func.attr), node.func.value] + node.args,
                keywords=node.keywords,
            )
            return ast.copy_location(new, node)
        return node

    def visit_AugAssign(self, node):
        self.generic_visit(node)
        # x += y / x *= y: charge by the receiver's current size, keep in-place
        # semantics and line numbers by only rewriting the value expression.
        if isinstance(node.op, (ast.Add, ast.Mult)):
            kind = "add" if isinstance(node.op, ast.Add) else "mult"
            load_target = _as_load(node.target)
            node.value = _call(AUGCHARGE, [ast.Constant(kind), load_target, node.value], node)
        return node


def _instrument(source):
    tree = ast.parse(source)
    OpInstrumenter().visit(tree)
    ast.fix_missing_locations(tree)
    return tree


def _safe_snapshot(value):
    """Copy containers (so later mutation doesn't alias frames) and cap size."""
    if isinstance(value, (list, tuple)):
        return list(value[:_SNAPSHOT_CAP])
    if isinstance(value, dict):
        return dict(list(value.items())[:_SNAPSHOT_CAP])
    if isinstance(value, (set, frozenset)):
        return sorted(list(value))[:_SNAPSHOT_CAP]
    return value


def run_traced(
    source,
    func_name,
    args,
    bound_names=(),
    input_names=(),
    capture_frames=False,
    max_frames=4000,
    hard_cap=DEFAULT_HARD_CAP,
):
    """Compile + run ``source``'s ``func_name`` on ``args``; return a RunResult.

    Op counting is always on. Frame capture + space measurement (via settrace)
    are on only when ``capture_frames`` is True. Raises DerefError if the source
    uses a banned construct, DerefOpLimit if it runs away, or the user code's
    own exception otherwise.
    """
    counter = {"ops": 0}
    helpers, charged_builtins = make_helpers(counter, hard_cap)

    sandbox_builtins = dict(SAFE_BUILTINS)
    sandbox_builtins.update(charged_builtins)
    g = {
        "__builtins__": sandbox_builtins,
        TICK: helpers["tick"], CONTAINS: helpers["contains"], SIZED: helpers["sized"],
        BINOP: helpers["binop"], AUGCHARGE: helpers["augcharge"], METHOD: helpers["method"],
    }

    code = compile(_instrument(source), "<deref-user>", "exec")
    exec(code, g)  # noqa: S102 - restricted namespace; user code by design
    if func_name not in g or not callable(g[func_name]):
        raise DerefError("no callable named %r was defined" % func_name)
    func = g[func_name]

    frames = []
    space_hi = {"v": 0}
    input_set = set(input_names)

    def _aux_space(local_vars):
        total = 0
        for name, val in local_vars.items():
            if name in input_set:
                continue
            if isinstance(val, (list, dict, set, frozenset)):
                total += len(val)
        return total

    def _tracer(frame, event, arg):
        if frame.f_code.co_name != func_name:
            return _tracer
        if event == "line":
            local_vars = frame.f_locals
            sp = _aux_space(local_vars)
            if sp > space_hi["v"]:
                space_hi["v"] = sp
            if capture_frames and len(frames) < max_frames:
                snap = {}
                for name in bound_names:
                    if name in local_vars:
                        snap[name] = _safe_snapshot(local_vars[name])
                frames.append(
                    Frame(tick=counter["ops"], line=frame.f_lineno, vars=snap, space_hi=space_hi["v"])
                )
        return _tracer

    if capture_frames:
        sys.settrace(_tracer)
        try:
            result = func(*args)
        finally:
            sys.settrace(None)
    else:
        result = func(*args)

    return RunResult(result=result, ops=counter["ops"], space_hi=space_hi["v"], frames=frames)
