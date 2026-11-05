"""Shift cell references when rows or columns are inserted or deleted - like Excel does.

openpyxl moves cells but leaves every formula, range and name pointing at the old
places. These helpers rewrite references so nothing silently breaks:

    shift_formula("=SUM(B2:D2)", host="Data", target="Data", axis="col", at=3, n=1)
    -> "=SUM(B2:E2)"
"""

from __future__ import annotations

import re

from openpyxl.formula.tokenizer import Token, Tokenizer
from openpyxl.utils import column_index_from_string, get_column_letter

_CELL = re.compile(r"^(\$?)([A-Za-z]{1,3})(\$?)(\d+)$")
_COL = re.compile(r"^(\$?)([A-Za-z]{1,3})$")
_ROW = re.compile(r"^(\$?)(\d+)$")
REF_ERROR = "#REF!"


def split_sheet(ref: str) -> tuple[str | None, str]:
    """"'My sheet'!A1:B2" -> ("My sheet", "A1:B2")."""
    if "!" not in ref:
        return None, ref
    sheet, addr = ref.rsplit("!", 1)
    if sheet.startswith("'") and sheet.endswith("'"):
        sheet = sheet[1:-1].replace("''", "'")
    return sheet, addr


def quote_sheet(name: str) -> str:
    return f"'{name.replace(chr(39), chr(39) * 2)}'" if re.search(r"[^A-Za-z0-9_]", name) else name


def _shift_index(i: int, at: int, n: int) -> int | None:
    """New index for an insert (n > 0) or delete (n < 0) of |n| rows/cols starting at ``at``."""
    if n > 0:
        return i + n if i >= at else i
    end = at - n - 1
    if i < at:
        return i
    if i <= end:
        return None
    return i + n


def _shift_endpoint_pair(a: int, b: int, at: int, n: int):
    """Shift an inclusive span [a, b]. Returns None if it is deleted entirely."""
    if n > 0:
        return _shift_index(a, at, n), _shift_index(b, at, n)
    end = at - n - 1
    if a >= at and b <= end:
        return None
    na = a if a < at else (at if a <= end else a + n)
    nb = b + n if b > end else (at - 1 if b >= at else b)
    return na, nb


def shift_address(addr: str, axis: str, at: int, n: int) -> str:
    """Shift an address without sheet name: A1, $A$1, A1:C9, A:C, 2:5."""
    parts = addr.split(":")
    if len(parts) == 1:
        m = _CELL.match(addr)
        if not m:
            return addr
        d1, col, d2, row = m.groups()
        c, r = column_index_from_string(col.upper()), int(row)
        if axis == "col":
            c = _shift_index(c, at, n)
        else:
            r = _shift_index(r, at, n)
        if c is None or r is None:
            return REF_ERROR
        return f"{d1}{get_column_letter(c)}{d2}{r}"
    if len(parts) != 2:
        return addr
    a, b = parts
    ma, mb = _CELL.match(a), _CELL.match(b)
    if ma and mb:
        c1, r1 = column_index_from_string(ma.group(2).upper()), int(ma.group(4))
        c2, r2 = column_index_from_string(mb.group(2).upper()), int(mb.group(4))
        if axis == "col":
            span = _shift_endpoint_pair(c1, c2, at, n)
            if span is None:
                return REF_ERROR
            c1, c2 = span
        else:
            span = _shift_endpoint_pair(r1, r2, at, n)
            if span is None:
                return REF_ERROR
            r1, r2 = span
        return (f"{ma.group(1)}{get_column_letter(c1)}{ma.group(3)}{r1}:"
                f"{mb.group(1)}{get_column_letter(c2)}{mb.group(3)}{r2}")
    ca, cb = _COL.match(a), _COL.match(b)
    if ca and cb and axis == "col":
        span = _shift_endpoint_pair(column_index_from_string(ca.group(2).upper()),
                                    column_index_from_string(cb.group(2).upper()), at, n)
        if span is None:
            return REF_ERROR
        return f"{ca.group(1)}{get_column_letter(span[0])}:{cb.group(1)}{get_column_letter(span[1])}"
    ra, rb = _ROW.match(a), _ROW.match(b)
    if ra and rb and axis == "row":
        span = _shift_endpoint_pair(int(ra.group(2)), int(rb.group(2)), at, n)
        if span is None:
            return REF_ERROR
        return f"{ra.group(1)}{span[0]}:{rb.group(1)}{span[1]}"
    return addr


def shift_ref(ref: str, host: str, target: str, axis: str, at: int, n: int) -> str:
    """Shift one reference (maybe sheet-qualified) if it points at ``target``."""
    if "[" in ref:  # structured table reference or external workbook - Excel tracks those by name
        return ref
    sheet, addr = split_sheet(ref)
    if (sheet or host) != target:
        return ref
    new = shift_address(addr, axis, at, n)
    if new == REF_ERROR:
        return REF_ERROR
    return f"{ref.rsplit('!', 1)[0]}!{new}" if sheet is not None else new


def shift_formula(formula: str, host: str, target: str, axis: str, at: int, n: int) -> str:
    if not isinstance(formula, str) or not formula.startswith("="):
        return formula
    try:
        tok = Tokenizer(formula)
    except Exception:
        return formula
    changed = False
    pieces = []
    for t in tok.items:
        value = t.value
        if t.type == Token.OPERAND and t.subtype == Token.RANGE:
            new = shift_ref(value, host, target, axis, at, n)
            changed |= new != value
            value = new
        pieces.append(value)
    return "=" + "".join(pieces) if changed else formula


def shift_sqref(sqref, axis: str, at: int, n: int) -> str:
    """Shift a space-separated list of ranges (data validation / conditional formatting)."""
    out = [shift_address(r, axis, at, n) for r in str(sqref).split()]
    return " ".join(r for r in out if r != REF_ERROR)


def rename_sheet_in_formula(formula: str, old: str, new: str) -> str:
    if not isinstance(formula, str) or not formula.startswith("="):
        return formula
    try:
        tok = Tokenizer(formula)
    except Exception:
        return formula
    pieces = []
    for t in tok.items:
        value = t.value
        if t.type == Token.OPERAND and t.subtype == Token.RANGE and "!" in value:
            sheet, addr = split_sheet(value)
            if sheet == old:
                value = f"{quote_sheet(new)}!{addr}"
        pieces.append(value)
    return "=" + "".join(pieces)


def references_sheet(formula: str, sheet_name: str) -> bool:
    if not isinstance(formula, str) or not formula.startswith("="):
        return False
    try:
        tok = Tokenizer(formula)
    except Exception:
        return False
    return any(t.type == Token.OPERAND and t.subtype == Token.RANGE and split_sheet(t.value)[0] == sheet_name
               for t in tok.items)


def cells_referenced(formula: str, host: str):
    """Yield (sheet, min_col, min_row, max_col, max_row) for every A1 reference in a formula."""
    if not isinstance(formula, str) or not formula.startswith("="):
        return
    try:
        tok = Tokenizer(formula)
    except Exception:
        return
    from openpyxl.utils.cell import range_boundaries

    for t in tok.items:
        if t.type == Token.OPERAND and t.subtype == Token.RANGE and "[" not in t.value:
            sheet, addr = split_sheet(t.value)
            try:
                c0, r0, c1, r1 = range_boundaries(addr.replace("$", ""))
            except ValueError:
                continue
            yield (sheet or host, c0 or 1, r0 or 1, c1 or 16384, r1 or 1048576)
