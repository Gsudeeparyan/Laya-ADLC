"""Insert and delete rows/columns the way Excel does: everything that points at moved cells follows.

openpyxl's insert_cols / delete_rows only move the cells. Here we also fix:
formulas on every sheet, Excel Tables (ranges and columns), data validation, conditional
formatting, merged cells, defined names, chart series and positions, freeze panes,
auto-filter, and column widths / row heights.
"""

from __future__ import annotations

import copy

from openpyxl.formatting.formatting import ConditionalFormattingList
from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import range_boundaries
from openpyxl.worksheet.table import TableColumn

from .refs import REF_ERROR, shift_address, shift_formula, shift_sqref


class StructureError(ValueError):
    pass


def insert_cols(wb, ws, at: int, n: int = 1, headers: list[str] | None = None):
    _shift(wb, ws, "col", at, n, headers)


def delete_cols(wb, ws, at: int, n: int = 1):
    _shift(wb, ws, "col", at, -n)


def insert_rows(wb, ws, at: int, n: int = 1):
    _shift(wb, ws, "row", at, n)


def delete_rows(wb, ws, at: int, n: int = 1):
    _shift(wb, ws, "row", at, -n)


def _shift_dv_formula(f, host, target, axis, at, n):
    if not f or f.startswith('"') or f.replace(".", "", 1).lstrip("-").isdigit():
        return f
    had_eq = f.startswith("=")
    new = shift_formula(f if had_eq else "=" + f, host, target, axis, at, n)
    return new if had_eq else new[1:]


def _tables(wb, ws, axis, at, n, headers):
    for name, t in list(((t.displayName, t) for t in ws.tables.values())):
        c0, r0, c1, r1 = range_boundaries(t.ref)
        cols = list(t.tableColumns)
        if axis == "col":
            if n > 0 and c0 < at <= c1:
                pos = at - c0
                existing = {c.name.lower() for c in cols}
                new_cols = []
                for k in range(n):
                    label = (headers[k] if headers and k < len(headers) else None) or f"Column{len(cols) + k + 1}"
                    base, i = label, 2
                    while label.lower() in existing:
                        label, i = f"{base} {i}", i + 1
                    existing.add(label.lower())
                    new_cols.append(TableColumn(id=0, name=label))
                cols[pos:pos] = new_cols
                c1 += n
            elif n > 0 and at <= c0:
                c0, c1 = c0 + n, c1 + n
            elif n < 0:
                end = at - n - 1
                lo, hi = max(c0, at), min(c1, end)
                if lo <= hi:
                    if lo == c0 and hi == c1:
                        del ws.tables[name]
                        continue
                    del cols[lo - c0:hi - c0 + 1]
                span = shift_address(f"{get_column_letter(c0)}1:{get_column_letter(c1)}1", "col", at, n)
                c0, _, c1, _ = range_boundaries(span)
        else:
            if n < 0:
                end = at - n - 1
                if at <= r0 <= end:
                    raise StructureError(f"That would delete the header row of table {name}.")
            span = shift_address(f"A{r0}:A{r1}", "row", at, n)
            if span == REF_ERROR:
                del ws.tables[name]
                continue
            _, r0, _, r1 = range_boundaries(span)
            r1 = max(r1, r0 + 1)
        for i, col in enumerate(cols, start=1):
            col.id = i
        t.tableColumns = cols
        t.ref = f"{get_column_letter(c0)}{r0}:{get_column_letter(c1)}{r1}"
        if t.autoFilter is not None:
            t.autoFilter.ref = t.ref
        if axis == "col" and n > 0 and c0 <= at <= c1:
            # Excel needs a text header in every table column.
            for k, col in enumerate(cols):
                cell = ws.cell(r0, c0 + k)
                if cell.value in (None, ""):
                    cell.value = col.name


def _dims(ws, axis, at, n):
    if axis == "col":
        widths = {}
        for letter, dim in list(ws.column_dimensions.items()):
            from openpyxl.utils import column_index_from_string

            widths[column_index_from_string(letter)] = dim.width
        new = {}
        for idx, w in widths.items():
            j = idx + n if idx >= at and n > 0 else idx
            if n < 0:
                end = at - n - 1
                if at <= idx <= end:
                    continue
                if idx > end:
                    j = idx + n
            new[j] = w
        for letter in list(ws.column_dimensions.keys()):
            del ws.column_dimensions[letter]
        for idx, w in new.items():
            if w:
                ws.column_dimensions[get_column_letter(idx)].width = w
    else:
        heights = {idx: d.height for idx, d in ws.row_dimensions.items() if d.height}
        for idx in list(heights):
            ws.row_dimensions[idx].height = None
        for idx, h in heights.items():
            j = idx
            if n > 0 and idx >= at:
                j = idx + n
            elif n < 0:
                end = at - n - 1
                if at <= idx <= end:
                    continue
                if idx > end:
                    j = idx + n
            ws.row_dimensions[j].height = h


