"""Change operations ("ops"): the only way ADLC changes a workbook.

Each op is a small dict such as ``{"op": "add_column", "table": "actions", "column": {...}}``.
Ops are checked and applied to a copy of the spec and the table rows first. The workbook
is only re-written when every op succeeded, so a failed request never leaves a
half-changed file. The vocabulary is documented in docs/excel-continuity-pattern.md.
"""

from __future__ import annotations

import copy

from . import formulas
from .render import coerce, read_rows
from .spec import (
    CHART_TYPES, SpecError, find_column, find_sheet, find_table, iter_tables,
    prepare_column, prepare_table, validate_spec,
)


class OpError(ValueError):
    """A change could not be made. The message is written for a non-technical reader."""


class OpContext:
    def __init__(self, awb):
        self.awb = awb
        self.original = awb.spec
        self.spec = copy.deepcopy(awb.spec)
        self._rows: dict[str, list[dict]] = {}
        self.dirty: set[str] = set()
        self.new_tables: set[str] = set()
        self.param_overrides: set[str] = set()
        self.changes: list[str] = []
        self.affected: list[str] = []
        self.warnings: list[str] = []

    def rows(self, key: str) -> list[dict]:
        if key not in self._rows:
            if key in self.new_tables:
                self._rows[key] = []
            else:
                sheet, table = find_table(self.original, key)
                self._rows[key] = read_rows(self.awb.wb[sheet["name"]], table)
        return self._rows[key]

    def table(self, ref):
        sheet, table = find_table(self.spec, ref)
        if table is None:
            names = ", ".join(f"{t['key']} (sheet '{s['name']}')" for s, t in iter_tables(self.spec))
            raise OpError(f"I can't find a table called '{ref}'. Tables in this workbook: {names}.")
        return sheet, table

    @staticmethod
    def column(table, ref):
        col = find_column(table, ref)
        if col is None:
            headers = ", ".join(c["header"] for c in table["columns"])
            raise OpError(f"I can't find a column called '{ref}'. Columns: {headers}.")
        return col

    def touch(self, sheet, table, what=""):
        self.dirty.add(table["key"])
        self.affected.append(f"{sheet['name']} ({table['name']})" + (f": {what}" if what else ""))


def _need(op, *keys):
    missing = [k for k in keys if k not in op]
    if missing:
        raise OpError(f"The '{op.get('op')}' change is missing: {', '.join(missing)}.")


# --------------------------------------------------------------------------- columns


def op_add_column(ctx, op):
    _need(op, "table", "column")
    sheet, table = ctx.table(op["table"])
    col = prepare_column(table, dict(op["column"]))
    if find_column(table, col["key"]) or find_column(table, col["header"]):
        raise OpError(f"There is already a column called '{col['header']}' in '{sheet['name']}'.")
    if col["type"] == "id":
        raise OpError("A table can only have one ID column.")
    rows = ctx.rows(table["key"])
    position = len(table["columns"])
    after = op.get("after")
    has_a1 = any(c.get("formula_a1") for c in table["columns"])
    if after and has_a1:
        ctx.warnings.append("This table has older-style formulas, so the new column was added at the end.")
    elif after == "start":
        position = 1
    elif after:
        position = table["columns"].index(ctx.column(table, after)) + 1
    if "fill_existing" in op and col["type"] != "formula":
        value = coerce(op["fill_existing"], col)
        for r in rows:
            r[col["key"]] = value
    table["columns"].insert(position, col)
    ctx.touch(sheet, table, f"new column '{col['header']}'")
    calc = f" (worked out as {formulas.display(col['formula'], table['name'])})" if col.get("formula") else ""
    return f"Added column '{col['header']}' to '{sheet['name']}'{calc}"


def op_rename_column(ctx, op):
    _need(op, "table", "column", "header")
    sheet, table = ctx.table(op["table"])
    col = ctx.column(table, op["column"])
    old, new = col["header"], str(op["header"]).strip()
    if find_column(table, new) and find_column(table, new) is not col:
        raise OpError(f"There is already a column called '{new}' in '{sheet['name']}'.")
    ctx.rows(table["key"])
    col["header"] = new
    for s2, t2 in iter_tables(ctx.spec):
        for c2 in t2["columns"]:
            if c2.get("formula") and formulas.references_column(c2["formula"], table["name"], old):
                c2["formula"] = formulas.rename_column_refs(c2["formula"], table["name"], old, new)
                if "rows_from" not in t2:
                    ctx.rows(t2["key"])
                    ctx.touch(s2, t2, f"formula in '{c2['header']}' now uses '{new}'")
    ctx.touch(sheet, table, f"renamed '{old}' to '{new}'")
    return f"Renamed column '{old}' to '{new}' in '{sheet['name']}' (formulas that used it were updated)"


