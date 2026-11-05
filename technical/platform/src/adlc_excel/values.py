"""Turn what people type ("31/10/2026", "€1,200", "50%") into proper Excel values, and compare values."""

from __future__ import annotations

import re
from datetime import date, datetime, time

DATE_FORMATS = ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y", "%d %B %Y", "%d %b %Y", "%Y-%m-%dT%H:%M:%S")


def parse_date(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time())
    if not isinstance(value, str):
        return None
    text = value.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def parse_number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    if not isinstance(value, str):
        return None
    text = value.strip().replace(",", "").replace("€", "").replace("£", "").replace("$", "")
    pct = text.endswith("%")
    try:
        num = float(text.rstrip("%"))
    except ValueError:
        return None
    if pct:
        num /= 100
    return int(num) if num.is_integer() and not pct and "." not in text else num


def column_kind(cells) -> str:
    """'formula', 'date', 'number' or 'text' from the existing cells of a column."""
    values = [c.value for c in cells if c.value not in (None, "")]
    if not values:
        return "text"
    if sum(isinstance(v, str) and v.startswith("=") for v in values) >= max(1, len(values) // 2):
        return "formula"
    if sum(isinstance(v, (datetime, date)) for v in values) >= len(values) * 0.6:
        return "date"
    if sum(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values) >= len(values) * 0.6:
        return "number"
    return "text"


def to_cell_value(value, kind: str):
    """Convert typed input for a column of the given kind. Formulas (starting '=') pass through."""
    if value is None or (isinstance(value, str) and value.startswith("=")):
        return value
    if kind == "date":
        d = parse_date(value)
        if d is not None:
            return d
    if kind == "number":
        n = parse_number(value)
        if n is not None:
            return n
    if isinstance(value, str):
        d = parse_date(value) if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}", value.strip()) else None
        if d is not None:
            return d
    return value


def sort_key(value):
    """Blanks last; numbers and dates in order; text case-insensitive."""
    if value in (None, ""):
        return (3, "")
    if isinstance(value, (datetime, date)):
        return (0, parse_date(value).timestamp())
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return (1, float(value))
    return (2, str(value).strip().lower())


def matches(cell_value, op: str, target=None) -> bool:
    op = (op or "equals").lower().replace(" ", "_")
    blank = cell_value in (None, "") or (isinstance(cell_value, str) and not cell_value.strip())
    if op in ("blank", "is_blank", "empty"):
        return blank
    if op in ("not_blank", "is_not_blank", "not_empty"):
        return not blank
    if op == "in":
        return any(matches(cell_value, "equals", t) for t in (target or []))
    if op == "not_in":
        return not any(matches(cell_value, "equals", t) for t in (target or []))
    if blank:
        return op in ("not_equals",) and target not in (None, "")
    # Compare as dates, then numbers, then text.
    cd, td = parse_date(cell_value), parse_date(target)
    if cd is not None and (td is not None or target in ("today",)):
        td = td or datetime.combine(date.today(), time())
        a, b = cd, td
    else:
        cn, tn = parse_number(cell_value), parse_number(target)
        if cn is not None and tn is not None:
            a, b = cn, tn
        else:
            a, b = str(cell_value).strip().lower(), str(target if target is not None else "").strip().lower()
    if op in ("equals", "is", "="):
        return a == b
    if op in ("not_equals", "is_not", "!="):
        return a != b
    if op == "contains":
        return str(b) in str(a)
    if op == "not_contains":
        return str(b) not in str(a)
    if op == "starts_with":
        return str(a).startswith(str(b))
    if op == "ends_with":
        return str(a).endswith(str(b))
    try:
        if op in ("greater_than", "after", ">"):
            return a > b
        if op in ("less_than", "before", "<"):
            return a < b
        if op in ("at_least", "greater_or_equal", ">="):
            return a >= b
        if op in ("at_most", "less_or_equal", "<="):
            return a <= b
    except TypeError:
        return False
    raise ValueError(f"I don't know the condition '{op}'. Use equals, not_equals, contains, starts_with, "
                     "greater_than, less_than, at_least, at_most, before, after, blank, not_blank or in.")


def normalise_conditions(where) -> list[dict]:
    """Accept {"Status": "Done"} or [{"column": "Status", "op": "equals", "value": "Done"}]."""
    if not where:
        return []
    if isinstance(where, dict):
        if "column" in where:
            return [where]
        return [{"column": k, "op": "equals", "value": v} for k, v in where.items()]
    return list(where)
