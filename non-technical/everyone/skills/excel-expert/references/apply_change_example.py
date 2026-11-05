"""Worked example of the AI-safe (_ADLC) update protocol - plain openpyxl, no ADLC engine.

This is what the Laya Excel Expert agent does on AI-safe workbooks inside Code Interpreter, written out in
full. It is also run by tests/test_protocol_compat.py, which checks that a file changed
this way still passes the engine's validation. That keeps the skill's instructions and
the engine in step.

Example change: add a 'Priority' dropdown column at the right-hand end of the Actions
table and add one new action.

    python apply_change_example.py "Action Tracker.xlsx" "Action Tracker (changed).xlsx"
"""

import hashlib
import json
import sys
from copy import copy
from datetime import datetime

import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import range_boundaries
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import TableColumn


def read_adlc(wb):
    """Step 1: the hidden _ADLC sheet holds key/value rows; the spec is split over spec_1..spec_N."""
    ws = wb["_ADLC"]
    kv = {row[0].value: row[1].value for row in ws.iter_rows(min_row=2) if row[0].value}
    spec = json.loads("".join(kv[f"spec_{i}"] for i in range(1, int(kv["spec_parts"]) + 1)))
    return kv, spec


def find_table(wb, spec, key):
    for sheet in spec["sheets"]:
        for table in sheet["tables"]:
            if table["key"] == key:
                return wb[sheet["name"]], table
    raise KeyError(key)


def add_row(ws, tspec, values):
    """Step 4 (rows): write under the last row, copy styles from the row above, extend the table."""
    t = ws.tables[tspec["name"]]
    c0, r0, c1, r1 = range_boundaries(t.ref)
    new_r = r1 + 1
    if any(ws.cell(new_r, c).value is not None for c in range(c0, c1 + 1)):
        raise ValueError(f"Something is in row {new_r} under the table - move it first.")
    prefix = tspec["id_prefix"]
    numbers = [int(str(v)[len(prefix):]) for v in (ws.cell(r, c0).value for r in range(r0 + 1, r1 + 1))
               if str(v or "").startswith(prefix) and str(v)[len(prefix):].isdigit()]
    values = dict(values, ID=f"{prefix}{max(numbers, default=0) + 1:03d}")
    for i, col in enumerate(tspec["columns"]):
        cell = ws.cell(new_r, c0 + i)
        cell._style = copy(ws.cell(new_r - 1, c0 + i)._style)
        cell.value = col["formula"] if col["type"] == "formula" else values.get(col["header"])
    t.ref = t.autoFilter.ref = f"{get_column_letter(c0)}{r0}:{get_column_letter(c1)}{new_r}"
    return values["ID"]


def add_choice_column_at_end(ws, tspec, header, choices, fill):
    """Step 4 (new column): right-hand end only, header, extend ref, TableColumn, dropdown."""
    t = ws.tables[tspec["name"]]
    c0, r0, c1, r1 = range_boundaries(t.ref)
    new_c = c1 + 1
    if any(ws.cell(r, new_c).value is not None for r in range(r0, r1 + 1)):
        raise ValueError("The column to the right of the table is not empty.")
    ws.cell(r0, new_c, header)._style = copy(ws.cell(r0, c1)._style)
    for r in range(r0 + 1, r1 + 1):
        ws.cell(r, new_c, fill)
    t.ref = t.autoFilter.ref = f"{get_column_letter(c0)}{r0}:{get_column_letter(new_c)}{r1}"
    t.tableColumns.append(TableColumn(id=len(t.tableColumns) + 1, name=header))
    letter = get_column_letter(new_c)
    dv = DataValidation(type="list", formula1='"' + ",".join(choices) + '"', allow_blank=True)
    dv.add(f"{letter}{r0 + 1}:{letter}500")
    ws.add_data_validation(dv)
    key = header.lower().replace(" ", "_")
    tspec["columns"].append({"key": key, "header": header, "type": "choice", "choices": choices})


def write_record(wb, kv, spec, who, summary, changes):
    """Step 5: bump version, rewrite the spec and checksum, add a Change Log row, update README."""
    major, minor = str(kv["version"]).split(".")
    version = f"{major}.{int(minor) + 1}"
    text = json.dumps(spec, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    parts = [text[i:i + 30000] for i in range(0, len(text), 30000)]
    kv = {k: v for k, v in kv.items() if not (k.startswith("spec_") and k[5:].isdigit())}
    kv.update(version=version, updated=datetime.now().replace(microsecond=0).isoformat(), updated_by=who,
              spec_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(), spec_parts=str(len(parts)))
    kv.update({f"spec_{i}": p for i, p in enumerate(parts, 1)})
    ws = wb["_ADLC"]
    ws.delete_rows(2, ws.max_row)
    for r, (k, v) in enumerate(kv.items(), start=2):
        ws.cell(r, 1, k)
        cell = ws.cell(r, 2, str(v))
        cell.data_type = "s"

    log = wb["Change Log"]
    lt = log.tables["tblChangeLog"]
    c0, r0, c1, r1 = range_boundaries(lt.ref)
    row = [version, datetime.now().replace(microsecond=0), who, "Laya Excel Expert", summary,
           "\n".join(f"• {c}" for c in changes), ""]
    for i, v in enumerate(row):
        log.cell(r1 + 1, c0 + i, v)._style = copy(log.cell(r1, c0 + i)._style)
    lt.ref = lt.autoFilter.ref = f"{get_column_letter(c0)}{r0}:{get_column_letter(c1)}{r1 + 1}"

    readme = wb["README"]
    for r in range(1, readme.max_row + 1):
        label = readme.cell(r, 1).value
        if label == "Version":
            readme.cell(r, 2, version)
        elif label == "Last updated":
            readme.cell(r, 2, datetime.now().strftime("%Y-%m-%d %H:%M"))
    return version


def snapshot(wb):
    """Step 3/6: every value and formula outside README, Change Log and _ADLC."""
    return {(ws.title, c.coordinate): c.value for ws in wb.worksheets
            if ws.title not in ("README", "Change Log", "_ADLC")
            for row in ws.iter_rows() for c in row if c.value is not None}


def main(src, dst):
    wb = openpyxl.load_workbook(src)
    kv, spec = read_adlc(wb)
    before = snapshot(wb)
    ws, tspec = find_table(wb, spec, "actions")
    new_id = add_row(ws, tspec, {"Action": "Order new headsets", "Owner": "Aoife",
                                 "Due date": datetime(2026, 10, 31), "Status": "Not started"})
    add_choice_column_at_end(ws, tspec, "Priority", ["High", "Medium", "Low"], "Medium")
    version = write_record(wb, kv, spec, "Aoife", "Added Priority and one action",
                           ["Added column 'Priority' (High, Medium, Low)", f"Added {new_id}"])
    wb.save(dst)
    after = snapshot(openpyxl.load_workbook(dst))
    changed = sorted(f"{s}!{c}" for s, c in set(before) | set(after) if before.get((s, c)) != after.get((s, c)))
    print(json.dumps({"version": version, "new_id": new_id, "changed": changed}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
