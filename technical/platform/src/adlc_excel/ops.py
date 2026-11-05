"""Expert Excel operations for ANY workbook.

Each op is a small dict, e.g.
    {"op": "insert_column", "sheet": "Members", "header": "Priority", "after": "Status",
     "choices": ["High", "Medium", "Low"], "fill": "Medium"}
and returns a plain-English description of what changed. Targets are found by sheet name,
table name or column heading, so the caller never needs cell addresses (but may use them).
"""

from __future__ import annotations

import copy
import re
from datetime import datetime

from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule, DataBarRule, FormulaRule, Rule
from openpyxl.formula.translate import Translator
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.styles.differential import DifferentialStyle
from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import range_boundaries
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.filters import AutoFilter
from openpyxl.worksheet.table import Table, TableColumn, TableFormula, TableStyleInfo

from . import refs, structure
from .regions import GENERATED, Region, TargetError, find_region, find_sheet
from .values import column_kind, matches, normalise_conditions, sort_key, to_cell_value

NUMBER_FORMATS = {
    "date": "dd/mm/yyyy", "datetime": "dd/mm/yyyy hh:mm", "currency": '"€"#,##0.00', "euro": '"€"#,##0.00',
    "percent": "0%", "percentage": "0%", "number": "#,##0.00", "integer": "#,##0", "whole": "#,##0", "text": "@",
}
COLOURS = {
    "red": ("FFC7CE", "9C0006"), "amber": ("FFEB9C", "9C5700"), "yellow": ("FFF2CC", "7F6000"),
    "green": ("C6EFCE", "006100"), "blue": ("DDEBF7", "1F4E78"), "grey": ("EDEDED", "595959"),
    "gray": ("EDEDED", "595959"), "purple": ("E4DFEC", "5B2C83"), "orange": ("FCE4D6", "843C0C"),
}


class OpError(ValueError):
    """A change could not be made. The message is written for a non-technical reader."""


class Ctx:
    def __init__(self, wb):
        self.wb = wb
        self.warnings: list[str] = []
        self.sheet_renames: dict[str, str] = {}
        # Sheets whose charts an AI-safe workbook redraws from its spec on every save.
        self.adlc_chart_sheets: set[str] = set()
        if "_ADLC" in wb.sheetnames:
            try:
                from adlc_workbook.meta import read_meta

                _, spec = read_meta(wb)
                self.adlc_chart_sheets = {s["name"] for s in spec["sheets"] if s.get("charts")}
            except Exception:
                pass


# --------------------------------------------------------------------------- helpers


def _region(ctx, op, column=None) -> Region:
    return find_region(ctx.wb, op.get("sheet"), op.get("table"), column)


def _fmt(name):
    return NUMBER_FORMATS.get(str(name).lower(), name) if name else None


def _colour(name):
    if not name:
        return None
    key = str(name).lower()
    if key in COLOURS:
        return COLOURS[key]
    hexv = key.lstrip("#").upper()
    if re.fullmatch(r"[0-9A-F]{6}", hexv):
        return (hexv, "000000")
    raise OpError(f"I don't know the colour '{name}'. Use red, amber, yellow, green, blue, grey, purple, orange or a hex code.")


def _is_formula(v) -> bool:
    return isinstance(v, str) and v.startswith("=")


def _translate(formula: str, origin: str, dest: str) -> str:
    if "[" in formula:  # structured references are the same on every row
        return formula
    try:
        return Translator(formula, origin=origin).translate_formula(dest)
    except Exception:
        return formula


def _table_formula(formula: str, table) -> str:
    """Accept Excel's [@Column] shorthand inside tables and convert it to the file form."""
    from adlc_workbook.formulas import normalise

    return normalise(formula, table.displayName) if table is not None else formula


def _dv_list(ws, col, row):
    for dv in ws.data_validations.dataValidation:
        if dv.type != "list" or not dv.formula1 or not dv.formula1.startswith('"'):
            continue
        for rng in str(dv.sqref).split():
            c0, r0, c1, r1 = range_boundaries(rng)
            if c0 <= col <= c1 and r0 <= row <= r1:
                return [x.strip() for x in dv.formula1.strip('"').split(",")]
    return None


def _check_choice(ws, col, row, value, header):
    choices = _dv_list(ws, col, row)
    if not choices or value in (None, "") or _is_formula(value):
        return value
    for c in choices:
        if str(value).strip().lower() == c.lower():
            return c
    raise OpError(f"'{value}' isn't one of the options for '{header}': {', '.join(choices)}. "
                  "Use one of those, or add the option to the dropdown first.")


def _extend_ranges(ctx, ws, region_c0, region_c1, old_last, new_last):
    """After adding rows, grow totals, lookups, dropdowns and highlights that ended at the old last row."""
    def grow(ref_text, host):
        sheet, addr = refs.split_sheet(ref_text)
        if (sheet or host) != ws.title or "[" in ref_text or ":" not in addr:
            return ref_text
        try:
            c0, r0, c1, r1 = range_boundaries(addr.replace("$", ""))
        except ValueError:
            return ref_text
        if r1 != old_last or c0 is None or c1 < region_c0 or c0 > region_c1:
            return ref_text
        a, b = addr.split(":")
        b = re.sub(r"(\$?)(\d+)$", lambda m: f"{m.group(1)}{new_last}", b)
        return f"{ref_text.rsplit('!', 1)[0]}!{a}:{b}" if sheet is not None else f"{a}:{b}"

    from openpyxl.formula.tokenizer import Token, Tokenizer

    def grow_formula(f, host):
        try:
            tok = Tokenizer(f)
        except Exception:
            return f
        out, changed = [], False
        for t in tok.items:
            v = t.value
            if t.type == Token.OPERAND and t.subtype == Token.RANGE:
                nv = grow(v, host)
                changed |= nv != v
                v = nv
            out.append(v)
        return "=" + "".join(out) if changed else f

    grown = 0
    for sheet in ctx.wb.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if _is_formula(cell.value) and not (sheet is ws and region_c0 <= cell.column <= region_c1
                                                     and old_last < cell.row <= new_last):
                    new = grow_formula(cell.value, sheet.title)
                    if new != cell.value:
                        cell.value = new
                        grown += 1
    for name in list(ctx.wb.defined_names.keys()):
        dn = ctx.wb.defined_names[name]
        if dn.attr_text and "!" in dn.attr_text:
            new = grow_formula("=" + dn.attr_text, ws.title)[1:]
            if new != dn.attr_text:
                dn.attr_text, grown = new, grown + 1
    for sheet in ctx.wb.worksheets:
        for chart in getattr(sheet, "_charts", []):
            for s in getattr(chart, "series", []) or []:
                for attr in ("val", "cat"):
                    data = getattr(s, attr, None)
                    for holder in ((getattr(data, "numRef", None), getattr(data, "strRef", None)) if data else ()):
                        if holder is not None and holder.f:
                            holder.f = grow_formula("=" + holder.f, sheet.title)[1:]
    for dv in ws.data_validations.dataValidation:
        dv.sqref = " ".join(grow(r, ws.title) for r in str(dv.sqref).split())
    from openpyxl.formatting.formatting import ConditionalFormattingList

    rebuilt = ConditionalFormattingList()
    for cf in ws.conditional_formatting:
        sq = " ".join(grow(r, ws.title) for r in str(cf.sqref).split())
        for rule in cf.rules:
            rebuilt.add(sq, rule)
    ws.conditional_formatting = rebuilt
    if grown:
        ctx.warnings.append(f"{grown} formula(s) that covered the whole list (like totals) were extended to include the new rows.")


