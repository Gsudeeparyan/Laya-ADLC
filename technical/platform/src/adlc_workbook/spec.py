"""Workbook spec: the single source of truth for a workbook's structure.

A spec is a plain dict (authored as YAML, stored as JSON inside the workbook). It describes
sheets, Excel Tables, columns, formulas, dropdown choices, settings and charts. It never
holds the business data itself - that lives in the workbook. See
docs/excel-continuity-pattern.md for the full format.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import yaml
from openpyxl.utils.cell import coordinate_from_string, column_index_from_string

from . import formulas

SPEC_VERSION = 1

COLUMN_TYPES = (
    "id", "text", "long_text", "number", "integer", "currency", "percent",
    "date", "choice", "yes_no", "formula",
)
INPUT_TYPES = tuple(t for t in COLUMN_TYPES if t not in ("id", "formula"))
CHART_TYPES = ("column", "bar", "pie", "line")
COLOURS = ("green", "amber", "red", "grey", "blue")
HIGHLIGHT_CONDITIONS = (
    "equals", "not_equals", "less_than", "greater_than", "less_or_equal",
    "greater_or_equal", "blank", "not_blank", "contains",
)
RESERVED_SHEETS = ("README", "Settings", "Change Log", "_ADLC", "_Lists")

_SHEET_BAD = re.compile(r"[\[\]:*?/\\]")
_HEADER_BAD = re.compile(r"[\[\]#'\n\r\t]")
# New tables are named tblSomething; adopted workbooks may keep names like "Table1".
_TABLE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]{0,250}$")
_KEY = re.compile(r"^[a-z][a-z0-9_]*$")


class SpecError(ValueError):
    """Raised when a spec is invalid. ``errors`` holds every problem found."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Invalid workbook spec:\n- " + "\n- ".join(errors))


# --------------------------------------------------------------------------- loading


def load_spec(path: str | Path) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    data = json.loads(text) if str(path).endswith(".json") else yaml.safe_load(text)
    return prepare_spec(data)


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", str(text).strip().lower()).strip("_")
    if not s or not s[0].isalpha():
        s = "c_" + s
    return s


def _camel(text: str) -> str:
    return "".join(p.capitalize() for p in re.split(r"[^A-Za-z0-9]+", str(text)) if p)


def prepare_spec(raw: dict) -> dict:
    """Fill defaults, normalise formulas and validate. Returns a new dict."""
    spec = copy.deepcopy(raw or {})
    spec.setdefault("adlc_spec", SPEC_VERSION)
    spec.setdefault("workbook", {})
    wbinfo = spec["workbook"]
    wbinfo.setdefault("title", "Untitled workbook")
    wbinfo.setdefault("purpose", "")
    wbinfo.setdefault("owner", "")
    wbinfo.setdefault("how_to_use", [])
    spec.setdefault("parameters", [])
    spec.setdefault("sheets", [])

    for p in spec["parameters"]:
        p.setdefault("type", "number")
        p.setdefault("description", "")
        p.setdefault("label", p.get("key", ""))

    for sheet in spec["sheets"]:
        sheet.setdefault("description", "")
        sheet.setdefault("tables", [])
        sheet.setdefault("charts", [])
        for table in sheet["tables"]:
            prepare_table(table)
        for chart in sheet["charts"]:
            chart.setdefault("type", "column")
            chart.setdefault("anchor", "H2")
            chart.setdefault("width", 16)
            chart.setdefault("height", 8)
            chart.setdefault("title", "")

    errors = validate_spec(spec)
    if errors:
        raise SpecError(errors)
    return spec


def prepare_table(table: dict) -> dict:
    key = table.get("key") or slug(table.get("name", "table").removeprefix("tbl"))
    table["key"] = key
    table.setdefault("name", "tbl" + _camel(key))
    table.setdefault("anchor", "A1")
    table.setdefault("style", "TableStyleMedium2")
    table.setdefault("columns", [])
    is_summary = "rows_from" in table
    if not is_summary and not any(c.get("type") == "id" for c in table["columns"]):
        table["columns"].insert(0, {"key": "id", "header": "ID", "type": "id"})
    if not is_summary:
        table.setdefault("id_prefix", (re.sub(r"[^A-Z]", "", key.upper())[:3] or "ROW") + "-")
    for col in table["columns"]:
        prepare_column(table, col)
    return table


def prepare_column(table: dict, col: dict) -> dict:
    col.setdefault("header", col.get("key", ""))
    col.setdefault("key", slug(col["header"]))
    col.setdefault("type", "text")
    col.setdefault("required", False)
    col.setdefault("description", "")
    if col["type"] == "yes_no":
        col["choices"] = ["Yes", "No"]
    if col["type"] == "formula" and col.get("formula"):
        col["formula"] = formulas.normalise(col["formula"], table["name"])
    return col


# --------------------------------------------------------------------------- validation


