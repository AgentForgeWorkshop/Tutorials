#!/usr/bin/env python3
"""Exact arithmetic for the calculator skill. Standard library only.

    python scripts/calc.py "412/487*100"
    python scripts/calc.py "1*F/(3.6*157.76)" --sig 4

The MCP server imports calculate() from this file, so the same code runs whether the skill
is used through MCP or on its own. Only numbers, arithmetic and the functions and constants
below are accepted, so nothing else can be run through it.
"""
import argparse
import ast
import math
import operator
import sys

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
       ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow,
       ast.USub: operator.neg, ast.UAdd: operator.pos}
FUNCS = {"sqrt": math.sqrt, "log": math.log, "log10": math.log10, "exp": math.exp, "abs": abs,
         "sin": math.sin, "cos": math.cos, "tan": math.tan, "round": round, "min": min, "max": max}
CONSTS = {"pi": math.pi, "e": math.e,
          "F": 96485.33212,        # Faraday constant, C/mol
          "R": 8.314462618,        # gas constant, J/(mol K)
          "NA": 6.02214076e23}     # Avogadro constant, 1/mol
MAX_EXPRESSION_LENGTH = 500
MAX_INTEGER_BITS = 4096


def _check_size(value):
    if isinstance(value, int) and value.bit_length() > MAX_INTEGER_BITS:
        raise ValueError("result is too large")
    return value


def _evaluate(node):
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        left, right = _evaluate(node.left), _evaluate(node.right)
        if isinstance(node.op, ast.Pow):
            if abs(right) > 1000:
                raise ValueError("exponent is too large")
            if isinstance(left, int) and isinstance(right, int) and left.bit_length() * abs(right) > MAX_INTEGER_BITS:
                raise ValueError("result is too large")
        return _check_size(OPS[type(node.op)](left, right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
        return OPS[type(node.op)](_evaluate(node.operand))
    if isinstance(node, ast.Name) and node.id in CONSTS:
        return CONSTS[node.id]
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in FUNCS and not node.keywords):
        return FUNCS[node.func.id](*[_evaluate(arg) for arg in node.args])
    raise ValueError(f"not allowed in an expression: {ast.unparse(node)}")


def _format(value, sig: int) -> str:
    if isinstance(value, complex):
        raise ValueError("the result is not a real number")
    if isinstance(value, int):
        return str(value) if abs(value) < 10**15 else f"{value:.{sig}e}"
    if value.is_integer() and abs(value) < 1e15:
        return str(int(value))
    return f"{value:.{sig}g}"


def calculate(expression: str, sig: int = 6) -> str:
    """Return 'expression = result'. Raises ValueError with a readable reason."""
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise ValueError("expression is too long")
    cleaned = expression.replace("×", "*").replace("−", "-").replace("^", "**")
    try:
        value = _evaluate(ast.parse(cleaned, mode="eval"))
        return f"{expression} = {_format(value, sig)}"
    except ZeroDivisionError:
        raise ValueError("division by zero") from None
    except (SyntaxError, TypeError, OverflowError, RecursionError, MemoryError) as err:
        raise ValueError(f"could not evaluate this expression ({type(err).__name__})") from None


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate one arithmetic expression exactly.")
    parser.add_argument("expression", help='for example "412/487*100"')
    parser.add_argument("--sig", type=int, default=6, help="significant figures in the result (default 6)")
    args = parser.parse_args()
    try:
        print(calculate(args.expression, args.sig))
    except ValueError as err:
        print(f"ERROR: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