def _next_id(region, col):
    values = [str(region.ws.cell(r, col).value or "") for r in region.data_rows]
    pattern = [re.match(r"^([A-Za-z]+[-_]?)(\d+)$", v) for v in values if v]
    pattern = [m for m in pattern if m]
    if not pattern:
        return None
    prefix = pattern[-1].group(1)
    width = len(pattern[-1].group(2))
    nums = [int(m.group(2)) for m in pattern if m.group(1) == prefix]
    return prefix, width, max(nums, default=0)


def _rewrite_rows(ctx, region: Region, order: list[int]):
    """Rewrite the data rows of a region in a new order (row numbers), clearing the rest.

    Used by sort, delete and de-duplicate. Formulas are translated to their new row and
    cell formatting travels with each row. Content outside the region is untouched.
    """
    ws = region.ws
    cols = range(region.c0, region.c1 + 1)
    snapshot = {r: [(ws.cell(r, c).value, copy.copy(ws.cell(r, c)._style)) for c in cols] for r in region.data_rows}
    first = region.header_row + 1
    default_style = snapshot[first][0][1] if first in snapshot else None
    for i, r in enumerate(region.data_rows):
        src = order[i] if i < len(order) else None
        for j, c in enumerate(cols):
            cell = ws.cell(r, c)
            if src is None:
                cell.value = None
                if default_style is not None:
                    cell._style = copy.copy(snapshot[r][j][1])
                continue
            value, style = snapshot[src][j]
            if _is_formula(value) and src != r:
                value = _translate(value, f"{get_column_letter(c)}{src}", f"{get_column_letter(c)}{r}")
            cell.value = value
            cell._style = style
    if region.table is not None:
        new_last = max(region.header_row + 1, region.header_row + len(order))
        region.table.ref = f"{get_column_letter(region.c0)}{region.header_row}:{get_column_letter(region.c1)}{new_last}"
        if region.table.autoFilter is not None:
            region.table.autoFilter.ref = region.table.ref
        region.refresh_table()


def _matching_rows(region: Region, where) -> list[int]:
    conds = normalise_conditions(where)
    if not conds:
        raise OpError("Say which rows, e.g. where Status equals Done.")
    for c in conds:
        region.col(c["column"])
    rows = []
    for r in region.rows_with_data:
        try:
            if all(matches(region.ws.cell(r, region.col(c["column"])).value, c.get("op", "equals"), c.get("value"))
                   for c in conds):
                rows.append(r)
        except ValueError as exc:
            raise OpError(str(exc)) from None
    return rows


def _describe_where(where) -> str:
    parts = []
    for c in normalise_conditions(where):
        op = c.get("op", "equals").replace("_", " ")
        parts.append(f"{c['column']} {op}" + (f" {c.get('value')}" if c.get("value") is not None else ""))
    return " and ".join(parts)


def _copy_to_sheet(ctx, region: Region, rows: list[int], sheet_name: str, reason: str):
    """Keep a copy of rows that are about to be removed, so nothing is lost."""
    wb = ctx.wb
    ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb.create_sheet(sheet_name)
    if ws.max_row == 1 and ws["A1"].value is None:
        ws.cell(1, 1, "Removed on")
        ws.cell(1, 2, "Reason")
        for j, h in enumerate(region.headers, start=3):
            ws.cell(1, j, h).font = Font(bold=True)
        ws["A1"].font = ws["B1"].font = Font(bold=True)
    for r in rows:
        out = ws.max_row + 1
        ws.cell(out, 1, datetime.now().replace(microsecond=0)).number_format = "dd/mm/yyyy hh:mm"
        ws.cell(out, 2, reason)
        for j, c in enumerate(range(region.c0, region.c1 + 1), start=3):
            src = region.ws.cell(r, c)
            cell = ws.cell(out, j, src.value)
            cell.number_format = src.number_format
            if _is_formula(src.value):  # keep the formula as readable text, not live
                cell.data_type = "s"


# --------------------------------------------------------------------------- columns


def op_insert_column(ctx, op):
    header = str(op.get("header") or "").strip()
    if not header:
        raise OpError("Give the new column a heading.")
    anchor_col = op.get("after") or op.get("before")
    region = _region(ctx, op, anchor_col)
    if region.has_col(header):
        raise OpError(f"There is already a column called '{header}' in {region.name}.")
    ws = region.ws
    if op.get("after"):
        at = region.col(op["after"]) + 1
    elif op.get("before"):
        at = region.col(op["before"])
    else:
        at = region.c1 + 1
    end_free = at == region.c1 + 1 and all(ws.cell(r, at).value in (None, "") for r in range(region.header_row, region.last_row + 1))
    if end_free:
        if region.table is not None:
            t = region.table
            t.tableColumns.append(TableColumn(id=len(t.tableColumns) + 1, name=header))
            t.ref = f"{get_column_letter(region.c0)}{region.header_row}:{get_column_letter(at)}{region.last_row}"
            if t.autoFilter is not None:
                t.autoFilter.ref = t.ref
    else:
        structure.insert_cols(ctx.wb, ws, at, 1, headers=[header])
    region.c1 += 1
    if region.table is not None:
        region.refresh_table()

    neighbour = at - 1 if at > region.c0 else at + 1
    head = ws.cell(region.header_row, at, header)
    head._style = copy.copy(ws.cell(region.header_row, neighbour)._style)
    rows = list(region.data_rows)
    formula = op.get("formula")
    values = op.get("values")
    fill = op.get("fill")
    if formula and region.table is not None and "[@" in formula:
        formula = _table_formula(formula, region.table)
        for tc in region.table.tableColumns:
            if tc.name == header:
                tc.calculatedColumnFormula = TableFormula(attr_text=formula[1:])
    number_format = _fmt(op.get("number_format"))
    for i, r in enumerate(rows):
        cell = ws.cell(r, at)
        cell._style = copy.copy(ws.cell(r, neighbour)._style)
        cell.number_format = number_format or "General"
        if formula:
            if region.is_blank_row(r) and region.table is None:
                continue
            first = f"{get_column_letter(at)}{rows[0]}"
            cell.value = _translate(formula, first, f"{get_column_letter(at)}{r}")
        elif values is not None:
            if i < len(values):
                cell.value = to_cell_value(values[i], "text")
        elif fill is not None and not region.is_blank_row(r):
            cell.value = to_cell_value(fill, "text")
        if isinstance(cell.value, datetime) and not number_format:
            cell.number_format = "dd/mm/yyyy"
    if op.get("choices"):
        _add_list_validation(ws, at, rows[0] if rows else region.header_row + 1, max(region.last_row, region.header_row + 1),
                             op["choices"], header)
    ws.column_dimensions[get_column_letter(at)].width = max(12, min(len(header) + 4, 45))
    where = "at the end" if end_free else (f"after '{op['after']}'" if op.get("after") else f"before '{op['before']}'" if op.get("before") else "")
    extra = f", worked out as {formula}" if formula else (f", options: {', '.join(op['choices'])}" if op.get("choices") else "")
    return f"Added column '{header}' to {region.name} {where}{extra}".strip()