def _users_of(ctx, table, col):
    users = []
    for s2, t2 in iter_tables(ctx.spec):
        for c2 in t2["columns"]:
            if c2 is not col and c2.get("formula") and formulas.references_column(c2["formula"], table["name"], col["header"]):
                users.append(f"column '{c2['header']}' on '{s2['name']}'")
        rf = t2.get("rows_from")
        if rf and find_table(ctx.spec, rf["table"])[1] is table and find_column(table, rf["column"]) is col:
            users.append(f"the summary table on '{s2['name']}'")
    for s2 in ctx.spec["sheets"]:
        for ch in s2.get("charts", []):
            if find_table(ctx.spec, ch["table"])[1] is table and col["key"] in (
                [find_column(table, ch["category"])["key"]] + [find_column(table, v)["key"] for v in ch["values"]]
            ):
                users.append(f"the chart '{ch.get('title') or ch['key']}' on '{s2['name']}'")
    return users


def op_remove_column(ctx, op):
    _need(op, "table", "column")
    sheet, table = ctx.table(op["table"])
    col = ctx.column(table, op["column"])
    if col["type"] == "id":
        raise OpError("The ID column can't be removed: it is how rows are found when updating them.")
    users = _users_of(ctx, table, col)
    if users:
        raise OpError(f"'{col['header']}' can't be removed because it is used by: {'; '.join(users)}. Change or remove those first.")
    rows = ctx.rows(table["key"])
    table["columns"].remove(col)
    for r in rows:
        r.pop(col["key"], None)
    ctx.touch(sheet, table, f"removed '{col['header']}'")
    return f"Removed column '{col['header']}' from '{sheet['name']}'"


def op_set_formula(ctx, op):
    _need(op, "table", "column", "formula")
    sheet, table = ctx.table(op["table"])
    col = ctx.column(table, op["column"])
    rows = ctx.rows(table["key"])
    if col["type"] == "id":
        raise OpError("The ID column can't become a formula.")
    if col["type"] != "formula":
        typed = [r for r in rows if r.get(col["key"]) not in (None, "")]
        if typed and not op.get("force"):
            raise OpError(
                f"'{col['header']}' has {len(typed)} typed value(s). Turning it into a formula would replace them. "
                "Confirm with the person, then repeat with force: true."
            )
        for r in rows:
            r.pop(col["key"], None)
        col["type"] = "formula"
        col.pop("choices", None)
    col["formula"] = formulas.normalise(op["formula"], table["name"])
    col.pop("formula_a1", None)
    col.pop("formula_row", None)
    bad = formulas.dynamic_array_functions_used(col["formula"])
    if bad:
        raise OpError(f"{', '.join(bad)} can't be used in a table column because the result spills into other cells.")
    ctx.touch(sheet, table, f"formula for '{col['header']}'")
    return f"'{col['header']}' in '{sheet['name']}' is now worked out as {formulas.display(col['formula'], table['name'])}"


def op_set_choices(ctx, op):
    _need(op, "table", "column", "choices")
    sheet, table = ctx.table(op["table"])
    col = ctx.column(table, op["column"])
    if col["type"] == "yes_no":
        raise OpError(f"'{col['header']}' is a Yes/No column, so its options can't change.")
    if col["type"] != "choice":
        raise OpError(f"'{col['header']}' is not a dropdown column.")
    mode = op.get("mode", "replace")
    old = list(col.get("choices", []))
    given = [str(c) for c in op["choices"]]
    if mode == "add":
        new = old + [c for c in given if c.lower() not in (o.lower() for o in old)]
    elif mode == "remove":
        new = [c for c in old if c.lower() not in (g.lower() for g in given)]
    else:
        new = given
    if not new:
        raise OpError("A dropdown needs at least one option.")
    rows = ctx.rows(table["key"])
    allowed = {c.lower() for c in new}
    orphans = sorted({str(r[col["key"]]) for r in rows if r.get(col["key"]) not in (None, "") and str(r[col["key"]]).lower() not in allowed})
    if orphans and not op.get("force"):
        raise OpError(
            f"Some rows in '{sheet['name']}' still use {', '.join(repr(o) for o in orphans)} in '{col['header']}'. "
            "Update those rows first, or confirm with the person and repeat with force: true."
        )
    col["choices"] = new
    ctx.touch(sheet, table, f"options for '{col['header']}'")
    return f"Dropdown options for '{col['header']}' in '{sheet['name']}' are now: {', '.join(new)}"


