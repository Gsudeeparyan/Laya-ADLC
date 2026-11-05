"""Formula helpers.

Excel's file format stores structured references in their long form
(``tblActions[[#This Row],[Due date]]``). The ``[@[Due date]]`` shorthand people type
in the Excel UI is not valid inside the file, so every formula is normalised before it is
written. Newer functions also need the ``_xlfn.`` prefix in the file.
"""

from __future__ import annotations

import re

# Functions added after Excel 2007 that must carry the _xlfn. prefix in the file.
XLFN_FUNCTIONS = (
    "XLOOKUP", "XMATCH", "IFS", "MAXIFS", "MINIFS", "SWITCH", "TEXTJOIN", "CONCAT",
    "IFNA", "DAYS", "ISOWEEKNUM", "STDEV.S", "STDEV.P", "PERCENTILE.INC", "RANK.EQ",
)

# Dynamic-array functions spill into neighbouring cells, which breaks table layouts.
DYNAMIC_ARRAY_FUNCTIONS = (
    "FILTER", "UNIQUE", "SORT", "SORTBY", "SEQUENCE", "LET", "LAMBDA", "RANDARRAY",
)

_THIS_ROW_BRACKETED = re.compile(r"\[@\[([^\[\]]+)\]\]")
_THIS_ROW_SIMPLE = re.compile(r"\[@([^\[\]]+)\]")
_XLFN = re.compile(
    r"(?<![\w.])(" + "|".join(re.escape(f) for f in XLFN_FUNCTIONS) + r")\s*\(",
    re.IGNORECASE,
)
_DYNAMIC = re.compile(
    r"(?<![\w.])(" + "|".join(DYNAMIC_ARRAY_FUNCTIONS) + r")\s*\(", re.IGNORECASE
)


def normalise(formula: str, table_name: str) -> str:
    """Return the file-safe form of ``formula`` for a calculated column of ``table_name``."""
    f = str(formula).strip()
    if not f.startswith("="):
        f = "=" + f
    f = _THIS_ROW_BRACKETED.sub(lambda m: f"{table_name}[[#This Row],[{m.group(1)}]]", f)
    f = _THIS_ROW_SIMPLE.sub(lambda m: f"{table_name}[[#This Row],[{m.group(1)}]]", f)
    f = _XLFN.sub(lambda m: f"_xlfn.{m.group(1).upper()}(", f)
    return f


def display(formula: str, table_name: str) -> str:
    """Return the friendly Excel-UI form of a normalised formula (for README text)."""
    return formula.replace(f"{table_name}[[#This Row],[", "[@[").replace("_xlfn.", "")


def dynamic_array_functions_used(formula: str) -> list[str]:
    return sorted({m.group(1).upper() for m in _DYNAMIC.finditer(str(formula))})


def _reference_spans(formula: str, table_name: str):
    """Yield (start, end) spans of every ``table_name[...]`` reference, brackets included."""
    needle = table_name + "["
    start = 0
    while True:
        i = formula.find(needle, start)
        if i < 0:
            return
        # Make sure we matched a whole table name, not the tail of a longer one.
        if i > 0 and (formula[i - 1].isalnum() or formula[i - 1] in "_."):
            start = i + 1
            continue
        j = i + len(table_name)
        depth = 0
        k = j
        while k < len(formula):
            if formula[k] == "[":
                depth += 1
            elif formula[k] == "]":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        yield j, k + 1
        start = k + 1


def references_column(formula: str, table_name: str, header: str) -> bool:
    """True if ``formula`` refers to column ``header`` of ``table_name``."""
    target = f"[{header}]".lower()
    return any(target in formula[a:b].lower() for a, b in _reference_spans(formula, table_name))


def rename_column_refs(formula: str, table_name: str, old: str, new: str) -> str:
    """Rewrite references to column ``old`` of ``table_name`` so they point at ``new``."""
    pieces = []
    last = 0
    pattern = re.compile(re.escape(f"[{old}]"), re.IGNORECASE)
    for a, b in _reference_spans(formula, table_name):
        pieces.append(formula[last:a])
        pieces.append(pattern.sub(f"[{new}]", formula[a:b]))
        last = b
    pieces.append(formula[last:])
    return "".join(pieces)


def references_table(formula: str, table_name: str) -> bool:
    return any(True for _ in _reference_spans(formula, table_name))