def op_delete_column(ctx, op):
    region = _region(ctx, op, op.get("column"))
    col = region.col(op["column"])
    header = region.headers[col - region.c0]
    ws = region.ws
    users, shrinking = [], []
    for sheet in ctx.wb.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if not _is_formula(cell.value) or (sheet is ws and cell.column == col):
                    continue
                for s, c0, r0, c1, r1 in refs.cells_referenced(cell.value, sheet.title):
                    if s == ws.title and c0 == c1 == col:
                        users.append(f"{sheet.title}!{cell.coordinate}")      # would become #REF!
                    elif s == ws.title and c0 <= col <= c1:
                        shrinking.append(f"{sheet.title}!{cell.coordinate}")  # range just gets narrower
                if region.table is not None and f"[{header.lower()}]" in cell.value.lower()                         and region.table.displayName.lower() in cell.value.lower():
                    users.append(f"{sheet.title}!{cell.coordinate}")
    users = sorted(set(users))
    if shrinking:
        ctx.warnings.append(f"Formulas covering several columns ({', '.join(sorted(set(shrinking))[:3])}) will no longer include '{header}'.")
    if users and not op.get("force"):
        raise OpError(f"'{header}' is used by formulas in {', '.join(users[:5])}{' and more' if len(users) > 5 else ''}. "
                      "Removing it would break them (#REF!). Change those formulas first, or confirm with force.")
    outside = [r for r in range(1, ws.max_row + 1)
               if not (region.header_row <= r <= region.last_row) and ws.cell(r, col).value not in (None, "")]
    if outside and not op.get("force"):
        raise OpError(f"Column {get_column_letter(col)} also has other content outside the table (row {outside[0]}). "
                      "Deleting the column would remove that too. Confirm with force if that's OK.")
    structure.delete_cols(ctx.wb, ws, col, 1)
    return f"Removed column '{header}' from {region.name}"


def op_rename_column(ctx, op):
    region = _region(ctx, op, op.get("column"))
    col = region.col(op["column"])
    old = region.headers[col - region.c0]
    new = str(op.get("new_header") or op.get("header") or "").strip()
    if not new:
        raise OpError("Give the new heading.")
    if region.has_col(new) and new.lower() != old.lower():
        raise OpError(f"There is already a column called '{new}'.")
    region.ws.cell(region.header_row, col).value = new
    if region.table is not None:
        from adlc_workbook.formulas import rename_column_refs

        tname = region.table.displayName
        for tc in region.table.tableColumns:
            if tc.name == old:
                tc.name = new
        n = 0
        for sheet in ctx.wb.worksheets:
            for row in sheet.iter_rows():
                for cell in row:
                    if _is_formula(cell.value):
                        newf = rename_column_refs(cell.value, tname, old, new)
                        if newf != cell.value:
                            cell.value, n = newf, n + 1
            for t in sheet.tables.values():
                for tc in t.tableColumns:
                    if tc.calculatedColumnFormula is not None and tc.calculatedColumnFormula.attr_text:
                        tc.calculatedColumnFormula.attr_text = rename_column_refs(
                            "=" + tc.calculatedColumnFormula.attr_text, tname, old, new)[1:]
        if n:
            ctx.warnings.append(f"Updated {n} formula(s) that referred to '{old}'.")
    return f"Renamed column '{old}' to '{new}' in {region.name}"


# --------------------------------------------------------------------------- rows


def op_add_rows(ctx, op):
    rows_in = op.get("rows") or []
    if not rows_in:
        raise OpError("Give at least one row to add.")
    headers_given = {k for r in rows_in for k in r}
    region = _region(ctx, op, next(iter(headers_given), None))
    ws = region.ws
    for h in headers_given:
        region.col(h)
    kinds = {c: column_kind([ws.cell(r, c) for r in region.data_rows]) for c in range(region.c0, region.c1 + 1)}
    filled = region.rows_with_data
    start = (filled[-1] + 1) if filled else region.header_row + 1
    old_last = region.last_row
    n = len(rows_in)
    needed_last = start + n - 1
    if needed_last > region.last_row:
        blocked = any(ws.cell(r, c).value not in (None, "") for r in range(region.last_row + 1, needed_last + 1)
                      for c in range(region.c0, region.c1 + 1))
        if blocked:
            structure.insert_rows(ctx.wb, ws, region.last_row + 1, needed_last - region.last_row)
            ctx.warnings.append("Content below the table was moved down to make room for the new rows.")
            region.refresh_table()
    template = filled[-1] if filled else region.header_row + 1
    id_cols = [c for c in range(region.c0, region.c1 + 1) if region.headers[c - region.c0].lower() in ("id", "ref", "reference")]
    next_ids = {c: _next_id(region, c) for c in id_cols}
    added = []
    for i, values in enumerate(rows_in):
        r = start + i
        given = {region.col(k): v for k, v in values.items()}
        for c in range(region.c0, region.c1 + 1):
            cell = ws.cell(r, c)
            src = ws.cell(template, c)
            if r != template:
                cell._style = copy.copy(src._style)
            header = region.headers[c - region.c0]
            if c in given:
                value = to_cell_value(given[c], kinds[c])
                cell.value = _check_choice(ws, c, template, value, header)
            elif kinds[c] == "formula" and _is_formula(src.value):
                cell.value = _translate(src.value, src.coordinate, cell.coordinate)
            elif c in id_cols and next_ids.get(c):
                prefix, width, last = next_ids[c]
                cell.value = f"{prefix}{last + 1:0{width}d}"
                next_ids[c] = (prefix, width, last + 1)
        added.append(r)
    new_last = max(region.last_row, start + n - 1)
    if region.table is not None:
        region.table.ref = f"{get_column_letter(region.c0)}{region.header_row}:{get_column_letter(region.c1)}{new_last}"
        if region.table.autoFilter is not None:
            region.table.autoFilter.ref = region.table.ref
    if new_last > old_last:
        _extend_ranges(ctx, ws, region.c0, region.c1, old_last, new_last)
    region.last_row = new_last
    return f"Added {n} row(s) to {region.name} (rows {added[0]}-{added[-1]})" if n > 1 else f"Added 1 row to {region.name} (row {added[0]})"