def op_set_format(ctx, op):
    _need(op, "table", "column")
    sheet, table = ctx.table(op["table"])
    col = ctx.column(table, op["column"])
    ctx.rows(table["key"])
    changed = []
    for k in ("number_format", "width", "description", "required", "min", "max", "highlights"):
        if k in op:
            col[k] = op[k]
            changed.append(k.replace("_", " "))
    if not changed:
        raise OpError("Nothing to change: give number_format, width, description, required, min, max or highlights.")
    ctx.touch(sheet, table, f"format of '{col['header']}'")
    return f"Updated {', '.join(changed)} of '{col['header']}' in '{sheet['name']}'"


# --------------------------------------------------------------------------- rows


def _input_row(table, raw):
    row = {}
    for k, v in raw.items():
        col = find_column(table, k)
        if col is None:
            raise OpError(f"There is no column called '{k}' in table {table['name']}.")
        if col["type"] == "formula":
            raise OpError(f"'{col['header']}' is calculated automatically, so it can't be typed in.")
        try:
            row[col["key"]] = (None if v in (None, "") else str(v)) if col["type"] == "id" else coerce(v, col)
        except ValueError as exc:
            raise OpError(str(exc)) from None
    return row


def _id_key(ctx, table):
    idcol = next((c for c in table["columns"] if c["type"] == "id"), None)
    if idcol is None:
        raise OpError(f"Table {table['name']} has no ID column, so rows can't be matched.")
    return idcol["key"]


def _find_rows(ctx, table, ids):
    key = _id_key(ctx, table)
    rows = ctx.rows(table["key"])
    found = []
    for wanted in ids:
        match = [r for r in rows if str(r.get(key) or "").lower() == str(wanted).strip().lower()]
        if not match:
            raise OpError(f"There is no row with ID '{wanted}' in table {table['name']}.")
        found.extend(match)
    return found


def op_add_rows(ctx, op):
    _need(op, "table", "rows")
    sheet, table = ctx.table(op["table"])
    if "rows_from" in table:
        raise OpError("This summary table fills itself in from the dropdown options.")
    rows = ctx.rows(table["key"])
    key = _id_key(ctx, table)
    existing = {str(r.get(key) or "").lower() for r in rows}
    new_rows = [_input_row(table, raw) for raw in op["rows"]]
    for r in new_rows:
        if r.get(key) and str(r[key]).lower() in existing:
            raise OpError(f"A row with ID '{r[key]}' already exists.")
    rows.extend(new_rows)
    from .workbook import fill_ids

    fill_ids(table, rows)
    ids = [str(r[key]) for r in new_rows]
    ctx.touch(sheet, table, f"{len(new_rows)} new row(s)")
    return f"Added {len(new_rows)} row(s) to '{sheet['name']}': {', '.join(ids)}"


def op_update_rows(ctx, op):
    _need(op, "table", "set")
    sheet, table = ctx.table(op["table"])
    ids = op.get("ids") or ([op["id"]] if "id" in op else [])
    if not ids:
        raise OpError("Say which rows to update by their ID (for example ACT-004).")
    targets = _find_rows(ctx, table, ids)
    values = _input_row(table, op["set"])
    if _id_key(ctx, table) in values:
        raise OpError("IDs can't be changed: they are how rows are found.")
    for r in targets:
        r.update(values)
    what = ", ".join(f"{find_column(table, k)['header']} = {v if v is not None else '(blank)'}" for k, v in values.items())
    ctx.touch(sheet, table, f"updated {len(targets)} row(s)")
    return f"Updated {', '.join(map(str, ids))} in '{sheet['name']}': {what}"


def op_delete_rows(ctx, op):
    _need(op, "table", "ids")
    sheet, table = ctx.table(op["table"])
    targets = _find_rows(ctx, table, op["ids"])
    rows = ctx.rows(table["key"])
    for t in targets:
        rows.remove(t)
    ctx.touch(sheet, table, f"deleted {len(targets)} row(s)")
    return f"Deleted {', '.join(map(str, op['ids']))} from '{sheet['name']}'"


# --------------------------------------------------------------------------- structure


def op_add_table(ctx, op):
    _need(op, "sheet", "table")
    raw = dict(op["table"])
    seed = raw.pop("rows", [])
    table = prepare_table(raw)
    if find_table(ctx.spec, table["key"])[1] is not None:
        raise OpError(f"There is already a table called '{table['key']}'.")
    sheet = find_sheet(ctx.spec, op["sheet"])
    if sheet is None:
        sheet = {"name": op["sheet"], "description": op.get("sheet_description", ""), "tables": [], "charts": []}
        ctx.spec["sheets"].append(sheet)
    sheet["tables"].append(table)
    ctx.new_tables.add(table["key"])
    if "rows_from" not in table:
        ctx.rows(table["key"]).extend(_input_row(table, r) for r in seed)
    ctx.touch(sheet, table, "new table")
    return f"Added a new table '{table['name']}' on sheet '{sheet['name']}' with columns: " + ", ".join(
        c["header"] for c in table["columns"]
    )