def _anchor_ok(anchor: str) -> bool:
    try:
        coordinate_from_string(anchor)
        return True
    except Exception:
        return False


def validate_spec(spec: dict) -> list[str]:
    """Return a list of human-readable problems. Empty list means the spec is valid."""
    errors: list[str] = []
    if spec.get("adlc_spec") != SPEC_VERSION:
        errors.append(f"adlc_spec must be {SPEC_VERSION}")
    if not str(spec.get("workbook", {}).get("title", "")).strip():
        errors.append("workbook.title is required")

    param_keys = set()
    for p in spec.get("parameters", []):
        k = p.get("key", "")
        if not _KEY.match(str(k)):
            errors.append(f"parameter key '{k}' must be lower_snake_case")
        if k in param_keys:
            errors.append(f"parameter '{k}' is defined twice")
        param_keys.add(k)
        if p.get("type") not in ("number", "integer", "currency", "percent", "text", "date"):
            errors.append(f"parameter '{k}' has unsupported type '{p.get('type')}'")

    sheet_names = set()
    table_names = set()
    table_keys = set()
    tables_by_key = {}
    for sheet in spec.get("sheets", []):
        name = str(sheet.get("name", ""))
        if not name.strip():
            errors.append("every sheet needs a name")
            continue
        if len(name) > 31 or _SHEET_BAD.search(name):
            errors.append(f"sheet name '{name}' must be 31 characters or fewer without [ ] : * ? / \\")
        if name.lower() in (s.lower() for s in RESERVED_SHEETS):
            errors.append(f"sheet name '{name}' is reserved by ADLC")
        if name.lower() in sheet_names:
            errors.append(f"sheet name '{name}' is used twice")
        sheet_names.add(name.lower())

        variable_tables = 0
        bands = []
        for table in sheet.get("tables", []):
            tname = table.get("name", "")
            if not _TABLE_NAME.match(tname):
                errors.append(f"table name '{tname}' must use only letters, digits or _ (new tables start with 'tbl')")
            if tname.lower() in table_names:
                errors.append(f"table name '{tname}' is used twice")
            table_names.add(tname.lower())
            if table["key"] in table_keys:
                errors.append(f"table key '{table['key']}' is used twice")
            table_keys.add(table["key"])
            tables_by_key[table["key"]] = table
            if not _anchor_ok(table.get("anchor", "A1")):
                errors.append(f"table '{tname}' has an invalid anchor '{table.get('anchor')}'")
            if "rows_from" not in table and not table.get("static"):
                variable_tables += 1
            col0 = column_index_from_string(coordinate_from_string(table.get("anchor", "A1"))[0]) if _anchor_ok(table.get("anchor", "A1")) else 1
            bands.append((col0, col0 + len(table.get("columns", [])) - 1, tname))
            errors.extend(_validate_columns(table))
        if variable_tables > 1:
            errors.append(f"sheet '{name}' has more than one growing table; give each its own sheet")
        bands.sort()
        for (a1, a2, n1), (b1, b2, n2) in zip(bands, bands[1:]):
            if b1 <= a2 + 1:
                errors.append(f"tables '{n1}' and '{n2}' on sheet '{name}' overlap or touch; leave a blank column between them")

    for sheet in spec.get("sheets", []):
        for table in sheet.get("tables", []):
            rf = table.get("rows_from")
            if rf:
                src = tables_by_key.get(rf.get("table"))
                col = find_column(src, rf.get("column")) if src else None
                if not col or not col.get("choices"):
                    errors.append(f"table '{table['name']}' rows_from must point at a choice column of another table")
                if not table.get("columns") or table["columns"][0].get("type") == "formula":
                    errors.append(f"table '{table['name']}' first column holds the category and must not be a formula")
        for chart in sheet.get("charts", []):
            src = tables_by_key.get(chart.get("table"))
            if chart.get("type") not in CHART_TYPES:
                errors.append(f"chart '{chart.get('key')}' type must be one of {', '.join(CHART_TYPES)}")
            if not src:
                errors.append(f"chart '{chart.get('key')}' points at unknown table '{chart.get('table')}'")
                continue
            for ck in [chart.get("category")] + list(chart.get("values", [])):
                if not find_column(src, ck):
                    errors.append(f"chart '{chart.get('key')}' points at unknown column '{ck}'")
            if not chart.get("values"):
                errors.append(f"chart '{chart.get('key')}' needs at least one values column")
            if not _anchor_ok(chart.get("anchor", "H2")):
                errors.append(f"chart '{chart.get('key')}' has an invalid anchor")
    return errors