def op_update_rows(ctx, op):
    sets = op.get("set") or {}
    if not sets:
        raise OpError("Say what to change, e.g. set Status to Done.")
    region = _region(ctx, op, next(iter(sets)))
    ws = region.ws
    rows = _matching_rows(region, op.get("where"))
    if not rows:
        raise OpError(f"No rows in {region.name} match: {_describe_where(op.get('where'))}. Nothing was changed.")
    first_data = region.header_row + 1
    kinds = {region.col(k): column_kind([ws.cell(r, region.col(k)) for r in region.data_rows]) for k in sets}
    for r in rows:
        for k, v in sets.items():
            c = region.col(k)
            if _is_formula(v):
                value = _translate(_table_formula(v, region.table) if region.table is not None and "[@" in v else v,
                                   f"{get_column_letter(c)}{first_data}", f"{get_column_letter(c)}{r}")
            else:
                value = _check_choice(ws, c, r, to_cell_value(v, kinds[c]), k)
            ws.cell(r, c).value = value
    what = ", ".join(f"{k} = {v}" for k, v in sets.items())
    return f"Updated {len(rows)} row(s) in {region.name} where {_describe_where(op.get('where'))}: {what}"


def op_delete_rows(ctx, op):
    region = _region(ctx, op, normalise_conditions(op.get("where"))[0]["column"] if op.get("where") else None)
    rows = _matching_rows(region, op.get("where"))
    if not rows:
        raise OpError(f"No rows in {region.name} match: {_describe_where(op.get('where'))}. Nothing was deleted.")
    if op.get("keep_copy", True):
        _copy_to_sheet(ctx, region, rows, "Deleted rows", f"Deleted where {_describe_where(op.get('where'))}")
    keep = [r for r in region.rows_with_data if r not in rows]
    _rewrite_rows(ctx, region, keep)
    note = " A copy is on the 'Deleted rows' sheet." if op.get("keep_copy", True) else ""
    return f"Deleted {len(rows)} row(s) from {region.name} where {_describe_where(op.get('where'))}.{note}"


def op_sort(ctx, op):
    by = op.get("by") or []
    if isinstance(by, (str, dict)):
        by = [by]
    by = [{"column": b} if isinstance(b, str) else b for b in by]
    if not by:
        raise OpError("Say which column to sort by.")
    region = _region(ctx, op, by[0]["column"])
    rows = region.rows_with_data
    cols = [(region.col(b["column"]), str(b.get("order", "asc")).lower().startswith("desc")) for b in by]
    ordered = rows
    for c, desc in reversed(cols):
        values = {r: region.ws.cell(r, c).value for r in ordered}
        blanks = [r for r in ordered if values[r] in (None, "")]
        filled = sorted([r for r in ordered if values[r] not in (None, "")], key=lambda r: sort_key(values[r]), reverse=desc)
        ordered = filled + blanks
    _rewrite_rows(ctx, region, ordered)
    desc = ", then ".join(f"{b['column']} ({'Z-A / largest first' if str(b.get('order', 'asc')).lower().startswith('desc') else 'A-Z / smallest first'})" for b in by)
    return f"Sorted {len(rows)} row(s) in {region.name} by {desc}"


def op_dedupe(ctx, op):
    region = _region(ctx, op, (op.get("columns") or [None])[0])
    cols = [region.col(c) for c in (op.get("columns") or region.headers)]
    keep_last = str(op.get("keep", "first")).lower() == "last"
    rows = region.rows_with_data
    seen, dupes = {}, []
    for r in (reversed(rows) if keep_last else rows):
        key = tuple(str(region.ws.cell(r, c).value or "").strip().lower() for c in cols)
        if key in seen:
            dupes.append(r)
        else:
            seen[key] = r
    if not dupes:
        return f"No duplicates found in {region.name}"
    _copy_to_sheet(ctx, region, sorted(dupes), "Removed duplicates", "Duplicate of an earlier row")
    _rewrite_rows(ctx, region, [r for r in rows if r not in dupes])
    on = ", ".join(region.headers[c - region.c0] for c in cols)
    return f"Removed {len(dupes)} duplicate row(s) from {region.name} (matching on {on}); copies are on 'Removed duplicates'"


def op_find_replace(ctx, op):
    find, repl = op.get("find"), op.get("replace", "")
    if find in (None, ""):
        raise OpError("Say what to find.")
    case = bool(op.get("match_case"))
    whole = bool(op.get("whole_cell"))
    sheets = [find_sheet(ctx.wb, op["sheet"])] if op.get("sheet") else [ws for ws in ctx.wb.worksheets if ws.title not in GENERATED]
    count = 0
    for ws in sheets:
        cols = None
        if op.get("column"):
            region = find_region(ctx.wb, ws.title, op.get("table"), op["column"])
            cols = {region.col(op["column"])}
        for row in ws.iter_rows():
            for cell in row:
                v = cell.value
                if not isinstance(v, str) or _is_formula(v) or (cols and cell.column not in cols):
                    continue
                if whole:
                    hit = v == find if case else v.strip().lower() == str(find).lower()
                    if hit:
                        cell.value = to_cell_value(repl, "text")
                        count += 1
                else:
                    pattern = re.compile(re.escape(str(find)), 0 if case else re.IGNORECASE)
                    new, k = pattern.subn(str(repl), v)
                    if k:
                        cell.value, count = new, count + 1
    if not count:
        raise OpError(f"I didn't find '{find}' anywhere{' in ' + op['column'] if op.get('column') else ''}. Nothing was changed.")
    return f"Replaced '{find}' with '{repl}' in {count} cell(s)"


def op_set_cells(ctx, op):
    ws = find_sheet(ctx.wb, op.get("sheet")) if op.get("sheet") else ctx.wb.worksheets[0]
    cells = op.get("cells") or {}
    for addr, value in cells.items():
        ws[addr].value = to_cell_value(value, "text")
    return f"Set {len(cells)} cell(s) on '{ws.title}': {', '.join(list(cells)[:6])}"


def op_fill_formula(ctx, op):
    region = _region(ctx, op, op.get("column"))
    col = region.col(op["column"])
    formula = op.get("formula")
    if not _is_formula(formula):
        raise OpError("The formula must start with '=' and be written for the first data row, e.g. =D2*1.23.")
    if region.table is not None and "[@" in formula:
        formula = _table_formula(formula, region.table)
        header = region.headers[col - region.c0]
        for tc in region.table.tableColumns:
            if tc.name == header:
                tc.calculatedColumnFormula = TableFormula(attr_text=formula[1:])
    rows = _matching_rows(region, op["where"]) if op.get("where") else [r for r in region.data_rows if region.table is not None or not region.is_blank_row(r)]
    first = f"{get_column_letter(col)}{region.header_row + 1}"
    for r in rows:
        region.ws.cell(r, col).value = _translate(formula, first, f"{get_column_letter(col)}{r}")
    return f"Filled '{region.headers[col - region.c0]}' in {len(rows)} row(s) with {formula}"


def op_split_column(ctx, op):
    region = _region(ctx, op, op.get("column"))
    col = region.col(op["column"])
    into = op.get("into") or ["Part 1", "Part 2"]
    delim = op.get("delimiter", " ")
    after = region.headers[col - region.c0]
    for k, name in enumerate(into):
        op_insert_column(ctx, {"sheet": region.ws.title, "table": op.get("table"), "header": name,
                               "after": after if k == 0 else into[k - 1]})
    region = _region(ctx, op, op.get("column"))
    col = region.col(op["column"])
    for r in region.rows_with_data:
        v = region.ws.cell(r, col).value
        if v in (None, "") or _is_formula(v):
            continue
        parts = str(v).split(delim, len(into) - 1) if delim else [str(v)]
        if delim == " " and len(into) == 2:
            parts = str(v).strip().split(" ", 1)
        for k in range(len(into)):
            region.ws.cell(r, col + 1 + k).value = parts[k].strip() if k < len(parts) else None
    return f"Split '{after}' into {', '.join(repr(i) for i in into)} in {region.name}"