def _anchor(obj, axis, at, n):
    anchor = getattr(obj, "anchor", None)
    if isinstance(anchor, str):
        new = shift_address(anchor, axis, at, max(n, 0) if n > 0 else n)
        if new != REF_ERROR:
            obj.anchor = new
        return
    marker = getattr(anchor, "_from", None)
    if marker is None:
        return
    for m in (marker, getattr(anchor, "to", None)):
        if m is None:
            continue
        idx = (m.col if axis == "col" else m.row) + 1
        new = idx + n if (n > 0 and idx >= at) else (max(at, idx + n) if n < 0 and idx >= at else idx)
        if axis == "col":
            m.col = new - 1
        else:
            m.row = new - 1


def _chart_refs(chart, host, target, axis, at, n):
    def fix(ref_holder):
        if ref_holder is not None and getattr(ref_holder, "f", None):
            ref_holder.f = shift_formula("=" + ref_holder.f, host, target, axis, at, n)[1:]

    for s in getattr(chart, "series", []) or []:
        for attr in ("val", "cat", "xVal", "yVal"):
            data = getattr(s, attr, None)
            if data is not None:
                fix(getattr(data, "numRef", None))
                fix(getattr(data, "strRef", None))
        tx = getattr(s, "tx", None)
        if tx is not None:
            fix(getattr(tx, "strRef", None))


def _shift(wb, ws, axis, at, n, headers=None):
    target = ws.title
    _tables(wb, ws, axis, at, n, headers)
    merged = [str(m) for m in ws.merged_cells.ranges]
    for m in merged:
        ws.unmerge_cells(m)

    if axis == "col":
        ws.insert_cols(at, n) if n > 0 else ws.delete_cols(at, -n)
    else:
        ws.insert_rows(at, n) if n > 0 else ws.delete_rows(at, -n)

    for m in merged:
        new = shift_address(m, axis, at, n)
        if new != REF_ERROR and ":" in new:
            ws.merge_cells(new)

    for sheet in wb.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and cell.value.startswith("="):
                    cell.value = shift_formula(cell.value, sheet.title, target, axis, at, n)
        for dv in list(sheet.data_validations.dataValidation):
            if sheet is ws:
                new = shift_sqref(dv.sqref, axis, at, n)
                if not new:
                    sheet.data_validations.dataValidation.remove(dv)
                    continue
                dv.sqref = new
            dv.formula1 = _shift_dv_formula(dv.formula1, sheet.title, target, axis, at, n)
            dv.formula2 = _shift_dv_formula(dv.formula2, sheet.title, target, axis, at, n)
        rebuilt = ConditionalFormattingList()
        for cf in sheet.conditional_formatting:
            sqref = shift_sqref(cf.sqref, axis, at, n) if sheet is ws else str(cf.sqref)
            if not sqref:
                continue
            for rule in cf.rules:
                rule = copy.copy(rule)
                if rule.formula:
                    rule.formula = [shift_formula("=" + f, sheet.title, target, axis, at, n)[1:] for f in rule.formula]
                rebuilt.add(sqref, rule)
        sheet.conditional_formatting = rebuilt
        for chart in getattr(sheet, "_charts", []):
            _chart_refs(chart, sheet.title, target, axis, at, n)
            if sheet is ws:
                _anchor(chart, axis, at, n)
        if sheet is ws:
            for img in getattr(sheet, "_images", []):
                _anchor(img, axis, at, n)

    for name in list(wb.defined_names.keys()):
        dn = wb.defined_names[name]
        if dn.attr_text and not dn.attr_text.startswith('"'):
            dn.attr_text = shift_formula("=" + dn.attr_text, target, target, axis, at, n)[1:] \
                if "!" in dn.attr_text else dn.attr_text

    if ws.freeze_panes:
        new = shift_address(ws.freeze_panes, axis, at, n)
        if new != REF_ERROR:
            ws.freeze_panes = new
    if ws.auto_filter and ws.auto_filter.ref:
        new = shift_address(ws.auto_filter.ref, axis, at, n)
        ws.auto_filter.ref = None if new == REF_ERROR else new
    _dims(ws, axis, at, n)
