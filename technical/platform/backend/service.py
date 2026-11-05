"""The SharePoint Excel Expert service: what each Copilot action does.

The PII firewall lives here. Copilot only ever receives tokens (PERSON_001, PPSN_002...).
Real values stay in SharePoint and in the server-side vault. When Copilot sends changes
back that contain tokens, they are swapped for the real values just before the workbook
is written. Kept free of Azure Functions code so it can be unit-tested with a fake Graph.
"""

from __future__ import annotations

import io
from datetime import date, datetime
from pathlib import PurePosixPath

from openpyxl import load_workbook

from adlc_excel import ExpertWorkbook
from adlc_excel.regions import all_regions, find_region
from adlc_excel.values import matches, normalise_conditions
from adlc_pii import Policy, Vault
from adlc_pii.report import PiiReport
from adlc_pii.scrub import scrub_file, scrub_table

PII_TYPES = (".xlsx", ".docx", ".csv", ".txt", ".md")


class ServiceError(ValueError):
    pass


def _plain(v):
    if isinstance(v, datetime):
        return v.strftime("%d/%m/%Y") if v.time() == datetime.min.time() else v.strftime("%d/%m/%Y %H:%M")
    if isinstance(v, date):
        return v.strftime("%d/%m/%Y")
    return v


class WorkbookService:
    def __init__(self, graph, vaults, user_id: str, user_name: str = "", policy: Policy | None = None):
        self.graph = graph
        self.vaults = vaults
        self.user_id = user_id
        self.user_name = user_name or "SharePoint user"
        self.policy = policy or Policy()

    # ------------------------------------------------------------------ helpers

    def _open(self, file_url: str, kinds=(".xlsx",)):
        f = self.graph.resolve(file_url)
        ext = PurePosixPath(f.name).suffix.lower()
        if ext not in kinds:
            raise ServiceError(f"'{f.name}' is a {ext or 'file without an extension'}; I can work with {', '.join(kinds)} files here.")
        return f, self.graph.download(f)

    @staticmethod
    def _key(f) -> str:
        return f"{f.drive_id}:{f.item_id}"

    def _tokenised_regions(self, data: bytes, vault: Vault, report: PiiReport):
        """Values (cached results for formulas) of every table, tokenised, plus PII column types."""
        wb_vals = load_workbook(io.BytesIO(data), data_only=True)
        wb_form = load_workbook(io.BytesIO(data))
        out = {}
        for region in all_regions(wb_form):
            ws_v = wb_vals[region.ws.title]
            rows_idx = region.rows_with_data
            rows = [[_plain(ws_v.cell(r, c).value) for c in range(region.c0, region.c1 + 1)] for r in rows_idx]
            clean, types = scrub_table(region.headers, rows, self.policy, vault, report, where=region.ws.title)
            out[region.name] = (region, rows_idx, clean, types)
        return out

    # ------------------------------------------------------------------ workbook actions

    def inspect(self, file_url: str, sample_rows: int = 3) -> dict:
        f, data = self._open(file_url)
        vault = self.vaults.get(self.user_id, self._key(f))
        report = PiiReport(f.name)
        xw = ExpertWorkbook.from_bytes(data)
        info = xw.inspect(sample_rows=0)
        tables = self._tokenised_regions(data, vault, report)
        for sheet in info["sheets"]:
            for t in sheet["tables"]:
                hit = tables.get(t["name"])
                if not hit:
                    continue
                _, _, clean, types = hit
                for i, col in enumerate(t["columns"]):
                    col["sample"] = [row[i] for row in clean[:sample_rows] if i < len(row) and row[i] not in (None, "")]
                    if i in types:
                        col["personal_data"] = types[i]
        self.vaults.put(self.user_id, self._key(f), vault)
        return {
            "file": f.name, "link": f.web_url, "workbook": info,
            "privacy": report.text(cleaned=False) if report.risk != "none" else "No personal data seen in the samples.",
            "note": "Values that look like PERSON_001 or PPSN_002 are privacy tokens for real values. Use them exactly as shown; they are turned back into the real values when changes are saved.",
        }

    def query(self, file_url: str, sheet=None, table=None, columns=None, where=None, limit: int = 100, offset: int = 0) -> dict:
        f, data = self._open(file_url)
        vault = self.vaults.get(self.user_id, self._key(f))
        report = PiiReport(f.name)
        tables = self._tokenised_regions(data, vault, report)
        wb = load_workbook(io.BytesIO(data))
        region = find_region(wb, sheet, table, (normalise_conditions(where)[0]["column"] if where else None) or (columns or [None])[0])
        _, rows_idx, clean, _ = tables[region.name]
        headers = region.headers
        conds = vault.detokenise(normalise_conditions(where))
        wb_vals = load_workbook(io.BytesIO(data), data_only=True)[region.ws.title]
        picked = []
        for r, row in zip(rows_idx, clean):
            if all(matches(_plain(wb_vals.cell(r, region.col(c["column"])).value), c.get("op", "equals"), c.get("value")) for c in conds):
                picked.append(row)
        cols = [region.col(c) - region.c0 for c in columns] if columns else list(range(len(headers)))
        page = picked[offset:offset + min(limit, 500)]
        self.vaults.put(self.user_id, self._key(f), vault)
        return {
            "table": region.name, "columns": [headers[i] for i in cols], "total_matching_rows": len(picked),
            "rows": [[row[i] if i < len(row) else None for i in cols] for row in page],
            "truncated": len(picked) > offset + len(page),
        }

    def _apply(self, file_url: str, ops, summary=None, save=False) -> dict:
        f, data = self._open(file_url)
        vault = self.vaults.get(self.user_id, self._key(f))
        real_ops = vault.detokenise(ops)
        xw = ExpertWorkbook.from_bytes(data)
        result = xw.apply(real_ops, requested_by=self.user_name, tool="Laya Excel Expert (SharePoint)",
                          summary=vault.retokenise_text(summary) if summary else None)
        response = {
            "changes": [vault.retokenise_text(c) for c in result.changes],
            "warnings": [vault.retokenise_text(w) for w in result.warnings],
            "cells_changed": result.changed,
            "version": result.version,
            "saved": False,
        }
        if save:
            new = self.graph.upload(f, xw.to_bytes())
            response.update(saved=True, link=new.web_url or f.web_url,
                            note="Saved in SharePoint. Version history keeps the previous copy.")
        return response

    def preview(self, file_url: str, ops) -> dict:
        return self._apply(file_url, ops, save=False)

    def apply(self, file_url: str, ops, summary: str | None = None) -> dict:
        return self._apply(file_url, ops, summary, save=True)

    # ------------------------------------------------------------------ PII actions

    def _run_pii(self, f, data: bytes, profile: str, write: bool):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / f.name
            src.write_bytes(data)
            out = Path(tmp) / f"clean{src.suffix}"
            path, report, vault = scrub_file(src, out if write else None, Policy(profile=profile), write=write)
            return (out.read_bytes() if write else None), report, vault

    def pii_scan(self, file_url: str) -> dict:
        f, data = self._open(file_url, PII_TYPES)
        _, report, _ = self._run_pii(f, data, "restore", write=False)
        d = report.to_dict()
        for loc in d["locations"]:
            loc.pop("example", None)  # never send even masked values to the AI
        return {"file": f.name, "risk": d["risk"], "summary": report.text(cleaned=False).replace(report.source, f.name),
                "found": d["counts"], "where": [{k: l[k] for k in ("where", "type", "count")} for l in d["locations"]]}

    def pii_clean_copy(self, file_url: str, profile: str = "restore") -> dict:
        f, data = self._open(file_url, PII_TYPES)
        content, report, vault = self._run_pii(f, data, profile, write=True)
        stem, ext = PurePosixPath(f.name).stem, PurePosixPath(f.name).suffix
        new = self.graph.create_sibling(f, f"{stem} (PII removed){ext}", content)
        if profile == "restore":
            self.vaults.put(self.user_id, self._key(new), vault)
        return {"original": f.name, "clean_copy": new.name, "link": new.web_url, "risk": report.risk,
                "summary": report.text().replace(report.source, f.name),
                "restorable": profile == "restore",
                "note": "The clean copy is safe to use with any AI agent. Ask me to restore it when the work is done."}

    def pii_restore_copy(self, file_url: str) -> dict:
        f, data = self._open(file_url, PII_TYPES)
        vault = self.vaults.get(self.user_id, self._key(f))
        if not len(vault):
            raise ServiceError("I don't hold the key for this file. Restore works on a 'PII removed' copy that I created for you (it can have been edited since).")
        ext = PurePosixPath(f.name).suffix.lower()
        if ext == ".xlsx":
            from adlc_pii.scrub import restore_workbook

            wb = load_workbook(io.BytesIO(data))
            restore_workbook(wb, vault)
            buf = io.BytesIO()
            wb.save(buf)
            content = buf.getvalue()
        elif ext == ".docx":
            from docx import Document

            from adlc_pii.scrub import restore_docx

            doc = Document(io.BytesIO(data))
            restore_docx(doc, vault)
            buf = io.BytesIO()
            doc.save(buf)
            content = buf.getvalue()
        else:
            content = vault.restore_text(data.decode("utf-8-sig")).encode("utf-8")
        name = PurePosixPath(f.name).stem.replace(" (PII removed)", "") + f" (restored){ext}"
        new = self.graph.create_sibling(f, name, content)
        return {"restored_copy": new.name, "link": new.web_url,
                "note": "Real values are back in this copy. Check it before sharing - it contains personal data again."}