def op_combine_columns(ctx, op):
    columns = op.get("columns") or []
    if len(columns) < 2:
        raise OpError("Give at least two columns to combine.")
    sep = op.get("separator", " ")
    region = _region(ctx, op, columns[0])
    first_row = region.header_row + 1
    if region.table is not None:
        parts = [f"[@[{region.headers[region.col(c) - region.c0]}]]" for c in columns]
    else:
        parts = [f"{get_column_letter(region.col(c))}{first_row}" for c in columns]
    joiner = f'&"{sep}"&'
    formula = f"=TRIM({joiner.join(parts)})"
    header = op.get("into") or " ".join(columns)
    op_insert_column(ctx, {"sheet": region.ws.title, "table": op.get("table"), "header": header,
                           "after": op.get("after") or columns[-1], "formula": formula})
    return f"Added '{header}' combining {', '.join(columns)} (it updates itself when they change)"


# --------------------------------------------------------------------------- formatting and rules


def _target_ranges(ctx, op) -> tuple[object, list[str]]:
    if op.get("range"):
        ws = find_sheet(ctx.wb, op.get("sheet")) if op.get("sheet") else ctx.wb.worksheets[0]
        return ws, [op["range"]]
    columns = op.get("columns") or ([op["column"]] if op.get("column") else None)
    region = _region(ctx, op, columns[0] if columns else None)
    last = max(region.last_row, region.header_row + 1)
    if op.get("header_only"):
        return region.ws, [f"{get_column_letter(region.c0)}{region.header_row}:{get_column_letter(region.c1)}{region.header_row}"]
    if not columns:
        return region.ws, [f"{get_column_letter(region.c0)}{region.header_row + 1}:{get_column_letter(region.c1)}{last}"]
    out = []
    for c in columns:
        letter = get_column_letter(region.col(c))
        out.append(f"{letter}{region.header_row + 1}:{letter}{last}")
    return region.ws, out


def op_format(ctx, op):
    ws, ranges = _target_ranges(ctx, op)
    side = Side(style="thin", color="BFBFBF")
    n = 0
    for rng in ranges:
        for row in ws[rng]:
            for cell in (row if isinstance(row, tuple) else (row,)):
                n += 1
                if op.get("number_format"):
                    cell.number_format = _fmt(op["number_format"])
                if any(k in op for k in ("bold", "italic", "font_color", "size")):
                    f = copy.copy(cell.font)
                    cell.font = Font(name=f.name, size=op.get("size", f.size), bold=op.get("bold", f.bold),
                                     italic=op.get("italic", f.italic),
                                     color=(_colour(op["font_color"])[1] if op.get("font_color") in COLOURS else
                                            (op["font_color"].lstrip("#") if op.get("font_color") else f.color)))
                if op.get("fill"):
                    bg = _colour(op["fill"])[0]
                    cell.fill = PatternFill(fill_type="solid", start_color=bg, end_color=bg)
                if op.get("align") or "wrap" in op:
                    a = cell.alignment
                    cell.alignment = Alignment(horizontal=op.get("align", a.horizontal), vertical=a.vertical or "top",
                                               wrap_text=op.get("wrap", a.wrap_text))
                if op.get("border"):
                    cell.border = Border(left=side, right=side, top=side, bottom=side) if op["border"] != "none" else Border()
    if op.get("width"):
        for rng in ranges:
            c0, _, c1, _ = range_boundaries(rng)
            for c in range(c0, c1 + 1):
                ws.column_dimensions[get_column_letter(c)].width = op["width"]
    changed = [k.replace("_", " ") for k in ("number_format", "bold", "italic", "font_color", "fill", "align", "wrap", "border", "width") if k in op]
    return f"Formatted {', '.join(ranges)} on '{ws.title}' ({', '.join(changed)})"


def op_conditional_format(ctx, op):
    ws, ranges = _target_ranges(ctx, op)
    rule_type = str(op.get("rule", "equals")).lower()
    bg, fg = _colour(op.get("color", "red")) if rule_type not in ("color_scale", "data_bar") else (None, None)
    fill = PatternFill(start_color=bg, end_color=bg, fill_type="solid") if bg else None
    font = Font(color=fg) if fg else None

    def lit(v):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return str(v)
        return '"' + str(v).replace('"', '""') + '"'

    applied = []
    for rng in ranges:
        c0, r0, c1, r1 = range_boundaries(rng)
        first = f"${get_column_letter(c0)}{r0}"
        target = rng
        if op.get("whole_row"):
            region = _region(ctx, op, op.get("column"))
            target = f"{get_column_letter(region.c0)}{r0}:{get_column_letter(region.c1)}{r1}"
        v, v2 = op.get("value"), op.get("value2")
        if rule_type == "color_scale":
            rule = ColorScaleRule(start_type="min", start_color="F8696B", mid_type="percentile", mid_value=50,
                                  mid_color="FFEB84", end_type="max", end_color="63BE7B")
            if op.get("reverse"):
                rule = ColorScaleRule(start_type="min", start_color="63BE7B", mid_type="percentile", mid_value=50,
                                      mid_color="FFEB84", end_type="max", end_color="F8696B")
        elif rule_type == "data_bar":
            rule = DataBarRule(start_type="min", end_type="max", color="5B9BD5")
        elif rule_type == "duplicates":
            rule = Rule(type="duplicateValues", dxf=DifferentialStyle(fill=fill, font=font))
        elif rule_type in ("top", "bottom"):
            rule = Rule(type="top10", rank=int(op.get("n", 10)), bottom=rule_type == "bottom",
                        dxf=DifferentialStyle(fill=fill, font=font))
        else:
            expr = {
                "equals": f"{first}={lit(v)}",
                "not_equals": f"AND(LEN({first})>0,{first}<>{lit(v)})",
                "greater_than": f"AND(ISNUMBER({first}),{first}>{lit(v)})",
                "less_than": f"AND(ISNUMBER({first}),{first}<{lit(v)})",
                "at_least": f"AND(ISNUMBER({first}),{first}>={lit(v)})",
                "at_most": f"AND(ISNUMBER({first}),{first}<={lit(v)})",
                "between": f"AND(ISNUMBER({first}),{first}>={lit(v)},{first}<={lit(v2)})",
                "contains": f"ISNUMBER(SEARCH({lit(v)},{first}))",
                "blank": f"LEN(TRIM({first}))=0",
                "not_blank": f"LEN(TRIM({first}))>0",
                "date_past": f"AND(ISNUMBER({first}),{first}<TODAY())",
                "date_within_days": f"AND(ISNUMBER({first}),{first}>=TODAY(),{first}-TODAY()<={lit(v or 7)})",
                "formula": str(v or "").lstrip("="),
            }.get(rule_type)
            if expr is None:
                raise OpError(f"I don't know the highlight rule '{rule_type}'. Use equals, not_equals, greater_than, "
                              "less_than, at_least, at_most, between, contains, blank, not_blank, date_past, "
                              "date_within_days, duplicates, top, bottom, color_scale, data_bar or formula.")
            rule = FormulaRule(formula=[expr], fill=fill, font=font)
        ws.conditional_formatting.add(target, rule)
        applied.append(target)
    what = rule_type.replace("_", " ") + (f" {op.get('value')}" if op.get("value") is not None and rule_type != "formula" else "")
    colour = f" in {op.get('color', 'red')}" if bg else ""
    return f"Highlight{colour} where {what} on '{ws.title}' {', '.join(applied)}"


