"""AdlcWorkbook: build, open, change, validate and save self-describing workbooks."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook, load_workbook

from . import meta as meta_mod
from .charts import render_charts
from .render import (
    CHANGELOG_SHEET, DriftError, changelog_rows, check_room, coerce, order_sheets, read_rows,
    render_changelog, render_lists, render_readme, render_settings, summary_rows, write_table,
)
from .spec import find_column, find_table, id_column, iter_tables, prepare_spec, stored_spec


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def fill_ids(table: dict, rows: list[dict]) -> list[str]:
    """Give every row without an ID the next free one (ACT-001, ACT-002, ...). Returns new IDs."""
    idcol = id_column(table)
    if idcol is None:
        return []
    key, prefix = idcol["key"], table.get("id_prefix", "ROW-")
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$", re.IGNORECASE)
    numbers = [int(m.group(1)) for r in rows if (m := pattern.match(str(r.get(key) or "")))]
    next_no = max(numbers, default=0) + 1
    added = []
    for r in rows:
        if r.get(key) in (None, ""):
            r[key] = f"{prefix}{next_no:03d}"
            added.append(r[key])
            next_no += 1
    return added


def coerce_row(raw: dict, table: dict) -> dict:
    row = {}
    for k, v in (raw or {}).items():
        col = find_column(table, k)
        if col is None:
            raise ValueError(f"Unknown column '{k}' in table {table['name']}")
        if col["type"] == "formula":
            continue
        row[col["key"]] = coerce(v, col) if col["type"] != "id" else (None if v in (None, "") else str(v))
    return row


def ops_for_log(ops) -> list[dict]:
    """What goes in the Change Log's Technical details: structure in full, but never the
    values typed into rows (they may be personal data). Row changes record IDs and columns."""
    if isinstance(ops, dict):
        ops = ops.get("ops", [ops])
    logged = []
    for op in ops:
        op = dict(op)
        if "rows" in op:
            op["rows"] = f"{len(op['rows'])} row(s); values not logged"
        if isinstance(op.get("set"), dict):
            op["set"] = sorted(op["set"])
        if "fill_existing" in op:
            op["fill_existing"] = "(value not logged)"
        logged.append(op)
    return logged


@dataclass
class ChangeResult:
    version: str
    changes: list[str]
    affected: list[str]
    warnings: list[str] = field(default_factory=list)


class AdlcWorkbook:
    def __init__(self, wb, spec: dict, meta: dict, path: str | Path | None = None):
        self.wb = wb
        self.spec = spec
        self.meta = meta
        self.path = Path(path) if path else None

    # ------------------------------------------------------------------ create / open

    @classmethod
    def build(cls, spec: dict, *, owner: str | None = None, requested_by: str = "ADLC engine",
              tool: str = "ADLC engine") -> "AdlcWorkbook":
        full = prepare_spec(spec)
        seed = {t["key"]: [coerce_row(r, t) for r in t.get("rows", [])] for _, t in iter_tables(full)}
        stored = stored_spec(full)
        if owner:
            stored["workbook"]["owner"] = owner
        now = now_iso()
        meta = {
            "format_version": meta_mod.FORMAT_VERSION,
            "workbook_id": str(uuid.uuid4()),
            "template": stored["workbook"].get("template", ""),
            "title": stored["workbook"]["title"],
            "owner": stored["workbook"].get("owner", ""),
            "version": "1.0",
            "created": now,
            "updated": now,
            "updated_by": requested_by,
        }
        wb = Workbook()
        wb.remove(wb.active)
        awb = cls(wb, stored, meta)
        for sheet in stored["sheets"]:
            wb.create_sheet(sheet["name"])
        for sheet, table in iter_tables(stored):
            if "rows_from" in table:
                continue
            rows = seed[table["key"]]
            fill_ids(table, rows)
            write_table(wb, wb[sheet["name"]], table, rows)
        template = stored["workbook"].get("template")
        entry = {
            "version": "1.0",
            "date": datetime.now().replace(microsecond=0),
            "requested_by": requested_by,
            "tool": tool,
            "summary": "Workbook created" + (f" from the '{template}' template" if template else ""),
            "changes": "• Created sheets: " + ", ".join(s["name"] for s in stored["sheets"]),
            "details": "",
        }
        awb._finish(entry, param_overrides=None)
        return awb

    @classmethod
    def open(cls, path: str | Path) -> "AdlcWorkbook":
        wb = load_workbook(path)
        meta, spec = meta_mod.read_meta(wb)
        return cls(wb, spec, meta, path)

    def save(self, path: str | Path | None = None) -> Path:
        target = Path(path or self.path)
        self.wb.calculation.fullCalcOnLoad = True
        self.wb.save(target)
        self.path = target
        return target

    # ------------------------------------------------------------------ change

    def apply(self, ops: list[dict], *, requested_by: str = "", tool: str = "ADLC engine",
              summary: str | None = None) -> ChangeResult:
        """Apply change operations. Nothing in the workbook changes unless every op is valid."""
        from .ops import run_ops

        ctx = run_ops(self, ops)
        self.spec = ctx.spec
        for sheet in self.spec["sheets"]:
            if sheet["name"] not in self.wb.sheetnames:
                self.wb.create_sheet(sheet["name"])
        # Check every table has room to grow before writing anything.
        plan = []
        for key in sorted(ctx.dirty):
            sheet, table = find_table(self.spec, key)
            if "rows_from" in table:
                continue
            rows = ctx.rows(key)
            fill_ids(table, rows)
            check_room(self.wb[sheet["name"]], table, len(rows))
            plan.append((sheet, table, rows))
        for sheet, table, rows in plan:
            write_table(self.wb, self.wb[sheet["name"]], table, rows)

        self.meta["version"] = meta_mod.bump_version(self.meta.get("version"))
        self.meta["updated"] = now_iso()
        self.meta["updated_by"] = requested_by or "unknown"
        self.meta["title"] = self.spec["workbook"]["title"]
        self.meta["owner"] = self.spec["workbook"].get("owner", "")
        entry = {
            "version": self.meta["version"],
            "date": datetime.now().replace(microsecond=0),
            "requested_by": requested_by or "unknown",
            "tool": tool,
            "summary": summary or "; ".join(ctx.changes)[:250],
            "changes": "\n".join(f"• {c}" for c in ctx.changes),
            "details": json.dumps(ops_for_log(ops), ensure_ascii=False, default=str)[:30_000],
        }
        self._finish(entry, param_overrides=ctx.param_overrides)
        return ChangeResult(self.meta["version"], ctx.changes, ctx.affected, ctx.warnings)

    # ------------------------------------------------------------------ check

    def validate(self):
        from .validate import validate_workbook

        return validate_workbook(self.wb)

    # ------------------------------------------------------------------ internals

    def _render_summaries(self):
        for sheet, table in iter_tables(self.spec):
            if "rows_from" not in table:
                continue
            ws = self.wb[sheet["name"]]
            try:
                existing = read_rows(ws, table) if table["name"] in ws.tables else []
            except DriftError:
                existing = []
            write_table(self.wb, ws, table, summary_rows(self.spec, table, existing), freeze=False)

    def _finish(self, entry: dict, param_overrides):
        self._render_summaries()
        render_lists(self.wb, self.spec)
        render_settings(self.wb, self.spec, param_overrides)
        render_charts(self.wb, self.spec)
        log = changelog_rows(self.wb) if CHANGELOG_SHEET in self.wb.sheetnames else []
        log.append(entry)
        render_changelog(self.wb, log)
        render_readme(self.wb, self.spec, self.meta)
        meta_mod.write_meta(self.wb, self.meta, self.spec)
        order_sheets(self.wb, self.spec)
