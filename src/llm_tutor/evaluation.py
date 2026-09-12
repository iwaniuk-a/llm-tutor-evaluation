"""Deterministic answer evaluation and benchmark-input validation."""

from __future__ import annotations

import re
from collections import Counter
from fractions import Fraction
from math import isclose
from typing import Any, Iterable

try:
    import sympy
except ImportError:  # pragma: no cover - exercised only in minimal installs
    sympy = None


_RESULT_PATTERN = re.compile(r"\[\[(.*?)\]\]", flags=re.DOTALL)
_NO_SOLUTION_TERMS = ("nosolution", "norealroot", "undefined", "emptyset")


def normalize_text(value: Any) -> str:
    """Normalize lightweight Markdown/LaTeX formatting for exact comparisons."""
    text = str(value).lower().strip()
    text = re.sub(r"[*_]", "", text)
    text = re.sub(r"\\[a-zA-Z]+", "", text)
    text = re.sub(r"[${}]", "", text)
    text = re.sub(r"\s+", "", text)
    return text.removesuffix(".")


def _symbolically_equivalent(left: str, right: str, tolerance: float = 0.03) -> bool:
    if sympy is None:
        try:
            return isclose(float(Fraction(str(left))), float(Fraction(str(right))), abs_tol=tolerance)
        except (TypeError, ValueError, ZeroDivisionError):
            return False
    try:
        left_expr = sympy.sympify(str(left).replace(",", "."))
        right_expr = sympy.sympify(str(right).replace(",", "."))
        if sympy.simplify(left_expr - right_expr) == 0:
            return True
        return abs(float(left_expr.evalf()) - float(right_expr.evalf())) < tolerance
    except (TypeError, ValueError, sympy.SympifyError):
        return False


def _matches_single_answer(model_answer: str, expected: str) -> bool:
    model_norm = normalize_text(model_answer)
    expected_norm = normalize_text(expected)
    if model_norm == expected_norm:
        return True
    return _symbolically_equivalent(model_answer, expected)


def evaluate_answer(raw_answer: Any, expected_result: str) -> int:
    """Return 1 when a delimited model answer matches the expected result."""
    if raw_answer is None:
        return 0
    match = _RESULT_PATTERN.search(str(raw_answer))
    if not match:
        return 0

    model_answer = match.group(1).strip()
    expected = str(expected_result).strip()
    expected_norm = normalize_text(expected)
    model_norm = normalize_text(model_answer)

    if any(term in expected_norm for term in _NO_SOLUTION_TERMS):
        return int(any(term in model_norm for term in _NO_SOLUTION_TERMS))

    if " or " in expected.lower():
        options = re.split(r"\s+or\s+", expected, flags=re.IGNORECASE)
        return int(any(_matches_single_answer(model_answer, option) for option in options))

    if " and " in expected.lower():
        components = re.split(r"\s+and\s+", expected, flags=re.IGNORECASE)
        return int(all(normalize_text(component) in model_norm for component in components))

    return int(_matches_single_answer(model_answer, expected))


def check_format(raw_answer: Any, variant: str) -> int:
    """Check the output contract for direct and structured-reasoning responses."""
    text = str(raw_answer or "")
    has_result = bool(_RESULT_PATTERN.search(text))
    if variant == "direct":
        return int(has_result)
    required_sections = ("ANALYSIS", "REASONING", "SELF-EVALUATION")
    return int(has_result and all(section in text.upper() for section in required_sections))


def validate_tasks(
    tasks: Iterable[dict[str, Any]],
    *,
    expected_task_count: int = 75,
    expected_category_count: int = 15,
    expected_tasks_per_category: int = 5,
) -> dict[str, int]:
    """Validate the public benchmark contract for the 75-task dataset."""
    rows = list(tasks)
    required = {"id", "category", "content", "expected_result"}
    missing_fields = sorted(required - set(rows[0]) if rows else required)
    if missing_fields:
        raise ValueError(f"missing required fields: {', '.join(missing_fields)}")

    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("task ids must be unique")

    counts = Counter(row["category"] for row in rows)
    if len(rows) != expected_task_count:
        raise ValueError(f"expected {expected_task_count} tasks, found {len(rows)}")
    if len(counts) != expected_category_count:
        raise ValueError(f"expected {expected_category_count} categories, found {len(counts)}")
    if any(count != expected_tasks_per_category for count in counts.values()):
        raise ValueError("each category must contain the expected number of tasks")
    return {"task_count": len(rows), "category_count": len(counts)}