def _add_list_validation(ws, col, first_row, last_row, choices, header):
    letter = get_column_letter(col)
    joined = ",".join(str(c) for c in choices)
    if len(joined) > 250 or any("," in str(c) for c in choices):
        raise OpError("That list is too long for a dropdown typed in directly; put the options on a sheet and use 'source'.")
    dv = DataValidation(type="list", formula1=f'"{joined}"', allow_blank=True)
    dv.errorTitle = "Please pick from the list"
    dv.error = f"'{header}' must be one of the dropdown options."[:225]
    dv.showErrorMessage = True
    dv.add(f"{letter}{first_row}:{letter}{last_row}")
    ws.add_data_validation(dv)


def op_add_validation(ctx, op):
    region = _region(ctx, op, op.get("column"))
    col = region.col(op["column"])
    header = region.headers[col - region.c0]
    ws = region.ws
    first, last = region.header_row + 1, max(region.last_row, region.header_row + 1)
    letter = get_column_letter(col)
    # Remove an existing rule on this column first, so the new one is the only one.
    for dv in list(ws.data_validations.dataValidation):
        if any(range_boundaries(r)[0] <= col <= range_boundaries(r)[2] for r in str(dv.sqref).split()):
            ws.data_validations.dataValidation.remove(dv)
    kind = str(op.get("kind", "list")).lower()
    if kind == "list":
        if op.get("source"):
            dv = DataValidation(type="list", formula1="=" + str(op["source"]).lstrip("="), allow_blank=True)
            dv.add(f"{letter}{first}:{letter}{last}")
            dv.showErrorMessage = True
            ws.add_data_validation(dv)
        else:
            _add_list_validation(ws, col, first, last, op.get("choices") or [], header)
        bad = sorted({str(ws.cell(r, col).value) for r in region.rows_with_data if ws.cell(r, col).value not in (None, "")
                      and op.get("choices") and str(ws.cell(r, col).value).lower() not in [str(c).lower() for c in op["choices"]]})
        if bad:
            ctx.warnings.append(f"Existing values in '{header}' not in the new list: {', '.join(bad[:6])}.")
        what = f"dropdown ({', '.join(map(str, op.get('choices') or [])) or op.get('source')})"
    else:
        types = {"whole": "whole", "integer": "whole", "decimal": "decimal", "number": "decimal", "date": "date", "text_length": "textLength"}
        if kind not in types:
            raise OpError("Validation kind must be list, whole, decimal, date or text_length.")
        lo, hi = op.get("min"), op.get("max")
        if kind == "date":
            from .values import parse_date

            lo = str(int((parse_date(lo) - datetime(1899, 12, 30)).days)) if lo else "1"
            hi = str(int((parse_date(hi) - datetime(1899, 12, 30)).days)) if hi else "2958465"
        dv = DataValidation(type=types[kind], operator="between", formula1=str(lo if lo is not None else -1e12),
                            formula2=str(hi if hi is not None else 1e12), allow_blank=True)
        dv.showErrorMessage = True
        dv.error = (op.get("message") or f"'{header}' needs a valid {kind.replace('_', ' ')}.")[:225]
        dv.add(f"{letter}{first}:{letter}{last}")
        ws.add_data_validation(dv)
        what = f"{kind} between {op.get('min', 'any')} and {op.get('max', 'any')}"
    return f"'{header}' in {region.name} now only accepts a {what}"


def op_freeze_panes(ctx, op):
    ws = find_sheet(ctx.wb, op.get("sheet")) if op.get("sheet") else ctx.wb.worksheets[0]
    cell = op.get("cell")
    if not cell or cell == "header":
        region = find_region(ctx.wb, ws.title)
        cell = f"A{region.header_row + 1}"
    ws.freeze_panes = cell
    return f"Froze the rows above {cell} on '{ws.title}' so the headings stay visible"


# --------------------------------------------------------------------------- lookups, summaries, charts


def _range_for(region: Region, header: str, absolute=True) -> str:
    if region.table is not None:
        return f"{region.table.displayName}[{region.headers[region.col(header) - region.c0]}]"
    letter = get_column_letter(region.col(header))
    sheet = refs.quote_sheet(region.ws.title)
    last = max(region.last_row, region.header_row + 1)
    return f"{sheet}!${letter}${region.header_row + 1}:${letter}${last}"


def op_add_lookup_column(ctx, op):
    src_spec = op.get("from") or {}
    key = op.get("key_column")
    if not key or not src_spec.get("key_column") or not src_spec.get("return_column"):
        raise OpError("A lookup needs: key_column (here), and from.key_column + from.return_column (in the other table).")
    target = _region(ctx, op, key)
    source = find_region(ctx.wb, src_spec.get("sheet"), src_spec.get("table"), src_spec["return_column"])
    ret = _range_for(source, src_spec["return_column"])
    keys = _range_for(source, src_spec["key_column"])
    if target.table is not None:
        me = f"[@[{target.headers[target.col(key) - target.c0]}]]"
    else:
        me = f"{get_column_letter(target.col(key))}{target.header_row + 1}"
    missing = op.get("if_not_found", "")
    formula = f'=IFERROR(INDEX({ret},MATCH({me},{keys},0)),"{missing}")'
    header = op.get("header") or src_spec["return_column"]
    op_insert_column(ctx, {"sheet": target.ws.title, "table": op.get("table"), "header": header,
                           "after": op.get("after") or key, "formula": formula})
    return (f"Added '{header}' to {target.name}: looks up {src_spec['return_column']} from {source.name} "
            f"by matching {key} to {src_spec['key_column']} (blank if not found)")


AGG = {"count": "COUNTIFS", "sum": "SUMIFS", "average": "AVERAGEIFS", "avg": "AVERAGEIFS",
       "min": "_xlfn.MINIFS", "max": "_xlfn.MAXIFS"}


