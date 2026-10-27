"""Deterministic tool interfaces (RUNTIME_LOCK §3). Stdlib only."""
from __future__ import annotations

import ast
import operator as op
from typing import Callable, Dict, Tuple


class ToolError(Exception):
    pass


_BIN_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
}
_UNARY = {ast.UAdd: op.pos, ast.USub: op.neg}
_SAFE_FUNCS: Dict[str, Callable] = {"abs": abs, "min": min, "max": max, "round": round}


def _eval_node(node: ast.AST):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Pow) and (abs(right) > 10 or abs(left) > 1e6):
            raise ToolError("pow overflow guard")
        return _BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_eval_node(node.operand))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        fn = _SAFE_FUNCS.get(node.func.id)
        if fn is None:
            raise ToolError(f"function not allowed: {node.func.id}")
        args = [_eval_node(a) for a in node.args]
        return fn(*args)
    raise ToolError(f"expression not allowed: {type(node).__name__}")


def tool_calc(expr: str) -> str:
    try:
        tree = ast.parse(expr.strip(), mode="eval")
        val = _eval_node(tree)
        if isinstance(val, float) and val.is_integer():
            val = int(val)
        return str(val)
    except ToolError:
        raise
    except Exception as e:  # noqa: BLE001 - classified as tool_error
        raise ToolError(f"calc failed: {e}") from e


def tool_str_ops(command: str) -> str:
    parts = command.strip().split("|")
    if not parts:
        raise ToolError("empty str_ops command")
    opname = parts[0].strip().lower()
    arg = parts[1] if len(parts) > 1 else ""
    try:
        if opname == "lower":
            return arg.lower()
        if opname == "upper":
            return arg.upper()
        if opname == "strip":
            return arg.strip()
        if opname == "reverse":
            return arg[::-1]
        if opname == "lstrip":
            return arg.lstrip()
        if opname == "rstrip":
            return arg.rstrip()
        if opname == "split":
            sep = parts[2] if len(parts) > 2 else " "
            return repr(arg.split(sep))
        if opname == "join":
            sep = parts[2] if len(parts) > 2 else ""
            return sep.join(list(arg))
        if opname == "replace":
            if len(parts) < 4:
                raise ToolError("replace needs old|new")
            return arg.replace(parts[2], parts[3])
        if len(parts) == 1:
            # identity passthrough for payloads that are not command strings
            return command
    except ToolError:
        raise
    except Exception as e:  # noqa: BLE001
        raise ToolError(f"str_ops failed: {e}") from e
    raise ToolError(f"unknown str_ops command: {opname}")


_ALLOWED_AST = (
    ast.Module, ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name, ast.Call,
    ast.Compare, ast.IfExp, ast.BoolOp, ast.List, ast.Tuple,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.UAdd, ast.USub, ast.Load, ast.Store,
    ast.If, ast.For, ast.Assign, ast.AugAssign, ast.Expr, ast.Break, ast.Continue,
    ast.Pass, ast.Return, ast.arguments, ast.arg, ast.keyword,
)


def tool_py_sandbox(code: str) -> str:
    """Extremely restricted execution: arithmetic/str assignments, if/else, for range(n<=100)."""
    try:
        tree = ast.parse(code.strip(), mode="exec")
    except SyntaxError as e:
        raise ToolError(f"syntax error: {e}") from e
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_AST):
            raise ToolError(f"node not allowed: {type(node).__name__}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _SAFE_FUNCS | {"range"}:
                raise ToolError("call not allowed")
            if node.func.id == "range" and (not node.args or not isinstance(node.args[0], ast.Constant)):
                raise ToolError("range must have constant bound")
            if node.func.id == "range":
                bound = node.args[0].value
                if not isinstance(bound, int) or bound > 100:
                    raise ToolError("range bound must be int <= 100")
        if isinstance(node, ast.Name) and node.id in ("eval", "exec", "open", "__import__"):
            raise ToolError("name not allowed")
    env: dict = {"range": range, **_SAFE_FUNCS}
    try:
        exec(compile(tree, "<sandbox>", "exec"), {"__builtins__": {}}, env)  # noqa: S102
    except Exception as e:  # noqa: BLE001
        raise ToolError(f"py_sandbox failed: {e}") from e
    out = env.get("result", env.get("out"))
    return str(out) if out is not None else "ok"


TOOL_REGISTRY: Dict[str, Callable[[str], str]] = {
    "calc": tool_calc,
    "str_ops": tool_str_ops,
    "py_sandbox": tool_py_sandbox,
}


def run_tool(name: str, payload: str) -> Tuple[bool, str]:
    fn = TOOL_REGISTRY.get(name)
    if fn is None:
        return False, f"unknown tool {name}"
    try:
        return True, fn(payload)
    except ToolError as e:
        return False, str(e)[:200]