def op_set_parameter(ctx, op):
    _need(op, "key", "value")
    params = ctx.spec.setdefault("parameters", [])
    p = next((x for x in params if x["key"] == op["key"]), None)
    if p is None:
        if "label" not in op:
            raise OpError(f"There is no setting called '{op['key']}'. To create one, also give a label.")
        p = {"key": op["key"], "label": op["label"], "type": op.get("type", "number"),
             "description": op.get("description", ""), "value": None}
        params.append(p)
    value = op["value"]
    if p["type"] in ("number", "integer", "currency", "percent"):
        try:
            value = coerce(value, {"type": p["type"], "header": p["label"]})
        except ValueError as exc:
            raise OpError(str(exc)) from None
    p["value"] = value
    ctx.param_overrides.add(p["key"])
    ctx.affected.append(f"Settings: {p['label']}")
    return f"Setting '{p['label']}' is now {value}"


def op_add_chart(ctx, op):
    _need(op, "sheet", "chart")
    sheet = find_sheet(ctx.spec, op["sheet"])
    if sheet is None:
        raise OpError(f"There is no sheet called '{op['sheet']}'.")
    chart = {"type": "column", "anchor": "H2", "width": 16, "height": 8, "title": ""}
    chart.update(op["chart"])
    chart.setdefault("key", f"chart_{len(sheet.get('charts', [])) + 1}")
    if chart["type"] not in CHART_TYPES:
        raise OpError(f"Chart type must be one of: {', '.join(CHART_TYPES)}.")
    sheet.setdefault("charts", []).append(chart)
    ctx.affected.append(f"{sheet['name']}: chart")
    return f"Added a {chart['type']} chart '{chart.get('title') or chart['key']}' to '{sheet['name']}'"


def op_remove_chart(ctx, op):
    _need(op, "sheet", "chart")
    sheet = find_sheet(ctx.spec, op["sheet"])
    charts = sheet.get("charts", []) if sheet else []
    match = [c for c in charts if op["chart"] in (c.get("key"), c.get("title"))]
    if not match:
        raise OpError(f"There is no chart '{op['chart']}' on '{op['sheet']}'.")
    charts.remove(match[0])
    ctx.affected.append(f"{sheet['name']}: chart removed")
    return f"Removed the chart '{op['chart']}' from '{sheet['name']}'"


def op_set_workbook_info(ctx, op):
    info = ctx.spec["workbook"]
    changed = []
    for k in ("title", "purpose", "owner", "how_to_use"):
        if k in op:
            info[k] = op[k]
            changed.append(k.replace("_", " "))
    if not changed:
        raise OpError("Nothing to change: give title, purpose, owner or how_to_use.")
    ctx.affected.append("README")
    return f"Updated the workbook's {', '.join(changed)}"


OPS = {
    "add_column": op_add_column,
    "rename_column": op_rename_column,
    "remove_column": op_remove_column,
    "set_formula": op_set_formula,
    "set_choices": op_set_choices,
    "set_format": op_set_format,
    "update_column": op_set_format,
    "add_rows": op_add_rows,
    "update_rows": op_update_rows,
    "delete_rows": op_delete_rows,
    "add_table": op_add_table,
    "set_parameter": op_set_parameter,
    "add_chart": op_add_chart,
    "remove_chart": op_remove_chart,
    "set_workbook_info": op_set_workbook_info,
}


def run_ops(awb, ops: list[dict]) -> OpContext:
    if isinstance(ops, dict):
        ops = ops.get("ops", [ops])
    if not ops:
        raise OpError("No changes were given.")
    ctx = OpContext(awb)
    for i, op in enumerate(ops, start=1):
        handler = OPS.get(op.get("op"))
        if handler is None:
            raise OpError(f"Change {i} has an unknown op '{op.get('op')}'. Known ops: {', '.join(OPS)}.")
        ctx.changes.append(handler(ctx, op))
    errors = validate_spec(ctx.spec)
    if errors:
        raise OpError("These changes would break the workbook's structure:\n- " + "\n- ".join(errors))
    return ctx


__all__ = ["OPS", "OpContext", "OpError", "run_ops", "SpecError"]