def op_add_summary(ctx, op):
    group = op.get("group_by")
    if not group:
        raise OpError("Say what to group by, e.g. group_by: Status.")
    src = find_region(ctx.wb, op.get("source_sheet") or op.get("sheet"), op.get("source_table") or op.get("table"), group)
    gcol = src.col(group)
    choices = _dv_list(src.ws, gcol, src.header_row + 1)
    groups = choices or sorted({src.ws.cell(r, gcol).value for r in src.rows_with_data
                                if src.ws.cell(r, gcol).value not in (None, "")}, key=sort_key)
    measures = op.get("measures") or [{"agg": "count"}]
    name = op.get("target_sheet") or "Summary"
    base, k = name, 2
    while name in ctx.wb.sheetnames and ctx.wb[name].max_row > 1:
        name, k = f"{base} {k}", k + 1
    ws = ctx.wb[name] if name in ctx.wb.sheetnames else ctx.wb.create_sheet(name)
    grng = _range_for(src, group)
    heads = [src.headers[gcol - src.c0]]
    tname = re.sub(r"[^A-Za-z0-9_]", "", f"tblSummary{heads[0].title()}")[:240]
    existing = {t.lower() for s in ctx.wb.worksheets for t in s.tables}
    base_t, k = tname, 2
    while tname.lower() in existing:
        tname, k = f"{base_t}{k}", k + 1
    for m in measures:
        agg = str(m.get("agg", "count")).lower()
        if agg not in AGG:
            raise OpError(f"Unknown summary '{agg}'. Use count, sum, average, min or max.")
        heads.append(m.get("header") or (f"Count" if agg == "count" else f"{agg.title()} of {m['column']}"))
    title_row = 1
    ws.cell(title_row, 1, op.get("title") or f"Summary of {src.name} by {heads[0]}").font = Font(bold=True, size=13, color="1F4E78")
    hr = title_row + 2
    for j, h in enumerate(heads, start=1):
        ws.cell(hr, j, h)
    for i, gv in enumerate(groups):
        r = hr + 1 + i
        ws.cell(r, 1, gv)
        for j, m in enumerate(measures, start=2):
            agg = str(m.get("agg", "count")).lower()
            crit = f"{tname}[[#This Row],[{heads[0]}]]"
            if agg == "count":
                f = f"=COUNTIFS({grng},{crit})"
            else:
                vr = _range_for(src, m["column"])
                f = f"=IFERROR({AGG[agg]}({vr},{grng},{crit}),0)" if agg != "sum" else f"=SUMIFS({vr},{grng},{crit})"
            cell = ws.cell(r, j, f)
            cell.number_format = _fmt(m.get("number_format")) or ("#,##0" if agg == "count" else "#,##0.00")
    last = hr + max(1, len(groups))
    ref = f"A{hr}:{get_column_letter(len(heads))}{last}"
    t = Table(displayName=tname, ref=ref)
    t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    t.autoFilter = AutoFilter(ref=ref)
    t.tableColumns = [TableColumn(id=i + 1, name=h) for i, h in enumerate(heads)]
    for j, tc in enumerate(t.tableColumns[1:], start=2):
        first_formula = ws.cell(hr + 1, j).value
        if _is_formula(first_formula):
            tc.calculatedColumnFormula = TableFormula(attr_text=first_formula[1:])
    ws.add_table(t)
    total_row = last + 1
    ws.cell(total_row, 1, "Total").font = Font(bold=True)
    for j, m in enumerate(measures, start=2):
        if str(m.get("agg", "count")).lower() in ("count", "sum"):
            letter = get_column_letter(j)
            c = ws.cell(total_row, j, f"=SUM({letter}{hr + 1}:{letter}{last})")
            c.font = Font(bold=True)
            c.number_format = ws.cell(hr + 1, j).number_format
    for j, h in enumerate(heads, start=1):
        ws.column_dimensions[get_column_letter(j)].width = max(14, min(len(str(h)) + 6, 40))
    if op.get("chart"):
        _chart(ws, ws, op["chart"], f"{heads[1]} by {heads[0]}", 1, [2], hr, last, f"{get_column_letter(len(heads) + 2)}{hr}")
    note = "" if choices else " (if new categories appear later, ask for the summary to be refreshed)"
    return (f"Created a live summary on '{name}': {', '.join(heads[1:])} by {heads[0]} for {len(groups)} group(s) "
            f"- it recalculates when {src.name} changes{note}")


def _chart(ws_target, ws_data, kind, title, cat_col, val_cols, header_row, last_row, anchor):
    kind = str(kind).lower()
    if kind in ("column", "bar", True, "true"):
        chart = BarChart()
        chart.type = "bar" if kind == "bar" else "col"
    elif kind == "line":
        chart = LineChart()
    elif kind == "pie":
        chart = PieChart()
    else:
        raise OpError("Chart type must be column, bar, line or pie.")
    chart.title = title
    chart.width, chart.height = 16, 8
    for vc in val_cols:
        chart.add_data(Reference(ws_data, min_col=vc, min_row=header_row, max_row=last_row), titles_from_data=True)
    chart.set_categories(Reference(ws_data, min_col=cat_col, min_row=header_row + 1, max_row=last_row))
    if len(val_cols) == 1 and kind != "pie":
        chart.legend = None
    ws_target.add_chart(chart, anchor)
    return chart


def op_add_chart(ctx, op):
    cat = op.get("category")
    vals = op.get("values") or []
    if not cat or not vals:
        raise OpError("A chart needs a category column (labels) and at least one values column.")
    src = find_region(ctx.wb, op.get("source_sheet") or op.get("sheet"), op.get("source_table") or op.get("table"), cat)
    target = find_sheet(ctx.wb, op["target_sheet"]) if op.get("target_sheet") and op["target_sheet"] in ctx.wb.sheetnames else (
        ctx.wb.create_sheet(op["target_sheet"]) if op.get("target_sheet") else src.ws)
    if target.title in ctx.adlc_chart_sheets:
        name = "Charts"
        target = ctx.wb[name] if name in ctx.wb.sheetnames else ctx.wb.create_sheet(name)
        ctx.warnings.append("The chart was put on the 'Charts' sheet, because the dashboard's own charts are redrawn automatically.")
        op = dict(op, anchor=op.get("anchor") if op.get("target_sheet") == name else "A1")
    anchor = op.get("anchor") or f"{get_column_letter(src.c1 + 2)}{src.header_row}"
    title = op.get("title") or f"{', '.join(vals)} by {cat}"
    _chart(target, src.ws, op.get("type", "column"), title, src.col(cat), [src.col(v) for v in vals],
           src.header_row, max(src.last_row, src.header_row + 1), anchor)
    return f"Added a {op.get('type', 'column')} chart '{title}' on '{target.title}' at {anchor}"


# --------------------------------------------------------------------------- sheets and tables


def op_add_sheet(ctx, op):
    name = str(op.get("name") or "").strip()
    if not name or len(name) > 31 or re.search(r"[\[\]:*?/\\]", name):
        raise OpError("Sheet names need 1-31 characters and can't use [ ] : * ? / \\.")
    if name.lower() in (s.lower() for s in ctx.wb.sheetnames):
        raise OpError(f"There is already a sheet called '{name}'.")
    ws = ctx.wb.create_sheet(name)
    if op.get("after") and op["after"] in ctx.wb.sheetnames:
        ctx.wb.move_sheet(ws, offset=ctx.wb.sheetnames.index(op["after"]) + 1 - ctx.wb.sheetnames.index(name))
    for j, h in enumerate(op.get("headers") or [], start=1):
        ws.cell(1, j, h).font = Font(bold=True)
    return f"Added sheet '{name}'" + (f" with headings {', '.join(op['headers'])}" if op.get("headers") else "")