def _validate_columns(table: dict) -> list[str]:
    errors = []
    tname = table.get("name", "?")
    cols = table.get("columns", [])
    if not cols:
        errors.append(f"table '{tname}' has no columns")
    keys, headers = set(), set()
    ids = 0
    for col in cols:
        k, h, t = col.get("key", ""), str(col.get("header", "")), col.get("type")
        if not _KEY.match(str(k)):
            errors.append(f"column key '{k}' in '{tname}' must be lower_snake_case")
        if k in keys:
            errors.append(f"column key '{k}' is used twice in '{tname}'")
        keys.add(k)
        if not h.strip() or _HEADER_BAD.search(h):
            errors.append(f"column header '{h}' in '{tname}' must not be blank or contain [ ] # ' or line breaks")
        if h.lower() in headers:
            errors.append(f"column header '{h}' is used twice in '{tname}'")
        headers.add(h.lower())
        if t not in COLUMN_TYPES:
            errors.append(f"column '{h}' in '{tname}' has unknown type '{t}'")
        if t == "id":
            ids += 1
        if t == "choice" and not col.get("choices"):
            errors.append(f"choice column '{h}' in '{tname}' needs a list of choices")
        if t == "formula":
            if not col.get("formula") and not col.get("formula_a1"):
                errors.append(f"formula column '{h}' in '{tname}' needs a formula")
            else:
                bad = formulas.dynamic_array_functions_used(col.get("formula") or col["formula_a1"])
                if bad:
                    errors.append(f"formula column '{h}' uses {', '.join(bad)}, which spills outside the table")
        for hl in col.get("highlights", []):
            if hl.get("when") not in HIGHLIGHT_CONDITIONS:
                errors.append(f"highlight on '{h}' has unknown condition '{hl.get('when')}'")
            if hl.get("color", "green") not in COLOURS:
                errors.append(f"highlight on '{h}' has unknown color '{hl.get('color')}'")
    if "rows_from" not in table and not table.get("static") and ids != 1:
        errors.append(f"table '{tname}' must have exactly one id column")
    return errors


# --------------------------------------------------------------------------- accessors


def iter_tables(spec: dict):
    for sheet in spec.get("sheets", []):
        for table in sheet.get("tables", []):
            yield sheet, table


def find_table(spec: dict, ref: str):
    """Find a table by key, name or sheet name. Returns (sheet, table) or (None, None)."""
    ref_l = str(ref).strip().lower()
    for sheet, table in iter_tables(spec):
        if ref_l in (table["key"].lower(), table["name"].lower()):
            return sheet, table
    for sheet, table in iter_tables(spec):
        if ref_l == sheet["name"].lower():
            return sheet, table
    return None, None


def find_column(table: dict | None, ref: str | None):
    if not table or ref is None:
        return None
    ref_l = str(ref).strip().lower()
    for col in table.get("columns", []):
        if ref_l in (col["key"].lower(), str(col["header"]).lower()):
            return col
    return None


def id_column(table: dict):
    return next((c for c in table["columns"] if c["type"] == "id"), None)


def find_sheet(spec: dict, name: str):
    return next((s for s in spec["sheets"] if s["name"].lower() == str(name).lower()), None)


def normalise_loaded(spec: dict) -> dict:
    """Tidy a spec read from a workbook without changing its structure.

    Copilot agents write the _ADLC spec themselves, so it may use the [@Column] shorthand
    or leave out defaults. This fills harmless defaults and normalises formulas so the
    engine compares like with like. It never adds or removes columns.
    """
    spec.setdefault("adlc_spec", SPEC_VERSION)
    spec.setdefault("workbook", {}).setdefault("title", "Untitled workbook")
    spec["workbook"].setdefault("how_to_use", [])
    spec.setdefault("parameters", [])
    for p in spec["parameters"]:
        p.setdefault("type", "number")
        p.setdefault("label", p.get("key", ""))
        p.setdefault("description", "")
    for sheet in spec.setdefault("sheets", []):
        sheet.setdefault("description", "")
        sheet.setdefault("charts", [])
        for table in sheet.setdefault("tables", []):
            table.setdefault("anchor", "A1")
            table.setdefault("style", "TableStyleMedium2")
            table.setdefault("columns", [])
            for col in table["columns"]:
                col.setdefault("header", col.get("key", ""))
                col.setdefault("key", slug(col["header"]))
                col.setdefault("type", "text")
                col.setdefault("required", False)
                col.setdefault("description", "")
                if col["type"] == "yes_no" and not col.get("choices"):
                    col["choices"] = ["Yes", "No"]
                if col["type"] == "formula" and col.get("formula"):
                    col["formula"] = formulas.normalise(col["formula"], table.get("name", ""))
    return spec


def stored_spec(spec: dict) -> dict:
    """The spec as kept inside the workbook: structure only, no seed rows."""
    out = copy.deepcopy(spec)
    for _, table in iter_tables(out):
        table.pop("rows", None)
    return out


def dump_yaml(spec: dict) -> str:
    return yaml.safe_dump(spec, sort_keys=False, allow_unicode=True, width=100)