def op_rename_sheet(ctx, op):
    ws = find_sheet(ctx.wb, op.get("sheet"))
    old, new = ws.title, str(op.get("new_name") or "").strip()
    if not new or len(new) > 31 or re.search(r"[\[\]:*?/\\]", new):
        raise OpError("Sheet names need 1-31 characters and can't use [ ] : * ? / \\.")
    if new.lower() in (s.lower() for s in ctx.wb.sheetnames if s != old):
        raise OpError(f"There is already a sheet called '{new}'.")
    ws.title = new
    n = 0
    for sheet in ctx.wb.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if _is_formula(cell.value):
                    f = refs.rename_sheet_in_formula(cell.value, old, new)
                    if f != cell.value:
                        cell.value, n = f, n + 1
        for dv in sheet.data_validations.dataValidation:
            if dv.formula1 and "!" in dv.formula1:
                dv.formula1 = refs.rename_sheet_in_formula("=" + dv.formula1.lstrip("="), old, new)[1:]
        for chart in getattr(sheet, "_charts", []):
            for s in chart.series:
                for attr in ("val", "cat"):
                    data = getattr(s, attr, None)
                    for holder in (getattr(data, "numRef", None), getattr(data, "strRef", None)) if data else ():
                        if holder is not None and holder.f:
                            holder.f = refs.rename_sheet_in_formula("=" + holder.f, old, new)[1:]
    for name in list(ctx.wb.defined_names.keys()):
        dn = ctx.wb.defined_names[name]
        if dn.attr_text and "!" in dn.attr_text:
            dn.attr_text = refs.rename_sheet_in_formula("=" + dn.attr_text, old, new)[1:]
    ctx.sheet_renames[old] = new
    return f"Renamed sheet '{old}' to '{new}'" + (f" and updated {n} formula(s) that pointed at it" if n else "")


def op_delete_sheet(ctx, op):
    ws = find_sheet(ctx.wb, op.get("sheet"))
    if ws.title in GENERATED:
        raise OpError("That sheet is part of how the workbook remembers its structure and can't be deleted.")
    users = [f"{s.title}!{c.coordinate}" for s in ctx.wb.worksheets if s is not ws
             for row in s.iter_rows() for c in row if refs.references_sheet(c.value, ws.title)]
    if users and not op.get("force"):
        raise OpError(f"Formulas on other sheets use '{ws.title}' ({', '.join(users[:5])}). Deleting it would break them.")
    if len([s for s in ctx.wb.worksheets if s.sheet_state == "visible"]) <= 1:
        raise OpError("A workbook needs at least one visible sheet.")
    title = ws.title
    ctx.wb.remove(ws)
    return f"Deleted sheet '{title}'"


def op_convert_to_table(ctx, op):
    ws = find_sheet(ctx.wb, op.get("sheet")) if op.get("sheet") else ctx.wb.worksheets[0]
    if ws.tables:
        raise OpError(f"'{ws.title}' already has a table ({', '.join(ws.tables)}).")
    from .regions import detect_block

    if op.get("range"):
        c0, r0, c1, r1 = range_boundaries(op["range"])
        region = Region(ws, r0, c0, c1, r1)
    else:
        region = detect_block(ws)
        if region is None:
            raise OpError(f"I can't find a header row with data on '{ws.title}'.")
    for m in ws.merged_cells.ranges:
        if not (m.max_col < region.c0 or m.min_col > region.c1 or m.max_row < region.header_row or m.min_row > region.last_row):
            raise OpError(f"There are merged cells at {m} inside the data. Unmerge them first.")
    seen = set()
    for c in range(region.c0, region.c1 + 1):
        cell = ws.cell(region.header_row, c)
        h = re.sub(r"[\[\]#'\n]+", "-", str(cell.value or f"Column {c - region.c0 + 1}")).strip()
        base, k = h, 2
        while h.lower() in seen:
            h, k = f"{base} {k}", k + 1
        seen.add(h.lower())
        cell.value = h
    name = op.get("name") or "tbl" + "".join(p.capitalize() for p in re.split(r"[^A-Za-z0-9]+", ws.title) if p)
    existing = {t.lower() for s in ctx.wb.worksheets for t in s.tables}
    base, k = name, 2
    while name.lower() in existing:
        name, k = f"{base}{k}", k + 1
    last = max(region.last_row, region.header_row + 1)
    ref = f"{get_column_letter(region.c0)}{region.header_row}:{get_column_letter(region.c1)}{last}"
    t = Table(displayName=name, ref=ref)
    t.tableStyleInfo = TableStyleInfo(name=op.get("style", "TableStyleMedium2"), showRowStripes=True)
    t.autoFilter = AutoFilter(ref=ref)
    t.tableColumns = [TableColumn(id=i + 1, name=str(ws.cell(region.header_row, c).value))
                      for i, c in enumerate(range(region.c0, region.c1 + 1))]
    ws.add_table(t)
    if ws.auto_filter.ref:
        ws.auto_filter.ref = None
    return f"Turned {ref} on '{ws.title}' into an Excel table called {name} (filters, banded rows, auto-expanding formulas)"


OPS = {
    "insert_column": op_insert_column, "add_column": op_insert_column,
    "delete_column": op_delete_column, "remove_column": op_delete_column,
    "rename_column": op_rename_column,
    "add_rows": op_add_rows, "append_rows": op_add_rows,
    "update_rows": op_update_rows,
    "delete_rows": op_delete_rows,
    "sort": op_sort,
    "dedupe": op_dedupe, "remove_duplicates": op_dedupe,
    "find_replace": op_find_replace,
    "set_cells": op_set_cells,
    "fill_formula": op_fill_formula,
    "split_column": op_split_column,
    "combine_columns": op_combine_columns,
    "format": op_format,
    "conditional_format": op_conditional_format, "highlight": op_conditional_format,
    "add_validation": op_add_validation, "add_dropdown": op_add_validation,
    "freeze_panes": op_freeze_panes,
    "add_lookup_column": op_add_lookup_column,
    "add_summary": op_add_summary,
    "add_chart": op_add_chart,
    "add_sheet": op_add_sheet,
    "rename_sheet": op_rename_sheet,
    "delete_sheet": op_delete_sheet,
    "convert_to_table": op_convert_to_table,
}


def run(ctx, ops) -> list[str]:
    if isinstance(ops, dict):
        ops = ops.get("ops", [ops])
    if not ops:
        raise OpError("No changes were given.")
    out = []
    for i, op in enumerate(ops, start=1):
        fn = OPS.get(str(op.get("op", "")).lower())
        if fn is None:
            raise OpError(f"Change {i}: unknown operation '{op.get('op')}'. Available: {', '.join(sorted(set(OPS)))}.")
        try:
            out.append(fn(ctx, op))
        except (TargetError, structure.StructureError) as exc:
            raise OpError(str(exc)) from None
    return out
